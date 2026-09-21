# 第 08 周 Session 01：LangGraph 的 State、Node 与 Edge

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_07/session_04/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

将已理解的循环映射到图状态、节点更新和条件边，并用相同输入比较行为。

## 前置知识与学习安排

第 4 周手写循环；TypedDict 只描述类型，不自动校验运行时数据。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

State 是节点共享的数据契约，Node 读取状态并返回更新，Edge 指定下一节点，条件边根据当前结果路由。模型仍然通过统一客户端调用；框架提供编排能力，不替代工具权限、预算和终态验证。

迁移先从最小流程开始：查询订单→成功时查政策→结束；查询不到走失败终态。默认字段更新可以覆盖旧值；累积消息或轨迹时要明确 reducer 或显式返回新列表，避免误以为框架自动追加任意列表。

本课先用标准库模拟图路由并与手写流程比较，再提供真正的 LangGraph 代码。模拟器不实现 checkpoint、并行 super-step 或 reducer，它的作用只是帮助看清职责。相同案例应比较业务状态与关键工具顺序，不要求内部日志逐字相同。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from typing import TypedDict

class State(TypedDict):
    order_id: str
    status: str
    trace: list[str]

ORDERS = {"A100": "keyboard"}
def order_node(state):
    exists = state["order_id"] in ORDERS
    return {**state, "status": "found" if exists else "not_found", "trace": state["trace"] + ["order"]}

def policy_node(state):
    return {**state, "status": "success", "trace": state["trace"] + ["policy"]}

def graph_like(order_id):
    state = {"order_id": order_id, "status": "running", "trace": []}
    node = "order"
    for _ in range(3):
        state = {"order": order_node, "policy": policy_node}[node](state)
        if node == "order" and state["status"] == "found":
            node = "policy"
        else:
            return state
    raise RuntimeError("budget")

def handwritten(order_id):
    state = order_node({"order_id": order_id, "status": "running", "trace": []})
    return policy_node(state) if state["status"] == "found" else state

for order_id, expected in (("A100", "success"), ("missing", "not_found")):
    assert graph_like(order_id) == handwritten(order_id)
    assert graph_like(order_id)["status"] == expected
    print(order_id, graph_like(order_id))
print("PASS：手写与图式路由的正常、无订单路径一致")
```

**预期现象：**A100 的轨迹为 order、policy；缺订单只运行 order；两种实现的状态相同。这一验证尚未执行 LangGraph。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

### 实际 LangGraph 示例（依赖未安装，本次仅核对 API 与语法）

教学固定 `langgraph==1.0.1`，不是“最新版”声明。到本节时可用临时附加依赖，避免现在改项目依赖：

```bash
uv run --with 'langgraph==1.0.1' python
```

在该 Python 环境执行下面完整块（独立于上方变量）：

```python
# course: optional
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    order_id: str
    status: str
    trace: list[str]

def order(state: State):
    return {"status": "found" if state["order_id"] == "A100" else "not_found",
            "trace": state["trace"] + ["order"]}

def policy(state: State):
    return {"status": "success", "trace": state["trace"] + ["policy"]}

def route(state: State):
    return "policy" if state["status"] == "found" else "done"

builder = StateGraph(State)
builder.add_node("order", order)
builder.add_node("policy", policy)
builder.add_edge(START, "order")
builder.add_conditional_edges("order", route, {"policy": "policy", "done": END})
builder.add_edge("policy", END)
graph = builder.compile()
for oid, expected in (("A100", "success"), ("missing", "not_found")):
    result = graph.invoke({"order_id": oid, "status": "running", "trace": []})
    assert result["status"] == expected
    print(result)
```

预计正常与无订单路径和离线对照一致；以届时实际运行结果为准。此块没有模型请求。
## 实验步骤与练习

1. 先运行离线对照，画出查询失败分支。
2. 学到本节时再安装下方指定版本，运行真正的图示例，比较相同输入的状态和轨迹。
3. 将第 4 周的模型决策节点接入图时保留客户端与执行器，仅迁移状态和边，不同时修改 Prompt。

## 常见错误

- 把 TypedDict 当作自动输入校验。
- 迁移框架时同时改模型和 Prompt，无法归因。
- 默认列表会自动追加，覆盖掉旧轨迹。

## 思考题

引入 LangGraph 后执行器权限检查可以删除吗？

<details>
<summary>参考答案（先自行作答）</summary>

不可以。框架编排节点和保存状态，业务身份、资源权限、输入校验与审批仍然是应用职责。

</details>

## 验收标准

- [ ] 能把第 4 周概念对应到 State、Node、Edge。
- [ ] 相同正常与失败样本行为可对照。
- [ ] 区分模拟图验证与真实框架验证。

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

下一节给图加持久 checkpoint，并在写入前暂停等待人确认。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_07/session_04/README.md) · [下一节](../session_02/README.md)
