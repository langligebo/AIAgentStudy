# RAG 知识清单与课程映射

[第六周概览](README.md) · [总学习计划](../LEARNING_PLAN.md) · [学习进度](../LEARNING_PROGRESS.md)

核对日期：2026-09-21。根据用户提供的 RAG 学习图补查。本文件是课程的知识索引，现对应扩课后的 65 节主线，不代表这些技术或用户掌握程度已经验收。此前 39 节材料齐全，只说明按原提纲备齐文件，不能据此声称覆盖了 RAG 的全部常见方法。

## 本次发现了什么问题

原第六周覆盖基础入库、简单检索、引用、无答案及版本权限管理，但分块仅讲到条款切分；排序只作概述。第七周讲预算和摘要，却没有明确 RAG 证据压缩、文档位置实验。HyDE、Multi-Query、BM25/RRF、RAPTOR、GraphRAG 和 RAGAS 没有正式列入；第九周虽然有 Agent 规划，也没有落实到迭代检索。

这不是把一份完整 RAG 课程藏在几个大标题里，而是原范围确实过浅。本次明确每项内容的目的、所在课次和学习深度。用户说以前学习过 RAG，可在对应节先用解释或小实验确认已有能力；图片的勾选不作为本项目验收证据。

## 对照图中的内容逐项补齐

“主线实践”指要做机制或策略对照；“架构理解”指能解释结构、适用范围、故障与代价，不等于已实现完整框架。技术可在同一 Session 内分次学习，不把全部实践强塞进一次课。

| 阶段 | 知识点 | 原课程覆盖 | 现在的对应位置与深度 |
| --- | --- | --- | --- |
| 入库前 | 固定、递归/结构化、语义 Chunking，大小与 overlap | 只有分块概述和按句切分 | [W06 S01](session_01/README.md)：策略比较与边界实验 |
| 入库前 | 父子分块 / Small-to-Big | 未列出 | [W06 S01](session_01/README.md)：子块召回、父块补条件、权限再检查 |
| 入库前 | 元数据增强与过滤 | 有来源、版本和权限，缺主题/产品等策略 | [W06 S01](session_01/README.md)：topic、product、user_type；可信 ACL 与语义标签分开 |
| 入库前 | Hypothetical Questions：为片段预生成可回答的问题 | 未列出 | [W06 S01](session_01/README.md)：问题索引→原始片段，理解与对照 |
| 检索时 | BM25、向量检索、混合检索、RRF | 只讲关键词和向量区别 | [W06 S02](session_02/README.md)：BM25/RRF 最小实现与候选集合对照 |
| 检索时 | HyDE | 未列出 | [W06 S02](session_02/README.md)：假设文档用于检索，不当作答案证据 |
| 检索时 | Multi-Query | 未列出 | [W06 S02](session_02/README.md)：多种问法、去重、查询预算、漂移检查 |
| 检索时 | 查询分解与 Step-Back | 未列出 | [W06 S02](session_02/README.md) 区分机制，[W09 S02](../week_09/session_02/README.md) 接入计划与迭代 |
| 检索后 | Reranking：Cross-encoder、BGE Reranker、Cohere Rerank | 只一句概述 | [W06 S02](session_02/README.md)：召回与重排职责、候选预算、对照实验 |
| 检索后 | 上下文压缩 | 只有通用工具摘要 | [W07 S01](../week_07/session_01/README.md)：证据抽取、条件保留、来源回溯 |
| 检索后 | 文档重排列、Lost-in-the-Middle | 未列出 | [W07 S01](../week_07/session_01/README.md)：固定证据集合，仅改变位置作对照 |
| 进阶架构 | RAPTOR | 未列出 | [W06 S03](session_03/README.md)：递归聚类与摘要树的原理和失效边界；架构理解 |
| 进阶架构 | GraphRAG | 未列出 | [W06 S03](session_03/README.md)：实体关系、社区摘要、局部/全局问题；架构理解 |
| 进阶架构 | Agentic RAG | 只有泛化 Agent 规划 | [W09 S02](../week_09/session_02/README.md)：决定是否补检索、分解问题、停止/追问；主线实践 |
| 评估 | RAGAS，Context Precision / Recall、Faithfulness | 有基础命中/正确率，无 RAGAS | [W06 S03](session_03/README.md) 建样本，[W10 S01](../week_10/session_01/README.md) 学指标，[W10 S03](../week_10/session_03/README.md) 做消融与回归 |

