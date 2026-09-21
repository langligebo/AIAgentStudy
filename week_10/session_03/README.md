# 第 10 周 Session 03：配对对照、回归与发布判断

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

用固定开发集、保留集和重复运行分析改进与退化，结合质量、调用量和成本判断。

## 前置知识与学习安排

端到端指标、版本追踪、开发与验收隔离。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

对照应匹配相同任务、运行条件和重复轮次，明确唯一主要变化。开发集用于调整，保留集用于冻结方案后的验收；一旦用保留集错误反复调参，它已参与开发，需另留新的独立验证。

重复运行揭示波动，但不同样本不能当作同一个输入的重复。统计整体成功率之外，要列出旧版成功新版失败的退化，尤其是安全负例。小样本无退化不证明没有退化，不能直接作普遍结论。

延迟、调用数、本地资源与远程费用需要分别记录。没有实际计费数据就标 unknown，不能用模拟耗时推断远程成本。下方数据是手工夹具，展示配对计算和门槛，不是已经完成的模型实验报告。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from statistics import mean

# 每个 case 两次重复；False 保留在端到端分母中。
old = {"normal": [True, True], "no_answer": [True, False], "deny": [True, True]}
new = {"normal": [True, True], "no_answer": [True, True], "deny": [True, False]}
assert old.keys() == new.keys()
paired = []
for case in old:
    assert len(old[case]) == len(new[case])
    for repeat, (a,b) in enumerate(zip(old[case],new[case]), 1):
        paired.append({"case": case, "repeat": repeat, "old": a, "new": b})
regressions = [r for r in paired if r["old"] and not r["new"]]
improvements = [r for r in paired if not r["old"] and r["new"]]
old_score = mean(r["old"] for r in paired)
new_score = mean(r["new"] for r in paired)
safety_failed = any(r["case"] == "deny" and not r["new"] for r in paired)
release = new_score >= old_score and not safety_failed
assert old_score == new_score
assert len(improvements) == len(regressions) == 1
assert not release
print("旧/新成功率：", old_score, new_score)
print("改进：", improvements, "退化：", regressions)
print("模拟调用数：", {"old": 12, "new": 16}, "真实费用：未验证", "允许发布：", release)
print("PASS：分母、重复配对、平均值掩盖退化、安全门槛")
```

**预期现象：**两个版本平均成功率相同，但新版在拒绝越权样本退化，发布被拒绝；新版本还增加模拟调用量。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## RAG 补充：逐项消融与效果归因

使用[第六周知识清单](../../week_06/RAG_ROADMAP.md)中的方法时，先固定知识版本、问题、预期证据、模型与预算，再比较一个因素。公开教案例子属于开发数据，不能同时称独立保留集。

| 对照 | 保持不变 | 重点观察 |
| --- | --- | --- |
| 基础分块 vs 父子分块 | 查询、原文与有效版本 | 例外条款遗漏、召回和上下文占用 |
| BM25 / 向量 vs 混合＋RRF | 已授权知识集合和候选预算 | 精确型号、同义表述、噪声候选 |
| 无重排 vs Cross-encoder | 同一候选集合 | Context Precision、首条命中和额外延迟 |
| 单查询 vs HyDE / Multi-Query / 分解 | 用户真实意图、数据、过滤规则 | 必需证据覆盖、查询漂移、调用数量 |
| 原文 vs 压缩；位置 A vs B | 各自固定其他变量 | 限定/否定遗漏、Faithfulness、位置敏感性 |
| 固定 RAG Workflow vs Agentic RAG | 工具、身份、资料、验收标准 | 补查收益、停止理由、预算和正确拒答 |

从坏例出发：型号错优先检查解析/词项和过滤；候选没找到查召回；候选有但噪声挤占查融合/重排；证据正确而回答漏例外查上下文与生成。不要同时启用全部增强后只报一个最终分数。

RAGAS 评分模型也要固定并记录失败。用一组人工标注抽查模型评分，防止所谓提升只是评分器偏好变化。RAPTOR/GraphRAG 若进入工程对照，还须计入索引构建/更新成本、原始证据可追溯性与删除/权限传播；本次没有这两套工程的实测结果。

正常对照应能复现同一输入的各层结果；边界对照加入无答案、错型号、过期文档、错误假设和缺失例外。所有原始分数、耗时与回答只打印控制台，学习进度只保存简短实际证据。

## 实验步骤与练习

1. 增加超时样本并保持在计划分母中，区分尚未尝试与尝试失败。
2. 先设定门槛，再改新版本结果；不要为了通过而事后改门槛。
3. 冻结模型、Prompt、Skill、数据和流程后执行保留集；只在进度中记简短实际证据，原始统计留终端。

## 常见错误

- 平均成功率没下降就忽略安全退化。
- 把展示过的教学案例叫未知保留集。
- 把费用未记录写成零成本。

## 思考题

成功率一样，新版仍值得升级吗？

<details>
<summary>参考答案（先自行作答）</summary>

需要看任务覆盖、退化类型、延迟与成本。本例出现安全退化且调用更多，门槛拒绝；其他场景也应按预先约定标准和实际证据判断。

</details>

## 验收标准

- [ ] 重复轮次一一配对。
- [ ] 改进与退化样本均可定位。
- [ ] 保留集和费用未知状态诚实记录。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

分层评分解释失败，轨迹提供事实，对照回归决定版本能否发布；平均成功率不能掩盖安全退化。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 分别定位格式、检索、工具选择、轨迹和业务终态错误，并认识模型评分的边界。 |
| [Session 02](../session_02/README.md) | 用任务和步骤标识串联请求、观察和状态，记录版本并避免在日志中泄露凭据。 |
| [Session 03](../session_03/README.md) | 用固定开发集、保留集和重复运行分析改进与退化，结合质量、调用量和成本判断。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Agent 评估的任务、轨迹与结果](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## 下一节衔接

本节完成本模块前三节的阶段复盘，接着学习新增的[Session 04](../session_04/README.md)；原下一模块安排顺延，历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
