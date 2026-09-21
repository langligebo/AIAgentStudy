# 第 07 周 Session 03：记忆纠正、冲突、过期与删除

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

避免旧偏好覆盖用户更正，给冲突和失效信息明确处理规则。

## 前置知识与学习安排

记忆来源、作用域与版本。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

记忆更新不应永远“最后写入赢”：慢请求可能携带旧信息。使用 revision 比较并要求更新引用当前版本，可拒绝陈旧写入。用户更正要替换当前值并使相关缓存失效。

来自检索的政策、用户自报地址和模型推测的地址不是同一种事实；先看来源权限和适用作用域，再处理冲突。没有充分证据时应追问，不能自动选听起来更合理的值。

过期是读取有效性规则；删除是移除后续使用权并清理缓存或索引。删除后仍要阻止在途旧请求“复活”记忆，可保留不含正文的版本墓碑。实际保留周期按产品需求设计，本例只演示版本机制。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
records, versions, cache = {}, {}, {}

def update(key, value, expected_revision, source="user_confirmed", expires=100):
    revision = versions.get(key, 0)
    if source != "user_confirmed":
        return "needs_confirmation"
    if revision != expected_revision:
        return "conflict"
    versions[key] = revision + 1
    records[key] = {"value": value, "revision": revision + 1, "source": source, "expires": expires}
    cache.pop(key, None)
    return "updated"

def read(key, now):
    row = records.get(key)
    return row["value"] if row and now < row["expires"] else None

def delete(key):
    records.pop(key, None)
    cache.pop(key, None)
    versions[key] = versions.get(key, 0) + 1

key = ("u1", "shipping_address")
assert update(key, "地址甲", 0) == "updated"
cache[key] = "地址甲"
assert update(key, "地址乙", 1) == "updated"
assert read(key, 10) == "地址乙" and key not in cache
assert update(key, "迟到的地址甲", 1) == "conflict"
assert update(key, "模型猜测地址", 2, "model_guess") == "needs_confirmation"
assert read(key, 100) is None
assert read(("u2", "shipping_address"), 10) is None
delete(key)
assert read(key, 10) is None
assert update(key, "旧请求复活", 2) == "conflict"
print("当前有效记忆：", records, "版本：", versions)
print("PASS：纠正、冲突、过期、用户隔离、删除后拒绝旧写入")
```

**预期现象：**只有地址乙在有效期内可读；过期或删除后读不到；删除前的旧版本无法写回。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 把读出的记忆标上来源，再与本轮用户更正比较，确认采用用户明确更新。
2. 模拟两次并发更新都携带同一 revision，只允许第一条成功，第二条需要重新读取并决策。
3. 列出删除涉及的数据库、缓存、上下文副本，设计下一轮重组上下文步骤。

## 常见错误

- 把时间更晚的模型推测覆盖用户确认。
- 删除数据库后忘记缓存。
- 把过期等同于物理清理。

## 思考题

用户删除偏好后在途模型请求返回旧偏好，能否再保存？

<details>
<summary>参考答案（先自行作答）</summary>

不能直接保存。校验版本和当前保留授权；本例通过墓碑版本拒绝旧请求。重新保存应由新的明确输入触发。

</details>

## 验收标准

- [ ] 用户更正后旧值不再参与后续回答。
- [ ] 冲突不会静默覆盖。
- [ ] 删除后旧请求不能复活记忆。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

上下文是本轮选择，长期记忆是有来源的跨会话信息，纠正和删除决定哪些旧信息不能继续使用。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 在有限预算内保留目标、约束和必要证据，并解释裁剪策略的损失。 |
| [Session 02](../session_02/README.md) | 用结构化存储保存最少必要偏好，读取时按可信用户身份隔离。 |
| [Session 03](../session_03/README.md) | 避免旧偏好覆盖用户更正，给冲突和失效信息明确处理规则。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [上下文工程](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Python SQLite](https://docs.python.org/3.12/library/sqlite3.html)

## 下一节衔接

本节完成本模块前三节的阶段复盘，接着学习新增的[Session 04](../session_04/README.md)；原下一模块安排顺延，历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
