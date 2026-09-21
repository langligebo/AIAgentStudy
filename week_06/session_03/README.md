# 第 06 周 Session 03：知识更新、删除与检索评估

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

使已失效或无权访问的资料不再参与回答，并分开评估检索和答案。

## 前置知识与学习安排

文档版本与引用 ID；固定测试样本。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

更新不只是添加新片段，还要让旧版失效；删除应作用于检索索引、缓存和后续上下文。正文删除之后仍缓存旧回答，会让用户看到过时政策。访问范围变化也必须影响缓存键和检索过滤。

本例用 active、version、scope 表示有效性。读取时先选有效且已授权版本，再形成上下文。生产系统更新通常跨存储与索引，需批次版本和切换确认；不能把本例内存赋值称为跨系统原子发布。

Recall@k 关注正确证据是否出现在前 k 个候选中；答案正确率关注最终业务结论。召回提升不保证答案更好。对于本来就无答案的样本，另评估正确拒答，不把它混入有证据样本的召回率分母。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
rows = [
    {"id": "return-v1", "doc": "returns", "v": 1, "active": True, "scope": "public", "days": 7},
    {"id": "vip-v1", "doc": "vip", "v": 1, "active": True, "scope": "vip", "days": 30},
]
cache = {}

def search(doc, scopes):
    return [r for r in rows if r["active"] and r["doc"] == doc and r["scope"] in scopes]

def replace_returns(days):
    version = max(r["v"] for r in rows if r["doc"] == "returns") + 1
    for r in rows:
        if r["doc"] == "returns":
            r["active"] = False
    rows.append({"id": f"return-v{version}", "doc": "returns", "v": version,
                 "active": True, "scope": "public", "days": days})
    cache.clear()

assert search("returns", {"public"})[0]["days"] == 7
cache["old"] = "七天"
replace_returns(10)
hits = search("returns", {"public"})
assert [r["days"] for r in hits] == [10]
assert not cache
assert not search("vip", {"public"})
assert len(search("vip", {"public", "vip"})) == 1
for r in rows:
    if r["doc"] == "returns":
        r["active"] = False
assert search("returns", {"public"}) == []
# 两个有答案样本：都检索命中，但第二个回答有误。
evaluations = [(True, True), (True, False)]
recall = sum(hit for hit, _ in evaluations) / len(evaluations)
accuracy = sum(correct for _, correct in evaluations) / len(evaluations)
assert recall == 1.0 and accuracy == 0.5
print("Recall@1：", recall, "答案正确率：", accuracy)
print("PASS：更新、缓存失效、删除、权限切换和分层评估")
```

**预期现象：**政策由七天变十天，旧版不再出现；删除后无命中；召回 100% 但答案正确率 50%，展示指标差异。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## RAG 补充：RAPTOR、GraphRAG 与架构选择

本节原有版本、删除和 ACL 内容继续保留；复杂索引同样要满足它们。进阶架构不是删除这些基础要求的理由。

| 架构 | 建库/查询方式 | 客服中的候选场景 | 需验证的代价与失败 |
| --- | --- | --- | --- |
| RAPTOR | 对片段表示进行聚类与摘要，递归组织多层摘要树；可从不同层次取证 | 多份长政策的总体规则与跨段主题 | 摘要可能漏例外；正文更新会影响祖先摘要；需回溯原片段 |
| GraphRAG | 利用实体、关系等图结构；Microsoft 实现还用社区报告支持全局查询，局部查询结合实体关系与文本块 | 产品、故障、政策之间的关联，或“所有投诉的共性” | 实体消歧、关系误提取、构建成本、增量更新和图上的权限传播 |
| Agentic RAG | 根据观察决定是否检索、改写、选知识源、补查或停止 | 一次没找到全部退货/赠品依据，需要有预算地补查 | 无限检索、错误改写、越权扩展、模型自称有证据；第九周做运行时实验 |

这是架构原理课，不把任意“摘要树”都叫 RAPTOR，也不把任何数据库有一条关系边就当成 Microsoft GraphRAG 的完整实现。[RAPTOR 原论文](https://arxiv.org/abs/2401.18059)、[GraphRAG 查询模式](https://microsoft.github.io/graphrag/query/overview/)

练习：针对同一组资料，设计三条问题：K1 是否支持蓝牙、K1 的退货例外、全店售后政策有哪些共性。说明哪类问题普通混合检索已足够，哪些可能需要跨片段组织；先收集基础 RAG 失败证据，再决定是否增加架构复杂度。没有实际实验时只给选型假设，不写成胜负结论。

更新和删除实验再增加两个检查：删除某条款后，RAPTOR 祖先摘要是否仍暴露该内容；撤销访问后，GraphRAG 关系或社区摘要是否仍泄露未授权事实。派生索引和摘要也有来源和访问边界，不能只过滤原始片段。

评估准备：为每个问题标注必要源片段、可接受答案和无答案条件。基础 Precision@k、Recall@k 先用人工标签计算；RAGAS 的 Context Precision、Context Recall 与 Faithfulness 在[第十周 Session 01](../../week_10/session_01/README.md)正式区分，[Session 03](../../week_10/session_03/README.md)做组件对照。完整范围见[RAG 知识清单](../RAG_ROADMAP.md)。

<details>
<summary>为什么不把 RAPTOR、GraphRAG、Agentic RAG 排成必须依次升级的等级？</summary>

它们改变的环节不同，适用问题不同。更多模型调用和更复杂索引可能增加错误与维护成本。应根据固定任务上的缺口选择，且可以组合；不是名称更复杂就更先进或更合适。

</details>

补充验收：能画出树、图和检索决策循环的区别；设计原文更新如何传播到派生结构的实验。原理资料已核对，完整框架工程、真实生成摘要/图谱与模型效果未运行；不因读过本节就标工程掌握。

## 实验步骤与练习

1. 增加未完成索引切换的故障，要求返回可解释的版本状态。
2. 切换用户权限后重复查询，检查缓存不会跨用户复用私有正文。
3. 对本周知识库列出有答案、无答案、版本冲突、越权四类开发样本，再冻结保留集。

## 常见错误

- 更新只添加新文档，不停用旧片段。
- 使用只含 query 的全局缓存键。
- 把检索分数提升当作客服任务完成。

## 思考题

删除资料后，上一轮对话历史里还保留旧片段，怎么办？

<details>
<summary>参考答案（先自行作答）</summary>

后续组装上下文时检查证据 ID 与版本的有效性，去掉失效正文或标明过期，并重新检索；仅删除索引并不能清除已经进入历史或缓存的副本。

</details>

## 验收标准

- [ ] 更新后只引用新版本，删除后不再命中。
- [ ] 权限切换影响候选、缓存和上下文。
- [ ] 检索与回答两个指标独立记录。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

分块和索引负责让证据可找到，回答负责忠于证据，生命周期管理保证证据仍有效且有权限。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 建立保留来源、版本、时间和访问范围的最小知识索引，理解分块与 Embedding 各自的作用。 |
| [Session 02](../session_02/README.md) | 分别检查检索结果和答案，使每个结论可追溯到实际片段。 |
| [Session 03](../session_03/README.md) | 使已失效或无权访问的资料不再参与回答，并分开评估检索和答案。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Python math：向量演示使用的数值运算](https://docs.python.org/3.12/library/math.html)

## 下一节衔接

本节完成本模块前三节的阶段复盘，接着学习新增的[Session 04](../session_04/README.md)；原下一模块安排顺延，历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
