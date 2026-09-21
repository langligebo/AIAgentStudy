# 第 06 周 Session 01：文档解析、分块与索引

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_05/session_04/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

建立保留来源、版本、时间和访问范围的最小知识索引，理解分块与 Embedding 各自的作用。

## 前置知识与学习安排

字典、列表、Skill 的 references；理解政策是外部证据。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

入库过程是解析文档→形成片段→附加元数据→计算表示→进入索引。分块过小可能丢掉条件，过大则浪费上下文；按政策条款切分往往比任意字符长度更容易保留边界。表格标题和“仅适用”条件也要保留。

Embedding 将文本映射成数值向量，用相似度寻找候选片段。相似不等于政策适用，更不等于有权限。本例用固定词表计数向量讲清表示与相似度，不是神经 Embedding，也不能宣称有同义词理解能力。第 2 节仍用透明的小索引，以便定位错误。

每个片段保留 doc_id、chunk_id、version、updated_at、scope 和原文。模型升级或向量维度变化应重建索引并保留可回退版本；不能混用不同向量空间。课程默认 Ollama 生成模型并未验证 Embedding 能力，未来接入需单独选择和验证嵌入接口，不能凭模型名字推定支持。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from math import sqrt

DOCS = [
    {"id": "returns", "version": 1, "updated_at": "2026-09-01", "scope": "public",
     "text": "键盘退货须在签收七天内申请。键盘换货需要保留配件。"},
    {"id": "vip", "version": 1, "updated_at": "2026-09-02", "scope": "vip",
     "text": "会员订单享有专属处理通道。"},
]
VOCAB = ("键盘", "退货", "换货", "会员", "订单")
def embed(text):
    return tuple(text.count(word) for word in VOCAB)

def cosine(a, b):
    denominator = sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    return sum(x*y for x,y in zip(a,b)) / denominator if denominator else 0.0

index = []
for doc in DOCS:
    chunks = [part.strip() for part in doc["text"].split("。") if part.strip()]
    for n, text in enumerate(chunks):
        index.append({"doc_id": doc["id"], "chunk_id": f'{doc["id"]}:v{doc["version"]}:{n}',
                      "version": doc["version"], "updated_at": doc["updated_at"],
                      "scope": doc["scope"], "text": text, "vector": embed(text)})

def search(query, scopes):
    query_vector = embed(query)
    candidates = [(cosine(query_vector, row["vector"]), row) for row in index if row["scope"] in scopes]
    return sorted([(score, row) for score,row in candidates if score > 0], key=lambda x: -x[0])

hits = search("键盘退货", {"public"})
assert hits[0][1]["chunk_id"] == "returns:v1:0"
assert not search("会员订单", {"public"})
assert not search("发票", {"public"})
assert len({row["chunk_id"] for row in index}) == len(index)
for score, row in hits:
    print(round(score, 3), row)
print("PASS：可追溯片段、零向量、访问过滤")
```

**预期现象：**键盘退货的第一名是 returns:v1:0；未授权会员查询和词表外的发票返回空。空结果不能说明真实资料绝对不存在。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## RAG 补充：分块策略、元数据增强与问题索引

本节还要回答“为什么按这种方式切块和建索引”，完整知识安排见[RAG 知识清单](../RAG_ROADMAP.md)。下面补充机制，不替换前文已验证的基础例子。

### 分块策略对照

| 策略 | 怎么切 | 适合观察什么 | 失败或代价 |
| --- | --- | --- | --- |
| 固定长度＋overlap | 按 Token 或字符窗口，邻块重叠 | 长度、重叠对召回和成本的影响 | 条款条件切断；重叠造成重复候选 |
| 递归/结构化分块 | 按标题、段落、句子逐级细分 | 政策章节、FAQ 问答、表格标题关联 | 文档解析错会破坏结构 |
| 语义分块 | 根据邻句语义变化等信号判断边界 | 跨段主题变化 | 额外 Embedding 成本；阈值与语言/模型相关，不保证更好 |
| 父子分块 | 小子块用于召回，命中后取较大父块 | 精确匹配同时保留政策条件 | 父块过大超预算；父子版本和权限必须一致 |

分块不是越小越好。对“七天内可退。已使用商品除外”，孤立命中第一句可能导致错误承诺。试固定、结构化和父子三种方式，用相同带例外的问题比较命中、上下文长度和答案遗漏；语义分块在真实嵌入能力验证后再做对照。若输入来自 PDF/表格，先检查 OCR、表头、阅读顺序和重复页眉。

Embedding 选型需要记录模型版本、维度、适用语言、是否要求查询/文档前缀、相似度与归一化约定。第一个索引可用精确比较作基线，随后了解 ANN/HNSW 的召回—延迟取舍；不要把 ANN 搜索参数、召回 candidate_k 和最终 context_k 混为一个 Top-k。

### 元数据与 Hypothetical Questions

`topic/product` 帮助业务过滤；`user_type` 若涉及访问权限，必须来自可信用户上下文。LLM 自动提取的标签只能作为待校验语义信息，不负责授予会员权限。

入库时可为真实片段生成“这个片段能回答哪些问题”，把这些问题作为额外检索入口，记录 `question_id → chunk_id → parent_id`；命中后返回真实正文，不引用生成的问题当政策。政策修改时问题索引也失效，不能保留旧问法对应旧规则。[元数据提取参考](https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_metadata_extractor/)

以下完整块可独立离线执行，模拟的是父子/问题映射与权限，问题是人工夹具，没有执行语义分块或模型生成。

```python
# course: offline
PARENTS = {
    "policy-v2": {"text": "K1 签收七天内可申请退货；已使用除外，赠品须完整。", "scope": "public", "active": True},
    "vip-v1": {"text": "会员专属处理政策。", "scope": "vip", "active": True},
}
CHILDREN = {"c1": "policy-v2", "c2": "vip-v1"}
QUESTIONS = {"K1 拆封后能退吗": "c1", "会员售后有什么不同": "c2"}

