# 第 08 周 Session 03：重放、副作用与结果未知

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

在返回丢失后核对真实业务状态，用持久幂等避免恢复导致重复工单。

## 前置知识与学习安排

Checkpoint、审批、输入契约、SQLite 唯一约束。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

状态恢复保证能继续编排，不自动保证外部副作用只发生一次。创建工单成功到保存 checkpoint 之间存在故障窗口。应由业务服务接受稳定幂等键，记录请求参数和结果；同键同参返回原结果，同键不同参拒绝。

结果至少区分 succeeded、failed 和 unknown。超时或连接断开常意味着不知道，而不是失败；核对时要使用原业务键和身份。只有服务明确保证未执行或查明状态，才决定是否再次提交。

下面用 SQLite 唯一键保存工单和请求内容，模拟提交事务后响应丢失。再次查询同键得到工单，重试同参不新增，不同参冲突。它只证明单机同库原子写与去重；真实跨服务事务、并发提交与长期键保留需额外验证。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as tmp:
    db = Path(tmp) / "tickets.db"
    def connect():
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE IF NOT EXISTS tickets (key TEXT PRIMARY KEY, payload TEXT, ticket_id TEXT UNIQUE)")
        return conn
    def create(key, action, lose_response=False):
        payload = json.dumps(action, sort_keys=True)
        conn = connect()
        try:
            with conn:
                conn.execute("INSERT OR IGNORE INTO tickets VALUES (?,?,?)", (key, payload, "T-" + key))
                old, tid = conn.execute("SELECT payload,ticket_id FROM tickets WHERE key=?", (key,)).fetchone()
                if old != payload:
                    raise ValueError("idempotency_conflict")
            if lose_response:
                raise TimeoutError("提交已完成，但响应丢失")
            return tid
        finally:
            conn.close()
    action = {"owner": "u1", "order_id": "A100", "reason": "损坏"}
    try:
        create("u1-task1-action1", action, lose_response=True)
    except TimeoutError:
        outcome = "unknown"
    assert outcome == "unknown"
    conn = connect()
    row = conn.execute("SELECT ticket_id FROM tickets WHERE key=?", ("u1-task1-action1",)).fetchone()
    assert row is not None
    outcome = "succeeded"
    assert create("u1-task1-action1", action) == row[0]
    try:
        create("u1-task1-action1", {**action, "order_id": "A101"})
    except ValueError as exc:
        assert str(exc) == "idempotency_conflict"
    else:
        raise AssertionError("同键异参不应成功")
    assert conn.execute("SELECT count(*) FROM tickets").fetchone()[0] == 1
    conn.close()
    print(outcome, row[0], "工单数量=1")
print("PASS：提交后断线、核对、同参去重、异参冲突")
```

**预期现象：**超时先标 unknown；核对后转 succeeded；同键重试仍只有一张，异参拒绝。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 把丢失响应移到提交前，比较数据库是否存在记录。
2. 恢复图时从 task_id 和 action_id 派生稳定幂等键，不能每次恢复随机换键。
3. 模拟核对服务也失败，确认任务保留 unknown，不宣称失败或盲目重发。

## 常见错误

- 把 checkpoint 当外部业务事务。
- 每次重试生成新幂等键。
- 相同键不检查参数，旧审批被用于新订单。

## 思考题

为什么仅在内存 set 中保存“已执行动作”不够？

<details>
<summary>参考答案（先自行作答）</summary>

进程重启后集合丢失，而且并发检查和写入不一定原子。幂等记录应与业务结果持久保存，并通过唯一约束或等价机制处理竞争。

</details>

## 验收标准

- [ ] 丢失响应先标未知并核对。
- [ ] 恢复后只有一张模拟工单。
- [ ] 同键异参拒绝，未知结果不能当确定失败。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

图负责编排，checkpoint 负责保存执行位置，业务幂等负责避免重复副作用；三种保证不能混淆。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 将已理解的循环映射到图状态、节点更新和条件边，并用相同输入比较行为。 |
| [Session 02](../session_02/README.md) | 在具体写入动作前保存状态，理解重启恢复、批准、修改与拒绝的差别。 |
| [Session 03](../session_03/README.md) | 在返回丢失后核对真实业务状态，用持久幂等避免恢复导致重复工单。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 框架部分固定 langgraph 1.0.1、langgraph-checkpoint-sqlite 3.0.0；仅核对 API/版本与语法，未安装或运行。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [1.0.1 的 interrupt 与 Command 源码](https://github.com/langchain-ai/langgraph/blob/1.0.1/libs/langgraph/langgraph/types.py)
- [langgraph 1.0.1](https://pypi.org/project/langgraph/1.0.1/)
- [SQLite checkpointer 3.0.0](https://pypi.org/project/langgraph-checkpoint-sqlite/3.0.0/)

## 下一节衔接

本节完成本模块前三节的阶段复盘，接着学习新增的[Session 04](../session_04/README.md)；原下一模块安排顺延，历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
