# 第 13 模块 Session 06：模型适配、训练路线与课程总复盘

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

能判断何时使用 Prompt、RAG、工具、Skill 或训练，并把后续专项学习建立在现有证据上。

## 前置知识与学习安排

模型机制、数据集划分、评估及综合项目。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

系统性 Agent 工程需要理解训练边界，不要求先从零训练大模型。知识更新通常先考虑 RAG；外部计算/动作使用工具；可复用流程用 Skill；稳定风格或任务模式在数据充足、基线明确时才考虑 SFT。微调不能自动获得实时知识、执行权限或可靠状态。

SFT 学习监督样本；LoRA/QLoRA 是减少可训练参数/资源的技术路线，不是新任务目标；DPO 使用偏好对，强化学习优化奖励信号。可验证奖励适合有检查器的任务，但检查器错误、数据污染和 reward hacking 会导致错误优化。蒸馏从强模型或策略构造训练信号，同样要校验质量与许可/隐私范围。

训练计划要写清基础模型、数据来源、去重与组隔离、标签、训练/验证/保留集、资源预算、checkpoint 和停止门槛。先看无训练基线，再同条件比较质量、工具行为、安全、遗忘、延迟与成本。离线数据分数提高不自动代表真实 Agent 任务改善。

下例只检查训练数据边界与选择逻辑，不安装训练栈或运行训练。完整 SFT/LoRA、DPO/RL、分布式训练、实时语音、浏览器规模化和生产 GraphRAG 是明确的专项工程，不在本主线声称全部实现。核心要求是知道何时需要、前置条件、实验设计和风险，并有清晰继续路径。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
def choose(problem):
    return {"fresh_knowledge":"rag", "external_action":"tool", "repeatable_procedure":"skill",
            "stable_style_with_data":"consider_sft"}.get(problem,"diagnose_first")

def validate_split(train, test):
    if not train or not test: raise ValueError("empty_split")
    if {x["source_group"] for x in train} & {x["source_group"] for x in test}: raise ValueError("leak")
    for row in train+test:
        if not row["approved"] or not row["input"] or not row["target"]: raise ValueError("bad_data")
    return True

train=[{"source_group":"g1","approved":True,"input":"退货条件","target":"查询政策"}]
test=[{"source_group":"g2","approved":True,"input":"K1 用过能退吗","target":"查拆封例外"}]
assert validate_split(train,test)
assert choose("external_action")=="tool"
assert choose("fresh_knowledge")=="rag"
try: validate_split(train,[{**test[0],"source_group":"g1"}])
except ValueError: pass
else: raise AssertionError("leak")
try: validate_split(train,[{**test[0],"approved":False}])
except ValueError: pass
else: raise AssertionError("unapproved_data")
print("PASS：适配方向与数据边界；没有训练或模型效果结论")
```

**预期现象：**新知识与外部动作不会默认走训练；数据跨组泄漏和未批准来源被拒绝。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 从项目真实失败中选一类，判断是检索、提示、执行器、记忆还是模型行为问题。
2. 写无训练基线与 SFT/LoRA 候选的比较设计，只有确认需要才进入专项训练。
3. 为偏好/奖励样本写规则，加入格式投机、错误工具、数据泄漏和遗忘回归。
4. 按覆盖矩阵逐项自查：能解释、能实现机制、能完成真实实验、能集成分别标记；任何尚无证据项继续保留。
5. 选择下一阶段专项时建立新的目标和验收，不用“课程全部结束”掩盖历史待办。

## 常见错误

- 用微调修复错误授权或过期索引。
- 把模型生成训练数据全部当正确标签。
- 只报告训练 loss，不报告独立任务指标。

## 思考题

客服模型总是生成漂亮但过期的政策，首先微调吗？

<details>
<summary>参考答案（先自行作答）</summary>

先检查知识来源、检索版本与引用约束。若事实来自过期索引，训练未必解决更新与追溯问题；先修数据路径并建立基线。

</details>

## 验收标准

- [ ] 能比较 Prompt/RAG/Tool/Skill/Memory/训练的适用边界。
- [ ] 训练方向有数据、预算、基线和退化检查。
- [ ] 完整主线各项状态由实际证据核对，未知不勾选。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [LoRA 原论文](https://arxiv.org/abs/2106.09685)
- [DPO 原论文](https://arxiv.org/abs/2305.18290)
- [Hugging Face PEFT](https://huggingface.co/docs/peft/index)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_05/README.md)
