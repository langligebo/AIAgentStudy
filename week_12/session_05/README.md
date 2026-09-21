# 第 12 模块 Session 05：事件流、背压与人工审核体验

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

使客户端断线和慢消费时仍能理解任务状态，审批精确绑定动作。

## 前置知识与学习安排

任务式 HTTP API、流式组装、审批 digest。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

SSE 将服务器事件推给客户端，事件 ID 和 Last-Event-ID 可帮助重连；它不能自动提供永久历史或 exactly-once。事件可能重复或超出保留窗口，客户端按 ID 去重，缺口则请求状态快照。WebSocket 提供双向交互，是否需要取决于任务，不因为使用 Agent 就必须使用。

慢客户端会积压缓冲，服务端要限大小并选择合并可丢的进度事件或断开连接；终态、审批和错误不能悄悄丢失。断开显示连接与取消任务是两个动作，产品需明确区分。事件总线必须按可信用户过滤，随机 task_id 不是权限。

人工审核界面需要展示动作、目标资源、关键参数、证据、风险/结果范围和提案版本。批准、修改、拒绝各自记录；修改导致原签名/摘要失效，审批超时不等于批准。用户应能看到等待输入、执行中、已完成、未知待核对，而不是永远一个转圈。

下例验证事件重放与状态快照边界，不启动 HTTP；真正 SSE 还需要编码、心跳、代理超时和取消清理的联调。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
EVENTS = [{"id":i,"task":"t1","owner":"u1","status":s} for i,s in [(4,"running"),(5,"waiting_approval"),(6,"success")]]
def replay(owner, last_id):
    visible = [e for e in EVENTS if e["owner"] == owner]
    if not visible: return {"events":[]}
    if last_id < visible[0]["id"]-1: return {"snapshot_required":True}
    return {"events":[e for e in visible if e["id"] > last_id]}

def consume(events, seen):
    accepted=[]
    for e in events:
        if e["id"] in seen: continue
        seen.add(e["id"]); accepted.append(e)
    return accepted

assert replay("u1",0) == {"snapshot_required":True}
assert [e["id"] for e in replay("u1",4)["events"]] == [5,6]
assert replay("u2",4) == {"events":[]}
seen=set()
assert len(consume(EVENTS+EVENTS,seen)) == 3
assert consume(EVENTS,seen) == []
print("PASS：重连缺口、去重、跨用户过滤")
```

**预期现象：**过旧游标要求快照，重复事件只消费一次，无权限用户收不到事件。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 把前一节任务状态转换成固定事件 Schema，并区分进度与必须保留的终态。
2. 参考官方 SSE 格式接入现有 FastAPI，使用测试客户端模拟半帧、重复、断线重连和慢消费。
3. 设计审批页面字段，将批准绑定到当前任务版本与动作摘要；测试提案被修改、过期和拒绝。
4. 增加事件缓冲上限与快照恢复，解释用户关闭页面后任务如何处理。

## 常见错误

- 流断开就宣布远程工具已取消。
- 自动把超时审批当同意。
- 客户端收到 success 文本但没有对应业务核验。

## 思考题

Last-Event-ID 是否意味着服务器一定能重放所有事件？

<details>
<summary>参考答案（先自行作答）</summary>

不是。它只传递客户端的恢复位置，服务端必须有对应保留策略；超过窗口时应回状态快照而非静默跳过。

</details>

## 验收标准

- [ ] 事件丢失/重复/保留过期均有恢复路径。
- [ ] 用户可分辨取消请求与实际停止。
- [ ] 审批展示与服务器执行参数完全对应。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [SSE 标准](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [FastAPI 自定义响应](https://fastapi.tiangolo.com/advanced/custom-response/)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_04/README.md) · [下一节](../session_06/README.md)
