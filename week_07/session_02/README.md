# 第 07 周 Session 02：任务、历史与长期记忆存储

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

用结构化存储保存最少必要偏好，读取时按可信用户身份隔离。

## 前置知识与学习安排

任务状态、字典、SQL 参数绑定基础。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

任务状态描述正在执行的工作；对话历史帮助理解交流；长期记忆保存跨会话仍有价值的信息。不是所有对话都值得入库：临时订单查询和未经证实的模型推断不应自动变成长期事实。

记忆至少包含 owner、key、value、source、scope、updated_at，必要时有过期时间。读取必须从已认证用户上下文确定 owner，不能让模型任意选别人的用户标识。示例用函数参数模拟可信上下文，在真实 API 中它由身份中间件提供。

SQLite 适合展示持久数据与事务；本例使用临时数据库，关闭再打开验证持久性，完成后清理。这是教学输入和运行状态，不是保存模型输出报告。保存到项目常驻路径应等到本节实践时明确设计保留和删除规则。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as tmp:
    db = str(Path(tmp) / "memory.db")
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE memory (owner TEXT, key TEXT, value TEXT, source TEXT, scope TEXT, updated_at TEXT, PRIMARY KEY(owner,key))")
    def save(owner, key, value, source):
        if source != "user_confirmed":
            raise ValueError("unconfirmed_source")
        conn.execute("INSERT OR REPLACE INTO memory VALUES (?,?,?,?,?,?)",
                     (owner, key, value, source, "support", "2026-09-21"))
        conn.commit()
    save("u1", "language", "中文", "user_confirmed")
    save("u2", "language", "English", "user_confirmed")
    try:
        save("u1", "address", "模型猜的地址", "model_guess")
    except ValueError:
        pass
    else:
        raise AssertionError("不应将猜测保存为事实")
    conn.close()
    conn = sqlite3.connect(db)
    def read_for(trusted_user, key):
        row = conn.execute("SELECT value,source FROM memory WHERE owner=? AND key=? AND scope=?",
                           (trusted_user, key, "support")).fetchone()
        return row
    assert read_for("u1", "language") == ("中文", "user_confirmed")
    assert read_for("u2", "language")[0] == "English"
    assert read_for("u3", "language") is None
    assert read_for("u1", "address") is None
    assert read_for("u1' OR 1=1 --", "language") is None
    print(read_for("u1", "language"))
    conn.close()
print("PASS：重开数据库、用户隔离、来源拒绝、参数化查询")
```

**预期现象：**数据库重开后读到 u1 的中文偏好；其他用户、伪造 SQL 身份和模型猜测均读不到该记忆。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 把同一 key 写入两个用户，验证主键包含 owner。
2. 用来源字段区分用户确认与文档事实，规定哪些字段允许长期保存。
3. 设计读取 API，明确 trusted_user 从何处来；不要给模型暴露“任意用户查询”的参数。

## 常见错误

- 把聊天全文当唯一长期记忆。
- 全局 language key 导致用户互相覆盖。
- 为了查记忆直接拼接 SQL。

## 思考题

为什么保存 source 比只保存 value 有用？

<details>
<summary>参考答案（先自行作答）</summary>

更正、冲突和验收时需要判断谁提供了信息、是否确认、何时生效。没有来源，系统无法区分用户明确偏好和模型猜测。

</details>

## 验收标准

- [ ] 重开后能读取必要偏好。
- [ ] 不同用户数据相互隔离。
- [ ] 未确认模型输出不自动进入事实记忆。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [上下文工程](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Python SQLite](https://docs.python.org/3.12/library/sqlite3.html)

## 下一节衔接

下一节为记忆增加冲突检测、过期和删除。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
