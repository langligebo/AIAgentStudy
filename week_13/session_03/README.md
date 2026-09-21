# 第 13 周 Session 03：基础项目验收、演示与学习复盘

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

以预定标准验收最终系统，对照基线交付可复现说明和明确限制。

## 前置知识与学习安排

综合项目实际实现、版本清单与独立保留集；未完成则保留待验收。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

冻结代码、模型与参数、Prompt、Skill、知识库和执行策略后，在未用于调参的保留集上运行。按计划样本统计成功、失败、未知和未运行；没有证据的样本不能当成功。与第 2 周基线比较时注意任务范围已经变化，只有同定义子任务才可直接比较指标。

交付包括安装与配置、启动/取消/恢复操作、测试数据、权限与审批范围、已知限制及代表性轨迹。原始模型回答和统计仍在终端展示；项目进度只记录简短证据。不要为了“交付报告”自动把用户不想保存的实验输出写入文件。

演示至少包含一条正常售后、一条拒绝越权、一条恢复核验和一条未知结果需接管。下方只测试验收汇总器；刻意留下 unknown 与 not_run，使它不能生成“全部通过”。实际毕业验收以用户运行和理解反馈确认。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from collections import Counter

VALID = {"passed", "failed", "unknown", "not_run"}

def summarize(plan, observed):
    if set(observed) - set(plan):
        raise ValueError("unplanned_case")
    rows = {case: observed.get(case, "not_run") for case in plan}
    if any(status not in VALID for status in rows.values()):
        raise ValueError("invalid_status")
    counts = Counter(rows.values())
    rate = counts["passed"] / len(plan) if plan else None
    return {"planned": len(plan), "counts": dict(counts), "end_to_end": rate,
            "accepted": bool(plan) and counts["passed"] == len(plan)}

plan = ["normal", "deny", "resume", "unknown_write", "cancel"]
partial = summarize(plan, {"normal": "passed", "deny": "passed", "resume": "passed", "unknown_write": "unknown"})
assert partial["end_to_end"] == 3/5
assert partial["counts"]["not_run"] == 1 and not partial["accepted"]
complete = summarize(plan, {case: "passed" for case in plan})
assert complete["accepted"]  # 仅检查汇总函数，不代表这些实验真的做过。
assert not summarize([], {})["accepted"]
try:
    summarize(plan, {"extra": "passed"})
except ValueError:
    pass
else:
    raise AssertionError("不应悄悄改变验收集")
print("教学部分结果：", partial)
print("全通过夹具的汇总逻辑：", complete)
print("PASS：未知、未运行、空计划、完整夹具与越界样本；非真实项目验收")
```

**预期现象：**部分夹具只算 3/5，unknown 和 not_run 保留；全通过夹具仅用于测试计算函数，不记录为学习验收通过。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 冻结独立保留集和版本，在真实项目上运行，统计所有计划样本并保留失败解释。
2. 现场演示正常、拒绝、恢复和未知四条路径，用工具状态核对文字声明。
3. 让另一位使用者按运行说明复现；逐节回顾仍待验收内容，用户明确确认后再更新学习状态。

## 常见错误

- 把未运行样本从分母删除。
- 课程材料齐全就宣布掌握 Agent 开发。
- 把意图分类基线直接与复杂工单任务成功率相减。

## 思考题

完成基础课件阅读后，怎样证明已经能够独立开发？

<details>
<summary>参考答案（先自行作答）</summary>

能从需求定义契约，独立实现并解释正常与失败路径，定位真实实验问题，处理权限、取消和恢复，并让别人依据说明复现。阅读数量不是这种能力的替代证据。

</details>

## 验收标准

- [ ] 保留集验收有实际终态证据。
- [ ] 成功、失败、未知、未运行分别报告。
- [ ] 运行说明可复现，限制明确，用户确认后才标已验收。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

需求先定义可验收边界，集成后逐层验证，最后用独立样本和他人复现确认交付。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 把“知识库客服助手”定义成可验证的任务边界和场景矩阵，先写成功与禁止条件。 |
| [Session 02](../session_02/README.md) | 沿用户目标串联 Skill、检索、记忆、审批和工具，以一组故障定位集成边界。 |
| [Session 03](../session_03/README.md) | 以预定标准验收最终系统，对照基线交付可复现说明和明确限制。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [评估方法参考](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## 下一节衔接

本节为基础项目阶段验收。接着学习[Session 04](../session_04/README.md)的真实工程集成，最终在 Session 05 做生产验收、Session 06 做总复盘；历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
