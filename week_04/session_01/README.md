# 第 04 周 Session 01：最小 Agent 执行循环

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_03/session_04/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

手写决策、执行、观察、再次决策的循环，并用步数和工具预算限制运行。

## 前置知识与学习安排

第 3 周的工具协议与执行器。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

循环由代码驱动，下一步动作可以由模型提出，这两点同时成立。固定“生成回答→检查回答”仍可能是 Workflow；只有决策会根据目标和反馈选择路径时，才在本课程中称为 Agent。

每轮先检查取消和预算，再调用决策器，再校验动作；工具观察进入下一轮上下文。模型结束回答只是候选终点，业务成功还需要证据。最大模型步数和最大工具次数是两项预算，一轮可能提出多个工具请求。

为了验证运行时，本例用确定性函数替代模型决策：它看到订单后再选政策工具。故意不进展的决策器用于测试预算。它验证循环的控制行为，不证明模型自主规划能力。接入模型时使用 `common.llm.create_llm_client().chat`，延续第 3 周消息协议，保留这里的所有预算检查。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
ORDERS = {"A100": {"product": "keyboard"}}
POLICY = {"keyboard": "7 天内可申请退货"}

def decide(observations):
    if "order" not in observations:
        return ("get_order", "A100")
    if "policy" not in observations:
        return ("get_policy", observations["order"]["product"])
    return ("finish", None)

def run(decider, max_steps=4, tool_budget=2):
    observations, trace = {}, []
    calls = 0
    for step in range(1, max_steps + 1):
        name, value = decider(observations)
        trace.append({"step": step, "action": name, "argument": value})
        if name == "finish":
            status = "success" if {"order", "policy"} <= observations.keys() else "unverified"
            return status, calls, trace
        if calls >= tool_budget:
            return "tool_budget", calls, trace
        if name not in {"get_order", "get_policy"}:
            return "unknown_tool", calls, trace
        calls += 1
        if name == "get_order":
            if value not in ORDERS:
                return "not_found", calls, trace
            observations["order"] = ORDERS[value]
        else:
            if value not in POLICY:
                return "no_policy", calls, trace
            observations["policy"] = POLICY[value]
        trace[-1]["observed"] = dict(observations)
    return "step_budget", calls, trace

normal = run(decide)
repeat = run(lambda obs: ("get_order", "A100"))
false_finish = run(lambda obs: ("finish", None))
assert normal[:2] == ("success", 2)
assert repeat[0] == "tool_budget"
assert false_finish[0] == "unverified"
assert run(decide, max_steps=1)[0] == "step_budget"
for result in (normal, repeat, false_finish):
    print(result)
print("PASS：正常多步、重复请求、假完成和步数耗尽")
```

**预期现象：**正常路径为 get_order → get_policy → finish；重复读取在工具预算处停止，提前 finish 返回 unverified。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 跟随 trace 逐轮指出观察如何影响下一步。
2. 把 max_steps 设为 1，tool_budget 设为 1，分别观察停止原因。
3. 用第 3 周真实工具请求替换 decider 时，记录模型调用次数，逐项回传观察；未知工具仍交执行器拒绝。

## 常见错误

- 因为出现 while 就称为自主 Agent。
- 只限制模型轮数，忽略一轮的多个工具调用。
- 只靠 system prompt 要求停止，没有代码预算。

## 思考题

模型为什么不能自行决定扩大工具预算？

<details>
<summary>参考答案（先自行作答）</summary>

预算是运行时约束。模型可以建议继续，但只有可信配置或用户授权能改变约束；否则失败循环会自行解除限制。

</details>

## 验收标准

- [ ] 能手动解释三轮观察和决策。
- [ ] 预算耗尽有明确状态，未伪装成功。
- [ ] 模拟决策与真实模型实验的证据分开。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Workflow 与 Agent 架构](https://www.anthropic.com/engineering/building-effective-agents)

## 下一节衔接

下一节让循环处理等待用户、更正和取消，而不只是一次运行到结束。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_03/session_04/README.md) · [下一节](../session_02/README.md)
