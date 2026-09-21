# 第 04 模块 Session 04：把真实模型接入手写循环

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

在同一个循环里替换决策器，保留工具权限、预算、观察和完成依据。

## 前置知识与学习安排

第四模块前三节与第三模块调用协议。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

前三节测试循环机制，但固定决策函数不构成真实模型 Agent。本节显式定义 decide(messages) 边界：返回文本、调用列表与结束原因；执行器维护可信用户、工具白名单与预算；两者不能相互替代。

运行时按请求→决策→动作校验→执行→观察构造下一轮消息。模型可选择查政策或订单，也可以直接回答；有回答不等于完成，必须检查必需证据。下例只处理只读模拟订单；创建工单继续使用第三模块的审批执行器，不能直接把只读示例扩成任意写入。

真实适配使用公共 chat；每轮保留 assistant 工具调用及 tool 观察。有限轮数限制总模型调用，单独的工具预算覆盖多调用。未知工具、无权限、截断都形成明确结果。文本准确性仍需与证据比对，本例最后的 answer_ready 只表示证据齐备、待检验回答。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
import json

TOOLS = [{"type": "function", "function": {"name": "get_order", "description": "查询当前用户的模拟订单", "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"], "additionalProperties": False}}}]

def run(decide, owner="u1", max_steps=3, tool_budget=2):
    messages = [{"role": "user", "content": "查询 A100 的发货状态。"}]
    evidence, trace = {}, []
    for step in range(max_steps):
        r = decide(messages)
        if r["finish"] != "stop": return "incomplete", trace
        calls = r["calls"]
        if not calls: return ("answer_ready" if evidence else "unverified"), trace
        messages.append({"role": "assistant", "content": r["text"], "tool_calls": [
            {"function": {"name": c["name"], "arguments": c["args"]}} for c in calls]})
        for c in calls:
            if tool_budget <= 0: return "budget", trace
            tool_budget -= 1
            if c["name"] != "get_order" or c["args"] != {"order_id": "A100"}:
                result = {"error": "invalid_call"}
            elif owner != "u1": result = {"error": "not_found_or_forbidden"}
            else:
                result = {"order_id": "A100", "status": "shipped", "source": "mock_orders"}
                evidence["A100"] = result
            trace.append(result)
            messages.append({"role": "tool", "tool_name": c["name"], "content": json.dumps(result)})
    return "step_limit", trace

def fake(messages):
    if messages[-1]["role"] == "tool":
        return {"text": "请核对工具状态", "finish": "stop", "calls": []}
    return {"text": "", "finish": "stop", "calls": [{"name": "get_order", "args": {"order_id": "A100"}}]}

assert run(fake)[0] == "answer_ready"
assert run(fake, owner="u2")[0] == "unverified"
assert run(fake, tool_budget=0)[0] == "budget"
assert run(lambda _: {"text": "已发货", "finish": "stop", "calls": []})[0] == "unverified"
print("PASS：相同循环的正常、越权、预算、无证据结束")
```

**预期现象：**正常路径得到可核对的订单观察；越权、预算不足和直接自称完成不会成功。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。

## 真实模型扩展：本次未运行

先在同一进程运行上方完整块，再运行下方块。使用项目根目录环境，无新增依赖；复用公共客户端与配置。最多 3 次请求，不自动重试。返回后的回答仍需人工核对，原始实验只打印。

<!-- verify: live; depends: offline -->
```python
from common.llm import create_llm_client
client = create_llm_client()
def real_decide(messages):
    r = client.chat(messages, tools=TOOLS, temperature=0.0, max_tokens=512)
    print("模型回答：", r.text, "调用：", r.tool_calls)
    return {"text": r.text, "finish": r.finish_reason,
            "calls": [{"name": c.name, "args": c.arguments} for c in r.tool_calls]}
print(run(real_decide))
```

## 实验步骤与练习

1. 离线逐步查看 messages/trace，解释 finish 与业务终态不同。
2. 执行下方真实扩展，观察模型实际是否选择工具，不预设必须成功。
3. 加入重复读取、错误工具和多调用输入，确认预算不被绕过。
4. 在第八模块迁移图时以本节相同输入、身份与工具作为对照。

## 常见错误

- 只更换函数名就声称完成真实模型集成。
- 丢弃工具错误，给下一轮伪造正常观察。
- 把 answer_ready 当回答已验收。

## 思考题

为什么真实模型选择不用工具时本例不通过？

<details>
<summary>参考答案（先自行作答）</summary>

本任务要求查询当前订单，模型参数中的知识不是业务状态来源；没有订单观察便不能验证其回答。

</details>

## 验收标准

- [ ] 能替换 decide 而不改变执行边界。
- [ ] 真实实验有模型动作与工具观察，不只有最终回答。
- [ ] 正常与失败轨迹均能重建并说明停止原因。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Ollama Tool calling](https://docs.ollama.com/capabilities/tool-calling)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../../week_05/session_01/README.md)
