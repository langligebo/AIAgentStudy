# 第 08 模块 Session 04：LangGraph 并行状态、子图与流式事件

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

理解 reducer、并行合并、子图边界和事件输出，防止迁移后丢状态。

## 前置知识与学习安排

第八模块前三节与 asyncio 基础。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

图编排不只包含顺序节点。并行节点可能在同一 super-step 更新共享字段；需要明确哪些字段覆盖、哪些按 reducer 合并。列表累加方便追踪，但可能产生重复；去重合并又必须识别同 ID 不同内容，不能任意最后写入获胜。

Send 可表达动态扇出，Command 可表达更新与控制转移，子图封装一段职责并映射输入输出。它们不是新的权限来源；把身份、预算、任务版本传入子图，避免靠全局变量共享状态。并行写入的审批、幂等仍由业务层处理。

流式图状态、模型 token、工具进度是不同事件。UI 可以展示进行中，但只有终态核验表示任务完成。stream_mode、子图事件命名空间、checkpoint 与中断行为按实际 LangGraph 版本核对；时光回溯或重放不能撤回已经发生的外部动作。

下例验证合并语义；下方真框架块在教学固定版本运行时才验证实际调度。state schema 迁移要定义旧 checkpoint 的读取、升级和回退，不能只改 TypedDict 就重启。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
def merge(left, right):
    result = {x["id"]:x for x in left}
    for x in right:
        if x["id"] in result and result[x["id"]] != x: raise ValueError("conflicting_evidence")
        result[x["id"]] = x
    return [result[k] for k in sorted(result)]

a = [{"id":"order:A100","value":"shipped"}]
b = [{"id":"policy:K1","value":"seven_days"}]
assert merge(a,b) == merge(b,a)
assert merge(a,a) == a
assert merge(merge(a,b),a) == merge(a,merge(b,a))
try: merge(a,[{"id":"order:A100","value":"cancelled"}])
except ValueError: pass
else: raise AssertionError("conflict silently overwritten")
print("PASS：交换/结合、幂等与冲突拒绝；不是图调度测试")
```

**预期现象：**相同证据重复合并不会膨胀，冲突值需要显式处理。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。

## 真框架最小并行：本次仅语法检查

安装方式沿用本模块：`uv run --with 'langgraph==1.0.1' python -`。下块独立运行，不依赖上方 merge。这是框架实验，不调用模型；生产持久化仍用前两节的 checkpoint 练习。

<!-- verify: external -->
```python
from typing import Annotated, TypedDict
from operator import add
from langgraph.graph import StateGraph, START, END
class State(TypedDict):
    trace: Annotated[list[str], add]
def order(state): return {"trace": ["order"]}
def policy(state): return {"trace": ["policy"]}
def finish(state): return {"trace": ["finished"]}
g = StateGraph(State)
g.add_node("order", order); g.add_node("policy", policy); g.add_node("finish", finish)
g.add_edge(START,"order"); g.add_edge(START,"policy")
g.add_edge(["order","policy"],"finish"); g.add_edge("finish",END)
app = g.compile()
result = app.invoke({"trace": []})
assert set(result["trace"][:-1]) == {"order","policy"}
assert result["trace"][-1] == "finished"
for event in app.stream({"trace": []}, stream_mode="updates"): print(event)
```

## 实验步骤与练习

1. 比较覆盖、列表追加与按 ID 合并，解释每种会在哪个场景出错。
2. 运行下面的框架块，观察两个分支合并；再制造同 ID 冲突。
3. 把政策节点改成子图，显式映射状态；记录子图错误、中断与事件如何回到父图。
4. 设计 Send 扇出与总预算，测试一个分支失败、取消、超时及旧 checkpoint 恢复。

## 常见错误

- 并行节点修改同一个列表对象。
- 把图事件文本当最终业务状态。
- 用重放恢复已执行的外部动作却不用幂等。

## 思考题

为什么 reducer 应尽量避免依赖分支完成顺序？

<details>
<summary>参考答案（先自行作答）</summary>

并发调度顺序不稳定，顺序敏感会导致结果漂移；需要明确的合并规则或显式串行依赖。

</details>

## 验收标准

- [ ] 能选用并验证合并语义。
- [ ] 真实框架并行/子图行为有独立实验记录。
- [ ] state 版本与恢复策略明确。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph 子图](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../../week_09/session_01/README.md)