## 用同一个客服问题串起来

问题：“K1 键盘已经拆封，昨天收到，能退吗？赠品也要寄回吗？”知识库含普通退货条款、拆封例外和赠品条款。

1. **入库**：按条款切块，保留产品、版本、适用用户与来源；子块用于匹配“拆封”，父块提供完整例外条件。由正文生成“拆封的 K1 能否退货？”作为检索入口，命中后仍返回原文。
2. **召回**：BM25 寻找 K1、拆封等精确词，向量分支寻找“开封/启封”等语义相关片段；各分支先按权限与有效版本过滤，合并候选并去重。
3. **查询变换**：单次检索缺赠品条款时，试多问法或拆成两个子问题。HyDE 生成的中间文档只能帮助定位资料，不得承诺“拆封必退”。
4. **重排与组装**：重排提升对本问相关的候选位置；去掉噪声和重复，保留“七天”“未使用”“例外”“赠品完整”等条件和引用。必要时做文档位置对照。
5. **迭代与回答**：若缺拆封例外，Agent 可在预算内补检索；仍无证据则说明缺口或追问，不无限循环、不编造政策。
6. **评估**：同时检查应找到的条款是否命中、是否带入大量无关块、回答是否受证据支持、例外是否遗漏、耗时和调用数是否增加。

## 容易混淆的几组概念

### Hypothetical Questions 与 HyDE

