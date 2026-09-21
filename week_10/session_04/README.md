# 第 10 模块 Session 04：数据集设计、统计不确定性与评分器偏差

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

避免用少量挑选样本宣布改进，能设计可重复、分层且不泄漏的评价。

## 前置知识与学习安排

第十模块前三节与基础概率/平均数。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

数据集需要任务分布、难例、无答案、安全负例、工具失败和多轮更正。相同用户/文档/模板的近重复样本应按组划分，避免训练/开发信息泄露到保留集。合成样本要人工抽查真实性和标签，不能以数量替代覆盖；线上失败应脱敏后进入新回归集。

区分每任务至少一次成功的 pass@k 与多次都成功的可靠性；增加尝试次数会提高机会，也增加成本。保留每任务与重复轮次，按问题配对比较。对同一会话的多轮输出不能假设完全独立，应按会话/任务重采样。

置信区间表达有限样本下的不确定性，不是未来成功保证。下面实现 Wilson 二项比例区间；仅适合相应抽样假设下的二元成功率。真实比较可按任务做 paired bootstrap，观察均值、分层差异与安全退化，不能只看总平均。

LLM-as-judge 要固定 rubric，打乱候选顺序，隐藏模型名称，检查位置、长度、自我偏好和提示注入偏差。用双人标注/仲裁校准困难样本，报告误接受/误拒绝，安全与写入终态用可检查事实而非主观分数。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
from math import sqrt

def wilson(success, total, z=1.96):
    if total <= 0 or not 0 <= success <= total: raise ValueError("counts")
    p = success/total; d = 1 + z*z/total
    center = (p + z*z/(2*total))/d
    half = z*sqrt(p*(1-p)/total + z*z/(4*total*total))/d
    return center-half, center+half

assert wilson(3,3)[0] < 0.5
assert wilson(300,300)[0] > 0.98
assert wilson(0,3)[1] > 0.5
try: wilson(0,0)
except ValueError: pass
else: raise AssertionError("empty accepted")

def assert_no_leak(dev, test):
    if {x["group"] for x in dev} & {x["group"] for x in test}: raise ValueError("group_leak")
assert_no_leak([{"group":"doc-a"}],[{"group":"doc-b"}])
try: assert_no_leak([{"group":"doc-a"}],[{"group":"doc-a"}])
except ValueError: pass
else: raise AssertionError("leak")
print("PASS：小样本区间、空分母拒绝和组隔离", wilson(3,3))
```

**预期现象：**3/3 的区间仍很宽；同文档组泄漏与零分母被拒绝。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 用已有任务构造分层表，每层有目标、样本来源与标注准则。
2. 对同一组任务各重复 3 次，分别算单次成功、至少一次成功和全通过比例，注明不是独立任务数。
3. 交换评分候选顺序并混入冗长但错误答案，测 judge 偏差及与人工标签一致性。
4. 对配对任务差值做 bootstrap，以任务为抽样单位，展示区间和退化清单；本例不替代这一步。

## 常见错误

- 用 3/3 宣称稳定正确。
- 同模板换几个词就当独立泛化集。
- 为了让版本胜出事后改变权重或删除失败。

## 思考题

新版本总体更好，但越权负例更差，可以直接发布吗？

<details>
<summary>参考答案（先自行作答）</summary>

不应把高风险退化淹没在平均值中。按预设硬门槛检查，并修复/复测受影响范围。

</details>

## 验收标准

- [ ] 能按数据来源分组并检查泄漏。
- [ ] 能解释样本量、重复与区间的限制。
- [ ] 模型评分的误接受有人工或事实对照。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Agent 评估设计](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Wilson 区间原论文](https://doi.org/10.1080/01621459.1927.10502953)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../session_05/README.md)
