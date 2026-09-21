# Session 02：JSON Schema、Pydantic 与业务校验

[第二周入口](../README.md) · [完整学习计划](../../LEARNING_PLAN.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md)

## 1. 本节目标与前置知识

上一节学习了如何通过消息角色、结构化输出参数和流式协议获得模型回答。本节进一步把回答变成可检查的数据，继续使用第一周的“客服消息分类”任务。

学完后应能：

- 区分 JSON 语法错误、字段契约错误和任务判断错误。
- 用 Pydantic 定义必填字段、允许值、严格类型和字段之间的关系。
- 解释“允许 null”和“字段可以省略”的差别。
- 从 Pydantic 模型生成 JSON Schema，理解服务端约束与本地校验各自的作用。
- 对信息不足、错误分类、截断回答做出不同处理。

前置知识：Python 类和异常处理、`json.loads()`、`client.chat(messages)`，以及第一周约定的“投诉优先”规则。预计学习 60～90 分钟，可分两次完成。

当前状态：教案与示例已准备，核心样例已做离线验证。本节尚未提供独立 `main.py`，也未执行远程模型实验；用户掌握情况仍待练习确认。

## 2. 三层校验分别解决什么问题

客户说：“帮我处理一下。”信息不足，预期为 `{"category":null,"needs_clarification":true}`。

| 模型输出 | JSON 语法 | 字段契约 | 任务判断 |
| --- | --- | --- | --- |
| `这是咨询。` | 不通过 | 未执行 | 未执行 |
| `{"category":"咨询","needs_clarification":"false"}` | 通过 | 不通过：字符串不是布尔值 | 未执行 |
| `{"category":null,"needs_clarification":false}` | 通过 | 不通过：两个字段互相矛盾 | 未执行 |
| `{"category":"咨询","needs_clarification":false}` | 通过 | 通过 | 不通过：应澄清 |
| `{"category":null,"needs_clarification":true}` | 通过 | 通过 | 通过当前样例 |

```text
完整响应及结束原因
        ↓
JSON 语法能否解析？
        ↓
字段、类型、取值及字段关系是否符合契约？
        ↓
与原始任务及预期答案是否一致？
```

“契约”是程序规定的接收格式和一致性条件；“任务判断”是结合客户消息，确认是否分对类。Pydantic 本身不会理解客户原话，也不会自动知道正确标签。

本节教学规则沿用第一周：明确不满或要求追责归为投诉，混合意图时投诉优先；已有购买并申请退换维修、未明确不满归为售后；其余明确的信息询问归为咨询；无法判断时返回空类别并追问。

## 3. 用 Pydantic 定义数据契约

示例使用 Pydantic 2.x。当前项目环境已具备 Pydantic；可在项目根目录运行 `uv run python`，将本节第 3、4、5 节代码按顺序放进同一个 Python 会话。前五节不调用模型。

```python
from typing import Literal, Self
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator


class Intent(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    category: Literal["咨询", "投诉", "售后"] | None
    needs_clarification: bool

    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        if (self.category is None) != self.needs_clarification:
            raise ValueError("空类别必须与需要澄清对应")
        return self
```

| 定义 | 本例含义 |
| --- | --- |
| `Literal["咨询", "投诉", "售后"]` | 只允许这三个字符串值 |
| `| None` | 允许明确传入空值；JSON 中写成 `null` |
| 字段没有默认值 | 字段必须出现，即使它允许空值 |
| `strict=True` | 本例拒绝 `"false"`、`0` 等非布尔值，不通过类型转换掩盖输出错误 |
| `extra="forbid"` | 拒绝额外字段，例如模型擅自增加的 `explanation` |
| `model_validator(mode="after")` | 字段验证完成后，再检查字段之间的关系 |

`category: ... | None` 与 `category: ... | None = None` 不同：后者有默认值，字段可省略。这里选择前者，让模型明确表达“缺信息”，避免把漏字段悄悄当成有意的空值。

