# 第 04 周 Session 03：环境反馈、完成验证与退出

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

在工单创建后核验实际状态，识别假完成、无进展和不可解释的退出。

## 前置知识与学习安排

工具结果、任务状态和预算。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

模型生成“已经为您创建”是文本；创建工具返回 ID 是一次观察；再按 ID 查询并检查订单归属，才形成更强的完成证据。若查询失败，保留待核对，而不是凭语言确信成功。

无进展检测可比较动作名称、规范化参数和状态版本。同一个读取在状态未变时反复出现通常没有新信息；写入不能用简单去重就代替业务幂等。本例直接阻止重复提交，并在下一阶段学习持久幂等。

轨迹只记录可见请求、工具结果、状态和停止原因，不需要模型内部思考。可从轨迹重建发生的事实。退出原因至少区分 success、verification_failed、no_progress、budget；它们影响后续是交付、追问还是人工接管。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import json

def run(actions, lose_response=False, phantom=False):
    tickets, trace, seen = {}, [], set()
    for step, (name, args) in enumerate(actions, 1):
        signature = (name, json.dumps(args, sort_keys=True))
        if signature in seen:
            return "no_progress", tickets, trace
        seen.add(signature)
        if step > 4:
            return "budget", tickets, trace
        if name == "create":
            if not phantom:
                tickets["T1"] = {"order_id": args["order_id"], "status": "open"}
            result = {"status": "unknown"} if lose_response else {"ticket_id": "T1"}
        elif name == "verify":
            result = tickets.get("T1")
            trace.append({"step": step, "action": name, "result": result})
            valid = result is not None and result["order_id"] == args["order_id"]
            return ("success" if valid else "verification_failed"), tickets, trace
        else:
            return "unknown_action", tickets, trace
        trace.append({"step": step, "action": name, "arguments": args, "result": result})
    return "needs_verification", tickets, trace

actions = [("create", {"order_id": "A100"}), ("verify", {"order_id": "A100"})]
assert run(actions)[0] == "success"
assert run(actions, lose_response=True)[0] == "success"
assert run(actions, phantom=True)[0] == "verification_failed"
assert run([actions[0], actions[0]])[0] == "no_progress"
assert run([actions[0]])[0] == "needs_verification"
for options in ({}, {"lose_response": True}, {"phantom": True}):
    status, tickets, trace = run(actions, **options)
    print(status, json.dumps(trace, ensure_ascii=False))
print("PASS：真实存在、回包丢失、虚假成功、重复动作、缺验证")
```

**预期现象：**回包丢失但核验查到工单仍可成功；phantom 模式没有工单，即使返回 T1 也验收失败。T1 是固定模拟 ID，真实系统要用稳定业务键核对。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 把 verify 的订单号改成其他订单，保证不能通过验收。
2. 统计 trace 中实际发生的创建次数，分别和模型宣称次数比较。
3. 整理本周最小 CLI 设计：输入、更正、取消、观察、退出；实现时复用前两节的契约，不把三个演示直接拼成生产服务。

## 常见错误

- 用“模型回答包含成功”作为验收条件。
- 工具返回 ID 后不检查与当前任务的关联。
- 无限自我检查，用更多文字替代环境事实。

## 思考题

核验失败时直接再创建一张是否合理？

<details>
<summary>参考答案（先自行作答）</summary>

先区分查询本身失败和确定不存在。网络失败无法证明不存在；即使确定不存在也要核对授权、幂等键与预算。修复必须有证据和边界。

</details>

## 验收标准

- [ ] 能从轨迹重建动作及退出理由。
- [ ] 回包丢失不触发重复创建。
- [ ] 虚假成功和没有核验都不能进入成功终态。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

预算约束循环，任务状态表达目标和更正，环境反馈支撑终态。用户取消和模型说完成都需要程序核对。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 手写决策、执行、观察、再次决策的循环，并用步数和工具预算限制运行。 |
| [Session 02](../session_02/README.md) | 把任务事实与聊天记录分开，建立有版本的任务状态，并阻止旧动作在用户更正后执行。 |
| [Session 03](../session_03/README.md) | 在工单创建后核验实际状态，识别假完成、无进展和不可解释的退出。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Workflow 与 Agent 架构](https://www.anthropic.com/engineering/building-effective-agents)

## 下一节衔接

本节完成本模块前三节的阶段复盘，接着学习新增的[Session 04](../session_04/README.md)；原下一模块安排顺延，历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
