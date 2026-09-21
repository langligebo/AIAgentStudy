# 第 08 周 Session 02：Checkpoint、人工审批与恢复

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

在具体写入动作前保存状态，理解重启恢复、批准、修改与拒绝的差别。

## 前置知识与学习安排

图状态；第 3 周审批绑定参数，第 7 周持久存储。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

Checkpoint 保存一次执行的中间状态，thread_id 标识恢复哪条执行线。内存 checkpointer 只在进程活着时有效，不能证明重启恢复。审批内容应绑定规范化动作参数和任务版本；不能只保存一个全局 approved=True。

LangGraph 的 interrupt 暂停执行，使用相同 thread_id 和 Command(resume=...) 恢复。恢复时包含 interrupt 的节点可能从头执行，因此 interrupt 前的副作用可能重复。把真正写入放在审批之后的独立节点，仍需下一节的业务幂等。

示例先用 SQLite 保存提案并关闭连接，重新打开后校验审批。连接重开测试只覆盖存储语义，实际进程重启的图恢复在下方框架练习完成。修改参数时必须重新提出审批；拒绝则进入 rejected，不能继续写。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import hashlib
import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

def digest(action):
    return hashlib.sha256(json.dumps(action, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

proposal = {"tool": "create_ticket", "order_id": "A100", "reason": "损坏", "revision": 1}
with TemporaryDirectory() as tmp:
    path = Path(tmp) / "checkpoint.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, proposal TEXT, status TEXT)")
    conn.execute("INSERT INTO tasks VALUES (?,?,?)", ("t1", json.dumps(proposal), "waiting_approval"))
    conn.commit()
    conn.close()
    conn = sqlite3.connect(path)
    raw, status = conn.execute("SELECT proposal,status FROM tasks WHERE id=?", ("t1",)).fetchone()
    restored = json.loads(raw)
    assert status == "waiting_approval" and restored == proposal
    def resume(action, approved, approved_digest):
        if not approved:
            return "rejected"
        if digest(action) != approved_digest:
            return "approval_stale"
        return "ready_to_write"
    approved_digest = digest(restored)
    assert resume(restored, True, approved_digest) == "ready_to_write"
    assert resume(restored, False, approved_digest) == "rejected"
    assert resume({**restored, "order_id": "B200"}, True, approved_digest) == "approval_stale"
    conn.close()
print("PASS：存储重开、批准、拒绝与参数更改失效；尚未执行图恢复")
```

**预期现象：**恢复得到同一提案；精确匹配的批准可继续，拒绝与改参数都不能写入。哈希用于绑定内容，不能替代身份认证或审批签名。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

### 实际 LangGraph 两进程练习（本次未运行）

固定依赖：`langgraph==1.0.1`、`langgraph-checkpoint-sqlite==3.0.0`。练习时把下一块保存为临时 `/tmp/course_graph.py`，它是单文件完整示例，无其他课程脚本依赖。

```python
# course: optional
import hashlib
import json
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite import SqliteSaver

class State(TypedDict):
    action: dict
    status: str

def fingerprint(action):
    return hashlib.sha256(json.dumps(action, sort_keys=True).encode()).hexdigest()

def review(state):
    key = fingerprint(state["action"])
    decision = interrupt({"action": state["action"], "digest": key})
    valid = isinstance(decision, dict) and decision.get("digest") == key
    return {"status": "approved" if valid and decision.get("approve") is True else "rejected"}

def write(state):
    # 这里只模拟写节点；不创建真实工单，不提供重放幂等保证。
    print("执行已批准的模拟动作：", state["action"])
    return {"status": "simulated_written"}

builder = StateGraph(State)
builder.add_node("review", review)
builder.add_node("write", write)
builder.add_edge(START, "review")
builder.add_conditional_edges("review", lambda s: s["status"], {"approved": "write", "rejected": END})
builder.add_edge("write", END)
phase, db_path = sys.argv[1:3]
config = {"configurable": {"thread_id": "lesson-task-1"}}
with SqliteSaver.from_conn_string(db_path) as saver:
    graph = builder.compile(checkpointer=saver)
    if phase == "start":
        result = graph.invoke({"action": {"tool": "create_ticket", "order_id": "A100"},
                               "status": "waiting_approval"}, config)
    elif phase == "resume":
        state = graph.get_state(config)
        if not state.next:
            raise RuntimeError("没有待恢复节点")
        result = graph.invoke(Command(resume={"approve": sys.argv[3] == "approve",
                              "digest": fingerprint(state.values["action"])}), config)
    else:
        raise ValueError("phase 必须为 start 或 resume")
    print(result)
```

同一个数据库用两次命令、两个独立进程运行：

```bash
uv run --with 'langgraph==1.0.1' --with 'langgraph-checkpoint-sqlite==3.0.0' python /tmp/course_graph.py start /tmp/course-checkpoint-approve.sqlite
uv run --with 'langgraph==1.0.1' --with 'langgraph-checkpoint-sqlite==3.0.0' python /tmp/course_graph.py resume /tmp/course-checkpoint-approve.sqlite approve
```

再换一个新的数据库文件重复 start，将 resume 最后一个参数换成 `reject`，应看到 rejected 且无“执行已批准”输出。这些 SQLite 文件是恢复状态，非实验报告；课堂练习后可自行清理。不要对旧数据库重复 start 冒充全新任务。生产审批必须核对操作者身份、展示的提案摘要和实际提交摘要；示例 CLI 的 approve 只模拟可信人工输入。
## 实验步骤与练习

1. 运行标准库示例，解释 thread_id 与业务 task_id 如何关联到可信用户。
2. 按下方两进程步骤运行 start 与 resume，观察拒绝时不进入模拟写节点。
3. 修改订单后创建新的审批提案和版本；不要把旧 digest 复制给新动作。

## 常见错误

- 用内存存储演示却宣称重启恢复完成。
- interrupt 前直接创建工单。
- 把来自模型的 approved 字段当审批。

## 思考题

为什么恢复节点时可能重复执行 interrupt 前的代码？

<details>
<summary>参考答案（先自行作答）</summary>

恢复重新进入节点，把恢复值用于 interrupt 的返回；不是恢复 Python 调用栈的任意指令位置。因此前面的副作用要避免或做持久幂等。

</details>

## 验收标准

- [ ] 暂停记录可被重新读取且绑定准确参数。
- [ ] 拒绝与参数变化不会执行写入。
- [ ] 真实进程重启恢复单独验收。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 框架部分固定 langgraph 1.0.1、langgraph-checkpoint-sqlite 3.0.0；仅核对 API/版本与语法，未安装或运行。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [1.0.1 的 interrupt 与 Command 源码](https://github.com/langchain-ai/langgraph/blob/1.0.1/libs/langgraph/langgraph/types.py)
- [langgraph 1.0.1](https://pypi.org/project/langgraph/1.0.1/)
- [SQLite checkpointer 3.0.0](https://pypi.org/project/langgraph-checkpoint-sqlite/3.0.0/)

## 下一节衔接

下一节处理“写入已成功、回包却丢失”的未知结果。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
