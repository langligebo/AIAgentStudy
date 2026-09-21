# 第 06 周 Session 02：检索排序、证据引用与无答案

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

分别检查检索结果和答案，使每个结论可追溯到实际片段。

## 前置知识与学习安排

上一节片段元数据与相似度。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

关键词检索擅长精确编号与术语，向量检索常用于语义近似。二者的分数尺度不同，混合时应经过排序策略或验证，而不是随意相加。重排阶段只处理已授权候选，不应用它补救已经泄露的正文。

检索器返回候选，回答器组织结论，引用验证器检查来源 ID 是否存在于本轮证据。引用存在只是必要条件，还要人工或程序判断结论是否受原文支持。相似段落若没有回答问题，应明确缺资料。

本例使用词项覆盖率排序及直接摘取证据，故意不让语言模型补全；便于验证“找到什么”与“说了什么”。真实生成时将授权片段作为有来源的资料输入公共客户端，并保留 no_answer 分支。外部正文是数据，不可把其中命令升格为系统指令。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
DOCS = [
    {"id": "p1", "terms": {"键盘", "退货"}, "text": "键盘签收七天内可申请退货。"},
    {"id": "p2", "terms": {"键盘", "蓝牙"}, "text": "K1 键盘支持蓝牙连接。"},
]

def retrieve(terms):
    if not terms:
        return []
    scored = [(len(terms & d["terms"]) / len(terms), d) for d in DOCS]
    return [d for score,d in sorted(scored, key=lambda x: -x[0]) if score == 1.0]

def answer(terms):
    evidence = retrieve(terms)
    if not evidence:
        return {"status": "no_answer", "text": "现有资料不足，请补充产品或政策。", "citations": []}, evidence
    first = evidence[0]
    return {"status": "answered", "text": first["text"], "citations": [first["id"]]}, evidence

def validate(result, evidence):
    by_id = {d["id"]: d["text"] for d in evidence}
    if result["status"] == "no_answer":
        return not result["citations"]
    # 本例采用原文摘录，因此可以做严格相等校验；自由生成不能直接套用。
    return (bool(result["citations"]) and all(c in by_id for c in result["citations"])
            and result["text"] in [by_id[c] for c in result["citations"]])

normal, evidence = answer({"键盘", "退货"})
missing, empty = answer({"发票"})
assert validate(normal, evidence)
assert validate(missing, empty)
assert missing["status"] == "no_answer"
assert not validate({**normal, "citations": ["invented"]}, evidence)
assert not validate({**normal, "text": "任何时间都能退货"}, evidence)
print("检索：", evidence)
print("回答：", normal)
print("缺资料：", missing)
print("PASS：正常引用、无答案、伪造来源、错误结论")
```

**预期现象：**先打印证据再打印引用回答；发票返回 no_answer；伪造引用与有引用但结论错误都不能通过。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## RAG 补充：混合检索、查询变换与 Reranking

原来的词项覆盖率示例只教检索与引用协议，不能替代 BM25、向量检索和重排实验。本节按“召回→融合→重排→证据组装”补齐，方法定位见[RAG 知识清单](../RAG_ROADMAP.md)。

### BM25＋向量召回＋RRF

BM25 基于词项匹配，考虑词频、文档频率与长度；对精确型号、订单号和政策名很重要。向量召回补充语义相近但用词不同的候选。中文分词质量要单独检查，不能把不含空格的整段中文当一个词。

RRF 用名次而非直接相加的原始分数融合：`score(d) = Σ 1 / (k + rank(d))`，名次从 1 开始；未命中的分支不贡献分数。`k` 是平滑常数，不是候选数量。各分支保持同样的身份和版本过滤，融合后去重，再送少量候选给重排。[RRF 官方说明](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)

下面实现一个正 IDF 形式的 BM25 教学评分和 RRF。中文 Token 手工给定；向量名次和相关性标签都是固定夹具，不是实测嵌入或 Cross-encoder。

```python
# course: offline
from collections import Counter, defaultdict
from math import log

DOCS = {"return": ["K1", "退货", "七天", "未使用"],
        "gift": ["K1", "赠品", "退货", "完整"],
        "bluetooth": ["K1", "蓝牙", "连接"]}

def bm25(query):
    n = len(DOCS)
    avgdl = sum(map(len, DOCS.values())) / n
    scores = {}
    for doc_id, terms in DOCS.items():
        tf, total = Counter(terms), 0.0
        for term in set(query):
            df = sum(term in values for values in DOCS.values())
            idf = log(1 + (n-df+0.5)/(df+0.5))
            frequency = tf[term]
            total += idf * frequency * 2.2 / (frequency + 1.2*(0.25 + 0.75*len(terms)/avgdl))
        scores[doc_id] = total
    return sorted((doc_id for doc_id in scores if scores[doc_id] > 0), key=lambda d: (-scores[d], d))

