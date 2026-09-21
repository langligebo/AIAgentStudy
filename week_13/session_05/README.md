# 第 13 模块 Session 05：CI、发布、备份恢复与生产验收

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

使他人能重建环境、部署、回退和恢复，并用事先标准决定能否交付。

## 前置知识与学习安排

第十二模块服务可靠性及 W13 S04 实际集成。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

持续集成应分离快速确定性测试与受控模型测试：前者每次变更运行，后者固定模型/数据/预算，在指定环境执行。lint、类型检查、依赖/秘密扫描、契约和安全回归是不同检查；不能把某一个绿灯当全部验收。模型测试不使用线上写工具。

发布清单固定代码、依赖锁、模型与量化、Prompt、Skill、索引、状态 schema 和配置。候选发布先离线回归，再预发布真实链路，最后小流量/明确授权部署。数据迁移与旧 checkpoint 可读性要先验证，回滚程序不能自动回滚外部副作用。

备份必须通过恢复演练证明可用。RPO 表达允许丢失多少时间的数据，RTO 表达恢复目标时间；任务、审批、幂等键、知识来源版本需要一起考虑。不能只恢复工单表却丢掉去重记录，然后重新创建已发生动作。

本例执行 SQLite 备份与恢复，并以 schema 门槛拒绝不兼容发布；不启动容器或修改真实系统。最后验收包括质量、权限、故障恢复、性能、运行手册和用户理解，所有未知项保留。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
import sqlite3
source=sqlite3.connect(":memory:")
backup=sqlite3.connect(":memory:")
restored=sqlite3.connect(":memory:")
try:
    source.execute("CREATE TABLE tickets(action_key TEXT PRIMARY KEY,order_id TEXT)")
    source.execute("INSERT INTO tickets VALUES ('task1-action1','A100')")
    source.commit()
    source.backup(backup); backup.backup(restored)
    assert restored.execute("SELECT order_id FROM tickets WHERE action_key=?",('task1-action1',)).fetchone()==('A100',)
    try:
        restored.execute("INSERT INTO tickets VALUES ('task1-action1','A100')")
    except sqlite3.IntegrityError: restored.rollback()
    else: raise AssertionError("idempotency lost after restore")
    assert restored.execute("SELECT count(*) FROM tickets").fetchone()[0]==1
finally:
    restored.close(); backup.close(); source.close()

def release_ok(manifest, state_schema, tests):
    return state_schema in manifest["readable_schemas"] and all(tests.values()) and bool(tests)
assert release_ok({"readable_schemas":{1,2}},2,{"contract":True,"security":True})
assert not release_ok({"readable_schemas":{1}},2,{"contract":True})
assert not release_ok({"readable_schemas":{1,2}},2,{"security":False})
assert not release_ok({"readable_schemas":{1,2}},2,{})
print("PASS：备份恢复后去重仍在、空测试和不兼容发布拒绝")
```

**预期现象：**恢复后仍能核对工单和幂等键；空测试集合不能成为发布通过。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 编写可从空环境复现的命令，明确 Python、锁文件、模型、配置与数据库准备顺序。
2. 建立 CI 分层清单，快速测试不联网；模型/API 密钥仅在受控环境注入。
3. 使用模拟服务做重启、负载、队列积压、依赖故障、备份恢复和回退，记录 RPO/RTO 实际证据。
4. 冻结保留集做端到端验收，演示正常、拒绝、恢复、未知四条路径；由用户确认学习掌握。

## 常见错误

- 备份文件存在就认为可恢复。
- 旧镜像启动成功就认为状态兼容。
- 发布失败时重新执行未知写操作。

## 思考题

为什么模型测试与普通单元测试要分层？

<details>
<summary>参考答案（先自行作答）</summary>

模型有网络、费用、版本和采样波动；确定性测试适合快速定位代码问题，真实模型测试验证能力和效果，两者都不能互相替代。

</details>

## 验收标准

- [ ] 全新环境可以按说明启动并运行同一验收集。
- [ ] 恢复后身份、审批、幂等和来源版本一致。
- [ ] 上线/回退门槛预先确定且有实际证据。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [SQLite backup API](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.backup)
- [Docker 构建建议](https://docs.docker.com/build/building/best-practices/)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_04/README.md) · [下一节](../session_06/README.md)
