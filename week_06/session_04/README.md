# 第 06 模块 Session 04：解析质量、真实 Embedding 与向量索引

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

从可追溯文档构造索引，知道什么时候必须重新编码或重建。

## 前置知识与学习安排

第六模块前三节和 Python 数据契约。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

入库流水线包含采集、解析、清洗、切块、元数据、编码、写索引、验证与发布。扫描 PDF 需要 OCR，表格要保留表头与单位，标题和页面用于定位；仅按字符切分可能割裂例外条件。先比较固定、结构与父子切分，再用独立问题集评估；语义切分本身也需要额外计算与阈值。

Embedding 要固定模型和版本、维度、编码提示、归一化、距离度量；相同维度不代表向量空间相同。查询/文档可能有不同前缀。batch 可提升吞吐，失败须按稳定 chunk_id 重试，避免重复片段；自动截断可能丢掉重要后半段。

精确近邻作为小数据基线，再对比 HNSW 等 ANN 的构建成本、内存、延迟与召回。索引的 ef/连接数与返回 top_k 不是同一参数。数据库选择先按权限过滤、数据规模、持久化和更新需求，没必要同时学多个产品的全部 API。

下例检查向量契约；后面的 Qdrant 本地扩展才用真实模型生成向量。常驻数据、模型缓存与索引属于运行依赖，实验统计仍只打印。未运行真实扩展不能宣称已经验证中文检索效果。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
from math import sqrt, isfinite

def cosine(a, b):
    if len(a) != len(b) or not a: raise ValueError("dimension")
    if not all(isfinite(x) for x in a+b): raise ValueError("nonfinite")
    na, nb = sqrt(sum(x*x for x in a)), sqrt(sum(x*x for x in b))
    if na == 0 or nb == 0: raise ValueError("zero_vector")
    return sum(x*y for x,y in zip(a,b)) / (na*nb)

def query(vector, model_version, index):
    if model_version != index["model"]: raise ValueError("embedding_version")
    return sorted([(cosine(vector, v), key) for key,v in index["vectors"].items()], reverse=True)

index = {"model": "fixture-v1", "vectors": {"return": [1.,0.], "shipping": [0.,1.]}}
assert query([1.,0.], "fixture-v1", index)[0][1] == "return"
for vec, ver in [([1.,0.], "v2"), ([1.], "fixture-v1"), ([0.,0.], "fixture-v1")]:
    try: query(vec, ver, index)
    except ValueError: pass
    else: raise AssertionError("bad vector accepted")
print("PASS：维度、零向量、版本拒绝；人工向量非语义模型")
```

**预期现象：**正确向量命中；版本、维度与零向量异常均拒绝。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。

## 真实模型与数据库扩展：未安装、未运行

教学 API 基线为 `sentence-transformers==3.3.1`、`qdrant-client==1.12.1`，不是最新版推荐。按需运行 `uv run --with 'sentence-transformers==3.3.1' --with 'qdrant-client==1.12.1' python -`。本次不安装或下载模型；完整可复现环境还要固定传递依赖与模型 revision。

到本课时在根 config.toml 增加 `[embedding]`，填 `model_path`（已下载可信模型的本地目录）、`query_prefix` 和 `document_prefix`（按该模型说明，允许空串）。这是新增能力配置，不修改既有 Ollama 地址。对话生成仍用 common.llm；本地向量编码作为独立接口，不用生成文本伪装向量。

下块独立执行，无需上一块变量；从项目根运行。使用本地内存数据库，关闭后不保留索引；真实部署需要另测持久化与过滤配置。模型路径未配置或不存在会明确失败。

<!-- verify: external -->
```python
import tomllib
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

cfg = tomllib.loads(Path("config.toml").read_text())["embedding"]
model_path = Path(cfg["model_path"]).expanduser()
if not model_path.is_dir(): raise ValueError("请先准备本地 Embedding 模型")
encoder = SentenceTransformer(str(model_path), local_files_only=True, trust_remote_code=False)
texts = ["K1 七天内可申请退货，已使用除外。", "VIP 内部补偿方案。"]
vectors = encoder.encode([cfg["document_prefix"] + x for x in texts], normalize_embeddings=True).tolist()
q = encoder.encode([cfg["query_prefix"] + "K1 用过还能退吗"], normalize_embeddings=True)[0].tolist()
db = QdrantClient(":memory:")
try:
    db.create_collection("policies", vectors_config=models.VectorParams(size=len(q), distance=models.Distance.COSINE))
    db.upsert("policies", points=[models.PointStruct(id=i+1, vector=v, payload={"text": t, "owner": owner})
                                 for i,(v,t,owner) in enumerate(zip(vectors,texts,["u1","u2"]))])
    for trusted_owner in ["u1", "unknown"]:
        hits = db.query_points(collection_name="policies", query=q, limit=2,
            query_filter=models.Filter(must=[models.FieldCondition(key="owner", match=models.MatchValue(value=trusted_owner))])).points
        assert all(h.payload["owner"] == trusted_owner for h in hits)
        if trusted_owner == "unknown": assert not hits
        print(trusted_owner, [(h.id,h.score,h.payload["text"]) for h in hits])
finally:
    db.close()
```

## 实验步骤与练习

1. 用一段含标题、表格、否定和脚注的资料做解析检查；每块能回到原文。
2. 比较固定/结构/父子三种切分，固定问题和编码模型，检查条件完整性。
3. 准备下方真实 Embedding 扩展的本地模型与配置，运行正常及越权过滤；记录实际未命中。
4. 加入更新/删除并检查缓存失效，再以精确检索作为 ANN 召回基准。

## 常见错误

- 嵌入模型换了但维度相同就复用旧索引。
- 先把私有内容送模型再过滤。
- 把手写词频向量视为 Embedding 效果实验。

## 思考题

为什么返回 top_k=5 不能单独说明检索质量？

<details>
<summary>参考答案（先自行作答）</summary>

只限定结果数量，不说明正确证据是否进入候选、是否受权限过滤、是否重复或足以支持回答。

</details>

## 验收标准

- [ ] 每个块都有来源、版本与访问范围。
- [ ] 真实向量实验与人工夹具记录分开。
- [ ] 能用基准解释切块和 ANN 参数的取舍。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Sentence Transformers 使用](https://sbert.net/docs/sentence_transformer/usage/usage.html)
- [Qdrant Python 客户端](https://github.com/qdrant/qdrant-client)
- [SentenceTransformer 3.3.1 接口](https://github.com/huggingface/sentence-transformers/blob/v3.3.1/sentence_transformers/SentenceTransformer.py)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../session_05/README.md)
