# 第 09 模块 Session 05：A2A 与跨 Agent 任务协议

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

区分本进程分工与跨服务协作，识别发现、任务状态、产物及授权边界。

## 前置知识与学习安排

W09 S04；HTTP/JSON，MCP 差异在第十一模块再对照。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

A2A 处理 Agent 之间的交互，MCP 连接应用与工具/数据能力；它们可以组合。Agent Card 描述能力和连接方式，但可发现不等于可信或有权限。远程 Agent 的能力说明和产物都需要校验，不能把远程文本提升为本地系统指令。

A2A 的消息与长期 Task 不同，context 关联多个交互，task_id 指向一个任务，artifact 表达结果。等待输入、等待授权与最终失败也不同。已完成任务的后续改动通常作为新的关联任务处理，不偷偷修改旧验收证据。

本节以 2026-09-21 官方 v1.0 文档的概念为核对范围。下例采用课程内部状态与消息字段，不是符合 wire schema 的 A2A 服务，也不假装安装了 SDK。传输绑定、字段序列化和鉴权必须按选定协议/SDK 版本单独验证。

远程交互要处理重复消息、断线恢复、异步通知、产物版本和取消未必成功。任何远程写入的结果未知仍需核对；不因跨 Agent 就把幂等和责任转移给对方。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
class Task:
    def __init__(self):
        self.state = "working"; self.seen = set(); self.artifacts = {}
    def apply(self, event):
        eid = event["event_id"]
        if eid in self.seen: return "duplicate"
        if self.state in {"completed","failed","canceled"}: raise ValueError("terminal")
        state = event["state"]
        if state not in {"working","input_required","completed","failed","canceled"}: raise ValueError("state")
        if state == "completed" and not event.get("artifact"): raise ValueError("no_artifact")
        self.seen.add(eid); self.state = state
        if event.get("artifact"): self.artifacts[eid] = event["artifact"]
        return state

t = Task()
e = {"event_id":"e1","state":"input_required"}
assert t.apply(e) == "input_required"
assert t.apply(e) == "duplicate"
assert t.apply({"event_id":"e2","state":"working"}) == "working"
try: t.apply({"event_id":"e3","state":"completed"})
except ValueError: pass
else: raise AssertionError("false completion")
assert t.apply({"event_id":"e4","state":"completed","artifact":{"evidence":["p1"]}}) == "completed"
try: t.apply({"event_id":"e5","state":"working"})
except ValueError: pass
else: raise AssertionError("terminal overwritten")
print("PASS：课程内部生命周期、事件去重和产物要求；非 A2A 协议实现")
```

**预期现象：**重复通知不重复处理，无产物不能按本任务契约完成，终态不可覆盖。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 画出 Agent Card 发现→身份/能力核验→发起消息→任务/产物→验收的数据流。
2. 将内部状态映射到固定版本官方 schema，列出不能直接同名映射的字段。
3. 跟随官方 Python quickstart 在独立环境做一次双服务通信；固定实际 SDK 版本并记录日志，不改已有 MCP 示例来冒充 A2A。
4. 用重复事件、取消冲突、错误身份和过期产物做失败测试；未实跑前保留未验证。

## 常见错误

- 把 Agent Card 当作访问凭证。
- 把两次模型调用当跨服务 A2A 联调。
- 等待用户状态被计作运行成功。

## 思考题

远程 Agent 返回一个工单编号，是否足以说明本地任务成功？

<details>
<summary>参考答案（先自行作答）</summary>

还要验证任务/用户关联、返回来源、工单实际状态和所需业务标准，远程产物也可能错误或过期。

</details>

## 验收标准

- [ ] 能区分工具接入协议与 Agent 任务协议。
- [ ] 跨服务任务有身份、关联、终态和产物校验。
- [ ] 内部夹具与真实协议兼容记录分开。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [A2A 规范](https://a2a-protocol.org/latest/specification/)
- [Task 生命周期](https://a2a-protocol.org/latest/topics/life-of-a-task/)
- [A2A Python 入门](https://a2a-protocol.org/latest/tutorials/python/1-introduction/)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_04/README.md) · [下一节](../../week_10/session_01/README.md)