一致性表达式中的 `!=` 表示两个布尔结果不相同就拒绝。因此本例只允许“空类别、需要澄清”或“明确类别、不需澄清”。这是教学约定；真实业务如果允许已经识别售后意图但仍缺订单号，应另外设计“缺少业务参数”，不要直接沿用本例二者等价的规则。

参阅 [Pydantic 严格模式](https://docs.pydantic.dev/latest/concepts/strict_mode/)、[模型校验器](https://docs.pydantic.dev/latest/concepts/validators/#model-validators)。

## 4. 实验一：故意提供错误回答

在定义 `Intent` 的同一个 Python 会话继续运行：

```python
import json


def reject_non_json_constant(value: str) -> None:
    # Python 默认容忍 NaN / Infinity；本例按标准 JSON 拒绝它们。
    raise ValueError(f"{value} 不是标准 JSON 值")


def evaluate(raw: str, expected: dict, finish_reason: str = "stop") -> str:
    if finish_reason != "stop":
        return f"响应结束原因待处理：{finish_reason}；不判定成功"

    try:
        data = json.loads(raw, parse_constant=reject_non_json_constant)
    except (ValueError, RecursionError) as exc:
        return f"JSON 解析失败：{exc}"

    try:
        intent = Intent.model_validate(data)
    except ValidationError as exc:
        error = exc.errors()[0]
        return f"契约校验失败：位置={error['loc']}，类型={error['type']}"

    if intent.model_dump() != expected:
        return "契约通过，但分类或澄清判断错误"
    return "通过当前样例"


expected = {"category": None, "needs_clarification": True}
samples = [
    "这是咨询。",
    '{"category":"咨询","needs_clarification":"false"}',
    '{"category":null,"needs_clarification":false}',
    '{"category":"咨询","needs_clarification":false}',
    '{"category":null,"needs_clarification":true}',
    '{"needs_clarification":true}',
    '{"category":null,"needs_clarification":true,"explanation":"信息不足"}',
]
for raw in samples:
    print(raw)
    print(evaluate(raw, expected))
```

预期依次观察到：JSON 错误、布尔类型错误、一致性错误、任务判断错误、成功、缺少必填字段、额外字段错误。不要为了让结果通过而剥离 Markdown 围栏、补字段或自动修复模型回答。

这里的 `expected` 是为教学样例预先标注的答案，只用于评分，不传给待评估模型。实际线上请求通常没有预先标注的答案，需要其他业务证据或人工检查；不能把这个比较函数当作通用语义判断器。

## 5. JSON Schema 与本地校验的配合

```python
schema = Intent.model_json_schema()
print(json.dumps(schema, ensure_ascii=False, indent=2))
```

观察生成结果中的四处：

- `properties` 描述字段和类型。
- `enum` 限制类别取值；`anyOf` 允许字符串枚举或 `null`。
- `required` 同时包含 `category` 与 `needs_clarification`。
- `additionalProperties: false` 禁止额外字段。

JSON Schema 是描述数据约束的标准格式；Pydantic 是本节在 Python 中定义和执行校验的工具。[JSON Schema 对象约束](https://json-schema.org/understanding-json-schema/reference/object)、[Pydantic Schema 生成](https://docs.pydantic.dev/latest/concepts/json_schema/)

生成出的 Schema **不包含**上面 `check_consistency()` 中任意 Python 逻辑的自动翻译。JSON Schema 标准本身可以表达一些条件关系，但本例没有手写这些条件；因此把 Schema 交给服务后，仍须本地执行一致性校验。

## 6. 实验二：接入共享模型客户端

这一步会发起 **一次真实模型请求**。先完成离线实验，再在项目根目录、已经定义好 `Intent` 和 `evaluate` 的同一个 Python 会话中执行。连接配置仍来自根目录 `config.toml`。

```python
from common.llm import create_llm_client
from week_01.session_03.prompts import ROLE, TASK, RULES, OUTPUT

client = create_llm_client()
message = "这次送错颜色让我很不满，我要求换货。"
messages = [
    {"role": "system", "content": "\n".join((ROLE, TASK, *RULES, OUTPUT))},
    {"role": "user", "content": message},
]
response = client.chat(
    messages,
    response_schema=Intent.model_json_schema(),
    temperature=0.0,
    seed=42,
    max_tokens=256,
)
print("原始回答：", response.text)
print("结束原因：", response.finish_reason)
print(evaluate(
    response.text,
    {"category": "投诉", "needs_clarification": False},
    response.finish_reason,
))
```

参数发送和响应解析复用 `common.llm`；本节只新增输出契约和验收步骤。当前示例仅接受已知正常结束的 `stop`；`length` 或未知原因不能作为成功。这里简化了失败分类，第 02 周 Session 03 再系统处理网络失败、空回答、截断和可靠性。

扩展练习：用第一周已有的咨询、售后、投诉、信息不足样例各做一次独立调用。打印原始回答和失败层次，不自动重试、不生成结果文件。通过几条样例只说明这些样例通过，不能据此声称分类器已经可靠。

## 7. 常见错误与练习

常见错误：

- 把“合法 JSON”当成“业务正确”，跳过语义验收。
- 把 `null`、省略字段、空字符串混为一谈。
- 忘记严格模式，自动转换类型后看不到模型原始错误。
- 认为服务端接受了 Schema，就无需检查返回值。
- 认为 Pydantic 自定义校验器都会进入生成的 Schema。
- 对截断回答补括号后判定成功，或者用模型自己说“正确”代替独立证据。

练习：

1. 对“送错颜色让我很不满，我要求换货”，返回 `{"category":"售后","needs_clarification":false}`。分别说明三层检查的结果。
2. 删除 `category` 字段，与显式传 `"category": null` 比较；再临时加入 `= None` 默认值，观察区别。
3. 将 `needs_clarification` 分别设成 `"false"`、`0`、`false`，预测并验证严格模式下的行为。
4. 给原本正确的 JSON 添加 `explanation`，查看错误位置与类型。
5. 对完整且正确的样例传入 `finish_reason="length"`，解释为什么仍不能判定任务成功。
6. 将分类器扩展为能识别“意图明确但缺订单号”，先讨论字段设计，再写代码；不要把所有缺信息都塞进空类别。

## 8. 验收与下一节

- [ ] 能独立解释三层校验，并为每层给出一个失败样例。
- [ ] 能说明必填、可空、默认值、枚举、严格类型和额外字段约束。
- [ ] 能解释模型校验器何时运行，以及为什么合法字段仍可能相互矛盾。
- [ ] 能查看生成的 JSON Schema，指出哪些规则只在本地执行。
- [ ] 能用离线样例验证错误分类，并区分离线验证与真实模型效果。
- [ ] 能通过共享客户端做一次真实结构化分类，检查原始回答和结束原因。

上述项目需依据实际实践与用户反馈确认，不因教案生成而自动勾选。下一节是 [第 02 周 Session 03：调用失败处理、能力基线与测试样本划分](../session_03/README.md)。

## 练习参考答案与环境核对

核对日期：2026-09-21。当前环境 Pydantic 2.13.5、Python 3.12.0；正文第 3、4、5 节须依序放在同一进程，离线验证不包含第 6 节真实模型。独立实验脚本仍未创建，原待办保留。

<details>
<summary>六项练习的参考答案</summary>

1. 混合消息明确不满，按本课规则是投诉；售后对象通过 JSON 和契约，但任务错误。
2. 允许 None 不等于允许省略；加入默认 None 后缺字段可能取默认值，改变了契约。
3. 严格模式只接受真正的布尔 false，字符串和数字均拒绝。
4. extra=forbid 应产生额外字段错误，不能忽略 explanation。
5. length 表示输出预算触顶，未确认完整结束；本课程保守处理为截断失败。
6. 可以增加 missing_fields 或单独订单字段，以表达“意图明确但缺参数”；不能把缺订单号与意图未知混成一个 category=null。

</details>

## 课程导航

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