def retrieve_parent(question, scopes):
    child_id = QUESTIONS.get(question)
    if child_id is None:
        return {"status": "no_answer"}
    parent_id = CHILDREN[child_id]
    parent = PARENTS[parent_id]
    if not parent["active"] or parent["scope"] not in scopes:
        return {"status": "no_accessible_evidence"}
    return {"status": "ok", "source": parent_id, "matched_child": child_id, "text": parent["text"]}

normal = retrieve_parent("K1 拆封后能退吗", {"public"})
assert normal["source"] == "policy-v2" and "已使用除外" in normal["text"]
assert retrieve_parent("会员售后有什么不同", {"public"})["status"] == "no_accessible_evidence"
assert retrieve_parent("运费多少钱", {"public"})["status"] == "no_answer"
PARENTS["policy-v2"]["active"] = False
assert retrieve_parent("K1 拆封后能退吗", {"public"})["status"] == "no_accessible_evidence"
print(normal)
print("PASS：父块保留例外、权限过滤、未知问题、旧版本拒绝")
```

预期正常返回完整父块和来源；越权、未知和旧版本都不能返回可用证据。额外练习：一条问题映射到多个子块时，先过滤、去重父块并控制预算，再组装上下文。

<details>
<summary>为什么命中子块后仍要检查父块权限？</summary>

父块可能包含更大范围的敏感内容，或父子版本已不一致。子块可访问不自动证明父块所有正文都可访问；权限与有效版本检查必须覆盖实际送给模型的文本。

</details>

补充验收：能比较分块策略；说清“生成问题”和真实证据的关系；政策更新后派生问题索引也应更新。本块仅有标准库依赖；真实 Embedding 与自动问题生成未运行。

## 实验步骤与练习

1. 把“七天内”的条件移动到相邻片段，观察单独检索退货时是否丢条件，再调整分块。
2. 加入同一文档 v2，生成不同 chunk_id，并列出切换索引需要更新的版本字段。
3. 以“退回商品”替换“退货”，解释词表模型的局限；后续换真实 Embedding 后仍用同组样本对照。

## 常见错误

- 丢掉来源只存向量。
- 把余弦分数当作正确概率。
- 将授权过滤留到模型已经看到正文之后。

## 思考题

为什么改嵌入模型后通常需要重建向量索引？

<details>
<summary>参考答案（先自行作答）</summary>

不同模型的维度和语义坐标可能不同，旧向量与新查询向量的距离不再有同一含义。需固定模型版本、重新编码并做检索回归。

</details>

## 验收标准

- [ ] 每个片段能回到文档和版本。
- [ ] 无权限片段不进入候选上下文。
- [ ] 能区分计数向量演示和真实语义 Embedding。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Python math：向量演示使用的数值运算](https://docs.python.org/3.12/library/math.html)

## 下一节衔接

下一节将候选排序、引用和无答案处理接成可检查的问答路径。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_05/session_04/README.md) · [下一节](../session_02/README.md)
