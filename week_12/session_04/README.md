# 第 12 模块 Session 04：持久任务队列、租约与事务发件箱

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

理解进程崩溃和重复投递时如何接续任务，不丢状态也不重复业务写入。

## 前置知识与学习安排

第八模块幂等与第十二模块前三节。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

进程内 BackgroundTasks/字典不能提供持久队列保证。任务提交应将状态与待投递事件一同提交，事务发件箱（outbox）解决“数据库已写但消息没发”的窗口；投递通常至少一次，消费者必须幂等，不能靠一句 exactly-once 消除跨系统故障。

Worker 用租约领取任务，超时后可重新领取。租约过期不表示旧 worker 已停，需 fencing token/版本防止旧 worker 提交结果；业务副作用仍需服务端幂等。重试次数、退避、死信队列、人工核对与最大执行时间都应明确。

下例用 SQLite 原子状态与 outbox，再演示租约版本；没有外部 broker、多 worker 压测或分布式锁，不把单进程例子称为生产队列。持久实验用临时数据库验证状态，输出仅控制台。

补偿不是事务回滚的同义词。退款通知已送达无法“没发生”，需要领域定义的补偿和人工介入；未知结果仍先核对，不能因为 worker 租约失效就再发一次。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
import sqlite3
c = sqlite3.connect(":memory:")
c.executescript("CREATE TABLE tasks(id TEXT PRIMARY KEY,state TEXT,epoch INT); CREATE TABLE outbox(id TEXT PRIMARY KEY,sent INT);")
def submit(key):
    with c:
        c.execute("INSERT OR IGNORE INTO tasks VALUES (?, 'queued', 0)",(key,))
        c.execute("INSERT OR IGNORE INTO outbox VALUES (?,0)",(key,))
def claim(key):
    with c:
        c.execute("UPDATE tasks SET state='running',epoch=epoch+1 WHERE id=? AND state IN ('queued','running')",(key,))
    return c.execute("SELECT epoch FROM tasks WHERE id=?",(key,)).fetchone()[0]
def complete(key,epoch):
    with c:
        changed = c.execute("UPDATE tasks SET state='done' WHERE id=? AND epoch=? AND state='running'",(key,epoch)).rowcount
    return bool(changed)
submit("t1"); submit("t1")
assert c.execute("SELECT count(*) FROM outbox").fetchone()[0] == 1
old = claim("t1")
# 模拟调度器已经确认租约过期后再次领取；本例不实现实际租约时钟。
new = claim("t1")
assert not complete("t1", old)
assert complete("t1", new)
assert not complete("t1", new)
assert c.execute("SELECT state FROM tasks").fetchone()[0] == "done"
c.close()
print("PASS：提交去重、事务发件箱记录、旧 worker 提交拒绝")
```

**预期现象：**重复提交只保留一条 outbox 记录，旧 worker 的完成事件被拒绝。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 画出 submit、投递、领取、业务写入、ack、checkpoint 的崩溃窗口。
2. 把数据库改成临时文件并在两进程间恢复；在每个窗口 kill 测试 worker，使用模拟工具核对副作用数量。
3. 实现租约时钟、退避上限与死信检查，复验旧 worker 晚到及服务端幂等。
4. 再选一个消息队列验证重复投递与确认行为，版本固定、无真实业务数据；不同时引入多个队列。

## 常见错误

- worker 消失就等同业务失败。
- 客户端生成随机新幂等键来重试。
- 用 outbox 唯一键宣称远程动作只发生一次。

## 思考题

租约过期后为什么不能信任旧 worker 的成功响应？

<details>
<summary>参考答案（先自行作答）</summary>

它可能针对旧任务版本运行，且新 worker 已接管；需要 fencing 与当前版本校验，副作用仍要单独核实。

</details>

## 验收标准

- [ ] 能逐个解释故障窗口的恢复方式。
- [ ] 重复投递/旧 worker 不导致错误终态覆盖。
- [ ] 未知副作用、死信与人工接管都有策略。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [SQLite 事务](https://www.sqlite.org/lang_transaction.html)
- [RabbitMQ 可靠性](https://www.rabbitmq.com/docs/reliability)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../session_05/README.md)
