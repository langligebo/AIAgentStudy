# 第 03 周 Session 01：工具调用协议

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_02/session_06/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

能把工具声明、模型提出的调用和程序返回的观察关联起来，处理一轮中的多个调用。

## 前置知识与学习安排

第二周的消息角色、JSON 对象和失败分类；理解 Python 字典和函数。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

工具声明是给模型看的接口说明；模型返回的名称和参数只是请求，Python 才执行函数。返回之后还要把 assistant 的调用记录和 tool 的结果一起交回模型，否则下一轮没有证据。

本课用 `get_order` 查询订单，用 `get_policy` 查询政策。名称要表达对象，描述要说明何时使用，参数 Schema 要写清必填、类型和额外字段。Schema 帮助生成；执行器仍须重新校验输入。

一次回答可能包含多个调用。给每个调用保留本轮序号，分别回传成功或失败。当前公共客户端只保留名称和参数，没有通用 `tool_call_id`；Ollama 消息使用 `tool_name` 并保持调用顺序。将来接其他服务时要由适配层保留其 ID，不能把本课的序号当成跨服务协议 ID。相同工具的多次调用在此串行处理。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import json

ORDERS = {"A100": {"status": "delivered", "product": "keyboard"}}
POLICIES = {"keyboard": "签收 7 天内可申请退货，须核验订单。"}
TOOLS = [{"type": "function", "function": {
    "name": name, "description": desc,
    "parameters": {"type": "object", "properties": {key: {"type": "string"}},
                   "required": [key], "additionalProperties": False},
}} for name, desc, key in [
    ("get_order", "查询模拟订单状态，必须有订单号", "order_id"),
    ("get_policy", "查询产品售后政策，不查询订单", "product"),
]]

def execute(name, args):
    spec = {"get_order": ("order_id", ORDERS), "get_policy": ("product", POLICIES)}
    if name not in spec:
        return {"ok": False, "error": "unknown_tool"}
    key, data = spec[name]
    if not isinstance(args, dict) or set(args) != {key} or type(args[key]) is not str:
        return {"ok": False, "error": "invalid_arguments"}
    if args[key] not in data:
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "data": data[args[key]]}

calls = [{"function": {"name": name, "arguments": args}} for name, args in [
    ("get_order", {"order_id": "A100"}),
    ("get_policy", {"product": "keyboard"}),
    ("get_order", {"order_id": "missing"}),
]]
messages = [{"role": "user", "content": "查 A100 和键盘政策"},
            {"role": "assistant", "content": "", "tool_calls": calls}]
for index, call in enumerate(calls):
    f = call["function"]
    result = execute(f["name"], f["arguments"])
    messages.append({"role": "tool", "tool_name": f["name"],
                     "content": json.dumps(result, ensure_ascii=False)})
    print(index, f["name"], result)
assert len(messages) == 5
assert json.loads(messages[-1]["content"])["error"] == "not_found"
assert execute("exec", {})["error"] == "unknown_tool"
assert execute("get_order", {"order_id": 100})["error"] == "invalid_arguments"
print("PASS：两个正常查询、无结果、未知工具和错误参数")
```

**预期现象：**前两个调用返回数据，第三个返回 not_found；最终输出 PASS。没有实际模型参与，calls 是固定测试夹具。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

### 接入真实模型（本次未执行）

先运行本节完整离线块，保留其 `TOOLS` 和 `execute` 定义，再在同一个 Python 进程执行下面代码。使用项目根目录启动的环境；不要把两段分到互不共享变量的终端。本例最多两次模型调用，只展示一轮工具协议，持续循环到第 4 周再做。

```python
# course: live; depends: offline
from common.llm import create_llm_client
import json

client = create_llm_client()
messages = [{"role": "user", "content": "查询订单 A100，并查询 keyboard 的售后政策。"}]
response = client.chat(messages, tools=TOOLS, temperature=0.0)
if response.finish_reason != "stop":
    raise RuntimeError(f"未完成响应：{response.finish_reason}")
messages.append({"role": "assistant", "content": response.text,
                 "tool_calls": [{"function": {"name": c.name, "arguments": c.arguments}}
                                for c in response.tool_calls]})
for call in response.tool_calls:
    result = execute(call.name, call.arguments)
    messages.append({"role": "tool", "tool_name": call.name,
                     "content": json.dumps(result, ensure_ascii=False)})
if not response.tool_calls:
    print("本轮没有工具调用，不能据此确认工具能力。", response.text)
else:
    final = client.chat(messages, temperature=0.0)
    if final.finish_reason != "stop" or final.tool_calls:
        raise RuntimeError("最终回答尚未完成")
    print(final.text)
```

本例查询的是不含个人资料的公共模拟订单；真实用户数据的访问必须采用下一节执行器。真实文本是否忠于工具结果需人工对照，不能用离线 PASS 替代。
## 实验步骤与练习

1. 运行示例，逐项对照 TOOLS、calls 与 messages，指出每一项是谁产生的。
2. 把两个调用改成同一工具查询两个订单，确认返回顺序和结果都保留；不能只处理 tool_calls[0]。
3. 做真实实验时，先按下方代码接入公共客户端；观察是否确实提出工具请求，未请求工具也应记录为未完成。

## 常见错误

- 直接执行模型给出的任意函数名；只允许注册表中的名称。
- 只把工具结果拼进 user 消息，丢失 assistant 调用记录。
- 收到 tool_calls 就宣称订单查询成功；应等执行结果。

## 思考题

工具请求中的参数是合法 JSON，为什么还不能立刻执行？

<details>
<summary>参考答案（先自行作答）</summary>

JSON 只保证可解析。还需检查工具是否注册、字段类型和取值、当前身份、业务状态及写入授权；本节只演示前两类，第 2 节补齐业务和权限。

</details>

## 验收标准

- [ ] 能说明请求、执行、观察三者的边界。
- [ ] 多个调用逐项回传，无结果不伪装成成功。
- [ ] 能指出当前 Ollama 适配与需要调用 ID 的服务的差异。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 模型接入复用项目 common.llm；环境有 ollama 0.6.2，但公共客户端当前通过标准库 HTTP 实现，服务端版本和真实工具能力仍需实测。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Ollama 工具调用](https://docs.ollama.com/capabilities/tool-calling)

## 下一节衔接

下一节给相同调用加上可信身份、输入输出契约和写入限制。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_02/session_06/README.md) · [下一节](../session_02/README.md)
