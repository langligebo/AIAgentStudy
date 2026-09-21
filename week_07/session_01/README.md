# 第 07 周 Session 01：上下文选择与预算

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_06/session_07/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

在有限预算内保留目标、约束和必要证据，并解释裁剪策略的损失。

## 前置知识与学习安排

第 4 周任务状态、第 6 周授权证据。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

模型每轮看到的信息由应用组装，通常包含系统约束、任务状态、激活 Skill、工具说明、当前证据和历史。历史最长不等于效果最好；重复工具大响应会挤掉订单号或用户更正。

优先保留不可丢的规则和任务事实，再放支持本轮动作的证据，最后按相关性或时间取历史。给输出预留预算；实际 Token 应使用对应模型的 tokenizer 或服务统计。下面用 UTF-8 字节数作为保守教学单位，不声称它等于 Token，也不据此设置 num_ctx。

工具摘要至少保留状态、证据 ID、关键事实、截断标记；不要把一万条结果压缩成“均正常”。如果必需信息已超过预算，应停止、询问或拆任务，而不是静默丢掉授权限制。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import json

MANDATORY = ["规则：写工单前核验审批。", "目标：处理 A100 退货；用户要求先给方案。"]
EVIDENCE = ["证据 p1/v2：键盘签收十天内可申请。"]
HISTORY = ["用户曾询问蓝牙。", "用户说谢谢。", "订单 A100 已签收两天。"]

def cost(text):
    return len(text.encode("utf-8"))

def compose(budget):
    parts = list(MANDATORY)
    used = sum(map(cost, parts))
    if used > budget:
        raise ValueError("mandatory_context_over_budget")
    selected = []
    for source, text in [("evidence", t) for t in EVIDENCE] + [("history", t) for t in reversed(HISTORY)]:
        if used + cost(text) <= budget:
            parts.append(text)
            selected.append(source)
            used += cost(text)
    return {"parts": parts, "used_bytes": used, "selected": selected,
            "omitted": len(EVIDENCE) + len(HISTORY) - len(selected)}

budget = sum(map(cost, MANDATORY + EVIDENCE))
context = compose(budget)
assert context["parts"][:2] == MANDATORY
assert context["selected"] == ["evidence"]
assert context["omitted"] == 3
try:
    compose(1)
except ValueError as exc:
    assert str(exc) == "mandatory_context_over_budget"
else:
    raise AssertionError("不应丢掉必需上下文后继续")
summary = {"status": "partial", "source": "orders-page1", "count": 20, "has_more": True}
assert summary["status"] == "partial" and summary["has_more"]
print(json.dumps(context, ensure_ascii=False))
print(summary)
print("PASS：保留约束、裁剪历史、必需预算不足、工具摘要保留截断")
```

**预期现象：**有限预算保留规则、目标和政策证据，三条历史被省略；预算过小抛出明确错误。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## RAG 补充：证据压缩与文档重排列

本节将第六周的候选结果变成回答所需的上下文，完整衔接见[RAG 知识清单](../../week_06/RAG_ROADMAP.md)。先进行权限/版本过滤和候选去重，再考虑压缩和位置，不靠压缩器修复已经泄露的正文。

### 压缩保留什么

抽取式压缩选择原文中相关句子；生成式压缩重写摘要，可能引入错误或删掉限制。两者都要保留 `source_id/version` 和可回到原文的位置。模型生成的摘要不是新的政策权威。

例如原文：“K1 签收七天内可申请；已使用不适用；赠品须完整寄回。”用户问拆封和赠品时，压成“七天内可退”虽然短，却漏掉关键条件。正常场景是保留资格、例外和赠品要求；失败场景是删掉“已使用不适用”或把否定变肯定。

实验顺序：

1. 固定候选块及顺序，用原文回答作为基线。
2. 先只删除重复和明显无关句，再测上下文占用及答案遗漏。
3. 尝试抽取或摘要，逐条核对时间、金额、否定、例外和适用对象；压缩输出保留引用映射。
4. 空压缩结果按无证据处理；不能让模型因为无上下文就凭常识编政策。

“FAQ 场景不需要压缩”不是通用规则。短小且精确命中的单条 FAQ 可以先不压缩；多条冗余或长 FAQ 仍可能超预算。是否启用要用缺失条件、耗时和质量对照决定。

### Lost-in-the-Middle 与位置实验

文档重排列调整同一批证据在上下文中的位置；它与 Cross-encoder 按相关性评分的 reranking 不同。已有研究发现某些长上下文设置对中间位置证据利用较弱，但不是所有模型、任务都一样，也不能保证移到两端必然改善。[Lost in the Middle 原论文](https://aclanthology.org/2024.tacl-1.9/)

用同一组块分别把关键例外放在开头、中间、结尾，保持问题、模型、参数、证据集合和总预算一致，重复评估是否引用并遵守该例外。改变位置时不要同时改变块数和压缩方式，否则无法归因。排序实验不能掩盖检索阶段根本没拿到证据的问题。

<details>
<summary>模型能看到整个窗口，为什么还要测证据位置？</summary>

能接收某长度输入不等于在所有位置上同样可靠地使用证据。要用当前模型与真实任务验证，不能把上下文容量当作均匀的信息利用能力。

</details>

补充验收：压缩保留否定/例外与来源；区分压缩、相关性重排和位置重排；能做仅改变位置的对照。本次只补方法、完整输入例和实验步骤，没有运行压缩模型或位置效果实验。无需为此提前增加依赖。

## 实验步骤与练习

1. 与只保留 HISTORY 最后两条比较，指出哪种策略丢了“先给方案”的约束。
2. 将订单签收时间提升为本轮必需事实，观察预算不足时是否明确退出。
3. 真实模型实验固定问题和输出预算，对比两种上下文策略并检查回答所依赖的证据，不比较字符长度就下结论。

## 常见错误

- 把字符数直接当 Token 数。
- 裁剪先删 system 或最近用户更正。
- 摘要丢掉 partial 标记却说查询完整。

## 思考题

为什么“只保留最新 N 条消息”可能保留了错误订单号？

<details>
<summary>参考答案（先自行作答）</summary>

任务更正和事实更新未必在最后 N 条内。应从有版本的任务状态提取当前订单与约束，而不是依靠消息位置隐含表示最新事实。

</details>

## 验收标准

- [ ] 预算内保留目标与限制。
- [ ] 能说明被省略的信息及影响。
- [ ] Token 估算与真实计量分开。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [上下文工程](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Python SQLite](https://docs.python.org/3.12/library/sqlite3.html)

## 下一节衔接

下一节把需要跨会话保留的偏好存储为有来源和作用域的记忆。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_06/session_07/README.md) · [下一节](../session_02/README.md)
