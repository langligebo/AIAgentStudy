# 第 13 周 Session 02：端到端整合与故障修复

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

沿用户目标串联 Skill、检索、记忆、审批和工具，以一组故障定位集成边界。

## 前置知识与学习安排

综合项目需求、持久状态与幂等。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

整合按契约推进：先让正常路径闭环，再让每一段能返回明确失败或等待状态。共享 task_id 和 goal_revision，避免检索、记忆与审批关联到不同目标；写入使用稳定 action_id 并核验业务终态。

下方是单文件集成切片，用内存字典模拟 Skill 选择、证据、用户偏好、checkpoint 和工单；通过序列化往返模拟状态搬运。它不冒充 LangGraph、MCP、HTTP 或真实模型的集成，这些在你的项目实现后需逐项替换并独立验收。

故障先按边界分类：模型没提出动作、执行器拒绝、资料缺失、远端回包丢失、恢复后重复写入。每次只修明确原因并跑受影响案例，避免同时改模型、Prompt 和编排导致无法归因。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import json

ORDERS = {"A100": {"owner": "u1", "product": "keyboard"}}
POLICIES = {"keyboard": {"id": "p1-v1", "text": "七天内可申请退货"}}
MEMORY = {("u1", "language"): "中文"}
TICKETS, CHECKPOINTS = {}, {}

def handle(task_id, user, order_id, approval=False, fault=None):
    state = {"task_id": task_id, "status": "running", "skill": "aftersales-v1",
             "language": MEMORY.get((user, "language"), "中文"), "order_id": order_id}
    if not order_id:
        return {**state, "status": "waiting_user"}
    order = ORDERS.get(order_id)
    if not order or order["owner"] != user:
        return {**state, "status": "denied"}
    policy = None if fault == "no_policy" else POLICIES.get(order["product"])
    if not policy:
        return {**state, "status": "no_answer"}
    state["citation"] = policy["id"]
    state["status"] = "waiting_approval"
    CHECKPOINTS[task_id] = json.loads(json.dumps(state))
    if not approval:
        return state
    key = (user, task_id, "create-1")
    if key in TICKETS and TICKETS[key]["order_id"] != order_id:
        return {**state, "status": "idempotency_conflict"}
    TICKETS.setdefault(key, {"ticket_id": "T" + str(len(TICKETS)+1), "order_id": order_id})
    if fault == "response_lost":
        state["write_outcome"] = "unknown"
    # 恢复核验按稳定业务键，不信模型完成声明。
    observed = TICKETS.get(key)
    state["status"] = "success" if observed and observed["order_id"] == order_id else "unknown"
    state["ticket_id"] = observed["ticket_id"] if observed else None
    CHECKPOINTS[task_id] = json.loads(json.dumps(state))
    return state

assert handle("t1", "u1", "A100")["status"] == "waiting_approval"
normal = handle("t1", "u1", "A100", True, "response_lost")
assert normal["status"] == "success"
assert handle("t1", "u1", "A100", True)["ticket_id"] == normal["ticket_id"]
assert len(TICKETS) == 1
assert handle("t2", "u2", "A100", True)["status"] == "denied"
assert handle("t3", "u1", None)["status"] == "waiting_user"
assert handle("t4", "u1", "A100", True, "no_policy")["status"] == "no_answer"
assert len(TICKETS) == 1
assert CHECKPOINTS["t1"]["ticket_id"] == normal["ticket_id"]
print(normal, "工单数量", len(TICKETS))
print("PASS：模拟整合、等待审批、回包丢失、去重、权限、缺信息、无资料")
```

**预期现象：**正常流程引用 p1-v1 并核验唯一工单；缺信息、无资料、越权都不新增工单；状态往返只在内存，不证明进程重启恢复。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 依次把内存模块替换为已学实现：真实 Skill 加载、检索器、带来源记忆、LangGraph checkpoint、受控工具和 FastAPI；一次替换一个边界。
2. 审批由可信界面提供并绑定 action 参数与版本，替换本例教学布尔值；再执行修改参数与拒绝审批的负例。
3. 运行真实端到端开发集，再注入超时、响应丢失、进程重启、取消、跨用户与策略更新；对每项记录未验证或实际证据。

## 常见错误

- 内存切片通过就标记真实系统集成完成。
- 模型生成 approval=True 就执行写入。
- 恢复后的任务使用新 action_id 造成重复工单。

## 思考题

最小示例里所有断言通过，为什么综合项目还不能验收？

<details>
<summary>参考答案（先自行作答）</summary>

断言只覆盖替身模块和已展示场景。真实模型、协议、数据库并发、身份、进程恢复及服务边界还未验证，需在最终系统上运行冻结的验收集。

</details>

## 验收标准

- [ ] 能追踪一个任务跨模块的输入输出。
- [ ] 失败定位到具体边界且无额外副作用。
- [ ] 模拟切片、真实集成和用户验收分别记录。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [评估方法参考](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## 下一节衔接

下一节冻结版本，在独立保留集验收并准备他人可复现的交付。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