def rrf(rankings, k=60):
    scores = defaultdict(float)
    for ranking in rankings:
        unique = list(dict.fromkeys(ranking))
        for rank, doc_id in enumerate(unique, 1):
            scores[doc_id] += 1/(k+rank)
    return sorted(scores, key=lambda d: (-scores[d], d))

lexical = bm25(["退货"])
vector_fixture = ["bluetooth", "gift", "return"]  # 故意包含语义召回噪声。
fused = rrf([lexical, vector_fixture])
assert set(lexical) == {"return", "gift"}
assert bm25(["发票"]) == []
assert rrf([[], []]) == []
assert rrf([["gift", "gift"], ["return"]]) == rrf([["gift"], ["return"]])
# 人工相关性夹具，仅检查重排接口：问题聚焦“赠品退货”。
relevance = {"gift": 2, "return": 1, "bluetooth": 0}
reranked = sorted(fused, key=lambda d: (-relevance[d], d))
assert reranked[0] == "gift"
assert "missing_policy" not in reranked  # 重排不能凭空补回未召回的证据。
print("BM25", lexical, "RRF", fused, "人工重排夹具", reranked)
print("PASS：BM25、融合去重、空召回、重排和候选缺失边界")
```

### 查询变换不要混成一种技术

| 方法 | 输入→中间结果→检索 | 客服练习 | 边界 |
| --- | --- | --- | --- |
| HyDE | 问题→假设文档→文档向量→真实证据 | 根据“开封是否可退”生成检索用说明 | 假设内容可能错误，不能引用它；真实证据不足仍拒答 |
| Multi-Query | 原问题→同意图的多种问法→多次召回去重 | “退货赠品”“退回商品附赠品处理” | 保留原查询，限制数量；扩展漂移不能绕过用户条件 |
| 查询分解 | 复合问题→多个必要子问题→汇合证据 | 退货资格、赠品处理、运费分别查 | 某子问题无证据不能用其他问题的证据填空 |
| Step-Back | 具体问题→较抽象的问题→原则证据→回到原问 | 先找拆封退货资格规则，再核对 K1 例外 | 抽象会丢精确型号，须保留原问题和限制 |

[HyDE 论文](https://aclanthology.org/2023.acl-long.99/)与[Step-Back 论文](https://arxiv.org/abs/2310.06117/)描述的是不同机制。实际查询改写/生成复用公共 LLM 客户端；Embedding 另需经过验证的嵌入能力，本次不新增适配器或调用模型。

对照步骤：固定一组问题和证据标签，先单查询基线，再分别启用一种变换；记录 unique chunks、证据覆盖、查询次数和延迟。先用人工写好的问法检验合并逻辑，之后才换真实模型生成，并记录生成失败与漂移。不要同时开四项再推断谁有效。

### Cross-encoder 重排与模型选择

第一阶段取较大 `candidate_k`，Cross-encoder 将 query 和每个候选正文一起输入评分，取较小 `rerank_k/context_k` 给回答器。重排可以清理噪声，不能召回候选集合外的条款。[官方检索与重排说明](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)

BGE Reranker 和 Cohere Rerank 是可研究的实现例子，不是两种必须同时安装的组件。真正选型时记录版本、输入限制、中文效果、调用方式、延迟以及资料能否发送到该服务。上方人工标签排序不是二者的模型实现，真实重排实验未运行。

<details>
<summary>HyDE 写出了“30 天可退”，真实文档却只有“7 天”，回答应依据哪个？</summary>

依据当前有效、已授权的真实文档，并保留其中例外条件。HyDE 内容只是检索中间表示，不能与原文争夺事实权威；若错误假设带来偏题候选，应回到原查询并记录检索失败。

</details>

补充验收：解释 BM25/向量互补、RRF 与 Cross-encoder 的区别；比较一种查询变换的收益和成本；测试空召回、错型号和遗漏例外。依赖仍为 Python 3.12 标准库，SDK 与真实模型未验证。

## 实验步骤与练习

1. 把关键词表中的产品改为鼠标，检查是否错误引用键盘政策。
2. 给一个相似但未回答“退款到账多久”的片段，要求回答器拒绝推断具体天数。
3. 接真实模型时使用 client.chat，发送本轮证据 ID 与正文，只打印回答与校验结果；不要把本例词项规则说成真实模型效果。

## 常见错误

- 有引用就认为答案正确。
- 无命中时让模型根据常识编政策。
- 只看最终答案，不保留本轮候选观察。

## 思考题

检索器找到了正确片段，但回答把七天写成三十天，应该优化哪里？

<details>
<summary>参考答案（先自行作答）</summary>

这是生成或答案验证阶段的问题。先保留正确检索证据，修正回答约束、引用校验与验收；盲目扩大检索量可能掩盖而非解决错误。

</details>

## 验收标准

- [ ] 能分别指出检索失败和答案错误。
- [ ] 引用均来自本轮有效证据。
- [ ] 资料不足时明确 no_answer。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Python math：向量演示使用的数值运算](https://docs.python.org/3.12/library/math.html)

## 下一节衔接

下一节测试版本更新、删除和权限切换后旧证据是否真正失效。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
