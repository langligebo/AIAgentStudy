# 第 09 周 Session 03：结果验证与有限修正

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

用业务状态定义成功，比较固定与动态策略的收益，并给修复循环设置终点。

## 前置知识与学习安排

计划、工具结果、端到端成功率与固定样本。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

检查器应判断订单、引用、审批与工单终态，而非“回答听起来有帮助”。修复器根据明确错误行动，例如缺政策可再次检索，订单越权则停止，未知写入则核对。不是所有失败都应修复。

先设定同一任务集和成功标准，再比较 Workflow 与规划器。指标包括成功率、工具与模型调用数、延迟、未知结果和安全失败。任务简单时固定流程常更经济，复杂变更时动态规划可能有用；结论必须来自实际实验。

示例用固定夹具模拟两种策略。repair 函数只补充一次缺失证据，不执行任何新写入。所有返回 success 的结果均由状态检查支撑。打印出来的模拟差异只用于学会读表，不是两种架构的真实胜负。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from time import perf_counter

CASES = [{"id": "normal", "ticket": "T1"}, {"id": "missing_evidence", "ticket": "T2"},
         {"id": "phantom", "ticket": "T3"}]
DB = {"T1": {"order": "A100"}, "T2": {"order": "A100"}}

def verify(result):
    row = DB.get(result.get("ticket"))
    return bool(row and row["order"] == "A100" and result.get("policy") == "p1")

def run(case, strategy, max_repairs=1):
    start = perf_counter()
    result = {"ticket": case["ticket"], "policy": "p1" if case["id"] != "missing_evidence" else None}
    calls, repairs = 1, 0
    while not verify(result) and repairs < max_repairs:
        if strategy != "adaptive" or result["ticket"] not in DB:
            break
        result["policy"] = "p1"  # 模拟重新检索到证据，不创建工单。
        repairs += 1
        calls += 1
    return {"success": verify(result), "calls": calls, "repairs": repairs,
            "elapsed": perf_counter() - start}

for strategy in ("fixed", "adaptive"):
    results = [run(case, strategy) for case in CASES]
    print(strategy, "成功", sum(r["success"] for r in results), "/", len(CASES),
          "调用", sum(r["calls"] for r in results), "模拟耗时", sum(r["elapsed"] for r in results))
assert run(CASES[0], "fixed")["success"]
assert run(CASES[1], "adaptive")["success"]
assert not run(CASES[1], "adaptive", max_repairs=0)["success"]
assert not run(CASES[2], "adaptive")["success"]
assert run(CASES[2], "adaptive")["repairs"] == 0
print("PASS：有证据成功、有限修复、预算耗尽、无工单不能假完成")
```

**预期现象：**夹具中 fixed 成功 1/3，adaptive 2/3，后者多一次检索；虚构工单永远不过验收。实际耗时无模型或网络意义。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 把正确工单的订单号改错，检查器必须拒绝。
2. 把缺政策修复设为持续失败，确认达到次数上限后不再循环。
3. 用相同开发集替换夹具，固定模型和工具条件，再比较两种真实实现；保留未知和失败样本。

## 常见错误

- 用模型自评分替代业务状态。
- 只看成功率不看额外调用和等待。
- 为通过验收不断改变标准。

## 思考题

修复次数已耗尽，但模型仍说“再尝试一下”，怎么办？

<details>
<summary>参考答案（先自行作答）</summary>

运行时停止并报告已经核验的事实、缺口和可选后续动作；是否继续由用户或可信策略重新授权，不由模型解除预算。

</details>

## 验收标准

- [ ] 同样输入和标准比较两个策略。
- [ ] 修复有针对性且有上限。
- [ ] 无法验证时保留未完成状态。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

固定流程与动态规划都是手段；依赖、预算、用户更正和终态验证决定它们是否适合当前任务。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 为明确业务流程选择串行、条件路由或独立并行，并用事件证明依赖顺序。 |
| [Session 02](../session_02/README.md) | 校验模型提出的计划，在观察或目标变化后废止过期步骤，并限制重新规划成本。 |
| [Session 03](../session_03/README.md) | 用业务状态定义成功，比较固定与动态策略的收益，并给修复循环设置终点。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Python asyncio 任务与并发](https://docs.python.org/3.12/library/asyncio-task.html)

## 下一节衔接

本节完成本模块前三节的阶段复盘，接着学习新增的[Session 04](../session_04/README.md)；原下一模块安排顺延，历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
