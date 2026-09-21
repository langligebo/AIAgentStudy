# 第 01 模块 Session 05：模型机制、采样与能力边界

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

建立 tokenizer、注意力、自回归、训练、推理和资源之间的因果关系。

## 前置知识与学习安排

第一周采样实验与模型/服务/客户端区别。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

文本先按 tokenizer 变成 token ID，经 embedding 和位置表示进入网络。注意力根据输入中位置之间的关系组合表示；自回归生成通常预测下一个 token，重复直到停止。上下文容量表示可处理的输入范围，不是知识真实性或长期记忆保证。检索向量与生成模型内部 token embedding 也不是可直接混用的接口。

预训练学习语言和统计规律；指令微调、偏好优化改变任务行为；推理时的 Prompt、检索与工具并不更新权重。推理模型可能使用额外计算，应该比较最终可验证结果、预算和延迟，不把要求输出隐含思维链作为可靠性手段。

采样对 logits 做温度缩放，再按指定策略选择候选。Top-k 与 Top-p 是不同筛选方法，服务的执行顺序、seed 与硬件影响重现。下例只演算分布，不模拟 Transformer；模型参数量、权重量化、KV cache、输入长度、batch 和并发一起影响内存。不要把模型文件大小当作运行峰值内存。

学习时画“输入→tokenizer→网络→logits→采样→输出”图，再区分冷启动、prefill 与 decode。量化是数值表示取舍；幻觉、知识过期、歧义和分布变化需要不同检测方法。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
from math import exp, isclose

def distribution(logits, temperature):
    if not logits or temperature < 0: raise ValueError("invalid")
    if temperature == 0:
        best = max(range(len(logits)), key=lambda i: logits[i])
        return [float(i == best) for i in range(len(logits))]
    scaled = [x / temperature for x in logits]
    weights = [exp(x - max(scaled)) for x in scaled]
    return [w / sum(weights) for w in weights]

def nucleus(probs, p):
    if not 0 < p <= 1: raise ValueError("top_p")
    chosen, total = [], 0.0
    for i in sorted(range(len(probs)), key=lambda i: probs[i], reverse=True):
        chosen.append(i); total += probs[i]
        if total >= p: break
    return chosen

cold, warm = distribution([3, 2, 0], 0.5), distribution([3, 2, 0], 1)
assert cold[0] > warm[0] and isclose(sum(warm), 1)
assert distribution([3, 2, 0], 0) == [1, 0, 0]
assert nucleus(warm, 0.5) == [0]
try: nucleus(warm, 0)
except ValueError: pass
else: raise AssertionError("invalid top_p accepted")
print("PASS：演算采样分布；不代表真实模型确定性", cold, warm)
```

**预期现象：**低温分布更集中，非法 Top-p 被拒绝；没有运行模型。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 手算最高分 token 的概率并与程序比较。
2. 保持 logits 不变，分别改变温度、Top-p；描述改变发生在哪一层。
3. 对已有 Ollama 实验记录模型版本、量化、输入输出 token、首字时间与总时间；未提供的值标未知。
4. 解释为什么增大上下文、模型参数或思考预算不能保证答案正确。

## 常见错误

- 把字符当 token。
- 把语言概率当事实概率。
- 把 temperature=0 的教学 argmax 当跨设备确定性承诺。

## 思考题

为什么更大的上下文不能代替检索评估？

<details>
<summary>参考答案（先自行作答）</summary>

能接收输入不代表能找到正确证据或可靠利用所有位置；还要测相关性、权限、冲突与回答忠实度。

</details>

## 验收标准

- [ ] 能画出推理数据流并说明不是训练过程。
- [ ] 能解释采样、检索、微调各改变什么。
- [ ] 能列出影响质量与运行资源的变量并设计单变量比较。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Transformer 原论文](https://arxiv.org/abs/1706.03762)
- [Ollama 参数](https://docs.ollama.com/modelfile)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_04/README.md) · [下一节](../../week_02/session_01/README.md)
