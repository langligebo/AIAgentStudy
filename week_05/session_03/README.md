# 第 05 周 Session 03：Skill 评估、版本与回退

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

用相同案例比较无 Skill、旧版和新版，发现误触发、漏触发及流程退化。

## 前置知识与学习安排

Skill 激活记录；第 2 周开发集与保留集。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

触发评估与任务评估不同：选对 Skill 仍可能执行失败。先人工给请求标注是否该使用售后 Skill，再看 TP、FP、FN；精确率反映被触发的请求中有多少合适，召回率反映适用请求是否被漏掉。没有预测正例时精确率应为不可计算，而不是 100%。

一次更新应固定 Skill 内容版本、引用政策版本、依赖和样本集。Skill 更新也可能变坏：新版本扩大触发范围，把购买前咨询错误地送入售后流程。回退应同时恢复正文、引用和依赖约定，不能仅改名称。

以下用三套确定性选择规则代替模型，演示评估与发布门槛。正式评估还要跑相同工具执行器、检查终态和安全负例；不要从这个夹具推出新版 Skill 普遍更优。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
CASES = [("我要退货", True), ("换货怎么办", True), ("这款有蓝牙吗", False), ("你好", False)]
VERSIONS = {
    "none": lambda text: False,
    "v1": lambda text: "退货" in text,
    "v2": lambda text: "货" in text or "蓝牙" in text,  # 增加召回但误触发
}

def score(select):
    tp = fp = fn = 0
    for text, expected in CASES:
        predicted = select(text)
        tp += bool(predicted and expected)
        fp += bool(predicted and not expected)
        fn += bool(not predicted and expected)
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None}

reports = {version: score(select) for version, select in VERSIONS.items()}
for version, report in reports.items():
    print(version, report)
assert reports["none"]["precision"] is None
assert reports["v1"]["fn"] == 1
assert reports["v2"]["fp"] == 1
# 教学门槛：不允许比当前版增加误触发。
current = "v1"
candidate = "v2"
if reports[candidate]["fp"] <= reports[current]["fp"]:
    current = candidate
assert current == "v1"
manifest = {"skill": current, "policy": "policy-v1", "executor": "executor-v1"}
print("保留/回退到", manifest)
print("PASS：空分母、漏触发、误触发与发布拒绝")
```

**预期现象：**v1 漏掉换货，v2 命中两项但误触发蓝牙咨询，门槛拒绝 v2；无 Skill 的精确率是 None。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 新增“买之前能否退货”的边界样本，先讨论应属于政策咨询还是售后，固定标签后再评估。
2. 把选择正确但创建失败加入终态指标，不把触发率当成功率。
3. 写一个版本清单并演练从新版回到旧版；实验统计只在终端输出，版本清单属于配置可以保存。

## 常见错误

- 只测应该触发的正例。
- 更换样本集后直接声称新版本更好。
- 回退正文却继续读取新版政策。

## 思考题

新版本召回率更高，但误触发写操作，是否应发布？

<details>
<summary>参考答案（先自行作答）</summary>

按预先设定的安全与任务门槛判断。不能用平均质量收益抵消未经授权的写操作；修复触发边界并重复同组开发样本，最终再独立验收。

</details>

## 验收标准

- [ ] 能手算精确率和召回率，解释零分母。
- [ ] 同案例比较三个版本，保留负例。
- [ ] 正文、依赖与引用版本能够一起回退。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

编写文件只是起点；发现、激活、正文加载和执行必须接通，再用负例与版本回归证明改动效果。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 编写描述适用范围、步骤和失败分支的 Skill，并区分说明文件、辅助资料和执行工具。 |
| [Session 02](../session_02/README.md) | 先提供元数据供选择，再读取被选 Skill 正文和必要资料，记录加载过程。 |
| [Session 03](../session_03/README.md) | 用相同案例比较无 Skill、旧版和新版，发现误触发、漏触发及流程退化。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 Skills 为文件协议，无 Python SDK 依赖；按核对日的官方规范编写，教学检查不是完整规范验证器。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Agent Skills 文件规范](https://agentskills.io/specification)
- [宿主如何接入 Skills](https://agentskills.io/client-implementation/adding-skills-support)

## 下一节衔接

本节完成本模块前三节的阶段复盘，接着学习新增的[Session 04](../session_04/README.md)；原下一模块安排顺延，历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
