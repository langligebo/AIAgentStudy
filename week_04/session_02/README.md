# 第 04 周 Session 02：任务状态、追问、更正与取消

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

把任务事实与聊天记录分开，建立有版本的任务状态，并阻止旧动作在用户更正后执行。

## 前置知识与学习安排

上一节循环和 Python dataclass。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

聊天记录保存“说过什么”，任务状态保存“现在要完成什么”。任务至少需要 task_id、目标、已知字段、状态、版本和完成证据。状态可为 running、waiting_user、success、failed、cancelled；等待输入不是失败。

缺订单号时进入 waiting_user。用户更正订单后版本增加，旧证据和审批失效。动作生成时携带任务版本，执行前再比较版本；否则模型慢响应可能把旧目标的操作执行到新任务上。

取消要在启动下一个动作前检查，也要传播给已经在运行的操作。这里演示单线程同步检查；远程写入已发出时取消无法撤销副作用，需核对结果，第 12 周再处理异步取消。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from dataclasses import dataclass, field

@dataclass
class Task:
    task_id: str
    order_id: str | None = None
    status: str = "waiting_user"
    revision: int = 0
    evidence: dict = field(default_factory=dict)

def update_order(task, order_id):
    if task.status in {"cancelled", "success", "failed"}:
        raise ValueError("终态任务不能直接修改")
    if not isinstance(order_id, str) or not order_id.strip():
        task.status = "waiting_user"
        return "请提供订单号"
    task.order_id = order_id
    task.revision += 1
    task.evidence.clear()
    task.status = "running"
    return "订单已更新，重新查询"

def execute_read(task, planned_revision):
    if task.status != "running":
        return "not_running"
    if planned_revision != task.revision:
        return "stale_action"
    task.evidence["order"] = {"order_id": task.order_id, "status": "delivered"}
    return "observed"

task = Task("task-1")
assert update_order(task, "") == "请提供订单号"
update_order(task, "A100")
old_revision = task.revision
assert execute_read(task, old_revision) == "observed"
update_order(task, "A101")
assert not task.evidence
assert execute_read(task, old_revision) == "stale_action"
assert execute_read(task, task.revision) == "observed"
task.status = "cancelled"
assert execute_read(task, task.revision) == "not_running"
other = Task("task-2")
assert other.evidence == {}
print(task)
print("PASS：缺信息、正常查询、更正失效、取消、任务隔离")
```

**预期现象：**缺订单号会追问；更新为 A101 后旧版本动作被拒绝；取消后不能继续读取，第二个任务没有继承证据。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 画出本例状态图，标出允许和禁止的转换。
2. 模拟先计划 A100、用户改 A101、旧模型调用才返回，验证旧动作无法提交。
3. 将任务证据中的订单号与当前订单号对比；思考恢复成功终态时为什么不能清空已发生的副作用记录。

## 常见错误

- 每轮从聊天全文猜任务当前状态。
- 订单更正后复用旧查询结果或审批。
- 取消只在 UI 显示，执行器继续调用工具。

## 思考题

用户取消时工单请求已经发出了，是否能显示“没有创建工单”？

<details>
<summary>参考答案（先自行作答）</summary>

不能。取消只表示不再继续目标，不证明已发出的写入没生效。应保存已发出动作并核对实际工单，结果不明则明确待确认。

</details>

## 验收标准

- [ ] 追问状态与失败状态不同。
- [ ] 更正使旧证据和待执行动作失效。
- [ ] 任务之间不共享可变默认字典，取消后无新动作。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Workflow 与 Agent 架构](https://www.anthropic.com/engineering/building-effective-agents)

## 下一节衔接

下一节用环境事实验证完成，并记录重复动作和退出原因。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