前者在入库时围绕已有片段生成可能问题，建立“问题→源片段”映射；后者在查询时围绕用户问题生成假设文档，再用该文档的向量检索真实文档。两者的生成文本都不是新的事实来源。HyDE 的“假设答案”更准确地说是检索中间表示，存在幻觉与主题漂移风险。[HyDE 原论文](https://aclanthology.org/2023.acl-long.99/)

### 混合检索、RRF 与 Reranking

混合检索组合词项与向量等召回渠道；RRF 根据各列表名次融合候选，属于融合方法；Cross-encoder 重排将 query 与候选文本一起打分。RRF 不等同于神经重排，重排也找不回完全没有进入候选集合的证据。[RRF 官方说明](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)、[Retrieve & Re-Rank](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)

Cross-encoder 是建模方式，BGE Reranker 是模型系列，Cohere Rerank 是服务/产品实现，不能视作三个互斥的算法层级。选择时比较中文、长输入、部署条件、延迟和数据发送范围，不因名字被列出就必须安装全部。[BGE 模型说明](https://huggingface.co/BAAI/bge-reranker-v2-m3)、[Cohere Rerank 说明](https://docs.cohere.com/docs/rerank-overview)

### Multi-Query、查询分解与 Step-Back

Multi-Query 从同一意图生成多种表述；分解把复合任务拆成需分别取证的问题；Step-Back 提升抽象层次，例如先问“拆封商品的退货资格由哪些规则决定”，取得一般原则后还需回到 K1 的具体限制。抽象不等于把一个问题拆成多个问题。[Step-Back 原论文](https://arxiv.org/abs/2310.06117)

### Reranking 与文档重排列

重排估计候选相关性；重排列改变送给模型的上下文位置。Lost-in-the-Middle 是有关长上下文中位置影响的实验发现，不能推出所有模型都如此，也不能保证将证据移到两端就解决问题。必须固定证据与模型做位置实验。[原论文](https://aclanthology.org/2024.tacl-1.9/)

### FAQ 与上下文压缩

图中“FAQ 场景不需要”应改成条件判断：少量、短小、完整的 FAQ 常可先不压缩；当召回重复、多文档、长答案或超预算时仍可能有必要。压缩的收益和是否漏掉否定、时间及适用条件要测量，不能按“FAQ”标签一概决定。

### RAPTOR、GraphRAG 与 Agentic RAG

RAPTOR 组织多层语义摘要；GraphRAG 利用图关系等结构；Agentic RAG 控制检索决策和反馈循环。前两者偏知识组织，后者偏运行时决策，能够组合。不是“从普通 RAG 升级到三种技术就一定更好”。架构、数据维护、额外模型调用和验收成本必须一起比较。[RAPTOR 论文](https://arxiv.org/abs/2401.18059)、[Microsoft GraphRAG 查询概览](https://microsoft.github.io/graphrag/query/overview/)

## 图外还需要保留的基础

这些不是另开一套课程，而是已有章节应明确检查的工程条件：

- 解析质量：扫描 PDF 的 OCR、表格行列与表头、标题层次、重复与噪声清理；解析失败不能靠后面的向量模型修复。
- Embedding：中文/领域适配、查询与文档编码要求、维度、相似度和归一化；更换模型版本需要重建或迁移索引并验收。
- 索引：精确检索与 ANN 的速度/召回取舍，HNSW 的索引和查询参数认识，candidate_k、rerank_k、context_k 分别控制哪个阶段。具体数据库按实践需要选择，不同时安装多个。
- 数据治理：版本替换、删除传播、可信身份、ACL、缓存隔离、索引一致性；自动生成 topic 不能代替用户权限。
- 生成与证据：引用准确性、冲突政策、无答案阈值、提示注入、答案正确性和端到端任务标准。
- 实验：固定数据和版本，一次变一项，先看失败样本再决定启用哪种增强；统计质量、延迟、Token/调用和真实费用，未知不写成零。

## 实际学习与时间安排

现为 13 个主题模块、65 个 Session，原 week 目录和旧课编号保留，新增课按同模块顺序学习。第六周做 RAG 基线、分块/融合/重排的核心机制与对照；第七周处理证据上下文；第九周做查询规划和 Agentic RAG；第十周做 RAGAS 指标与回归。RAPTOR、GraphRAG 现各有独立结构机制课与对照步骤；完整自动构建索引管线及规模化工程未标为已完成。

原先每周 6～8 小时只是基础预算，无法承诺在第六周一次完成图中所有技术的工程实践。对已经掌握的内容先用小题/实验确认，再把时间用在薄弱处；需要深做某种架构时按实际进度延长，同一 Session 可以分几次，不擅自推进学习位置。

## 材料与验证边界

- 本次补齐知识清单、课次安排、方法解释、策略对照步骤和机制示例；未安装新框架或模型。
- 新增离线块使用 Python 3.12 标准库，排序/评估中的人工夹具都显式标明；不把它们称作真实嵌入、Cross-encoder 或 RAGAS SDK 实验。
- 真实 Embedding、HyDE/Multi-Query 生成、Reranker、RAGAS 评分及 RAPTOR/GraphRAG 工程实验仍需在学习到相应课次时验证。当前公共客户端没有 Embedding 接口；不能用 `generate()` 文本假装向量。生成调用复用 `common.llm.create_llm_client()`；将来新增嵌入或评分适配先明确契约，不在各课复制服务地址。
- 纯概念说明不绑定某 SDK 版本；具体 SDK 安装和运行在引入实现时再固定版本并检查官方接口。资料核对日是 2026-09-21，不表示已经完成库级运行验证。
- 学习位置继续为 W02 S03；RAG 各课仍未开始，用户以往学习经历不自动转换为本项目通过记录。

## 参考资料

仅把这些资料作为概念和接口依据，不把原文代码整段复制成项目已验证实现。

- [LlamaIndex：从片段提取可回答问题的元数据示例](https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_metadata_extractor/)
- [LangChain：MultiQueryRetriever 接口说明](https://reference.langchain.com/python/langchain-classic/retrievers/multi_query/MultiQueryRetriever)
- [Ragas：Context Precision](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)、[Context Recall](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/)、[Faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/)

## 全课程扩课后的独立实践入口

- [W06 S04：解析、真实 Embedding 与向量索引](session_04/README.md)
- [W06 S05：查询增强、重排与消融](session_05/README.md)
- [W06 S06：RAPTOR 层级与派生证据](session_06/README.md)
- [W06 S07：GraphRAG 与图检索](session_07/README.md)
- [W10 S05：RAGAS SDK 适配与观测](../week_10/session_05/README.md)

这些入口补充原三节，不重复生成或替换旧内容。真实索引、生成和评分代码已保存但未运行，不能用结构夹具通过代替模型效果。
