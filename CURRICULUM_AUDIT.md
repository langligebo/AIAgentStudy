# 全课程覆盖审查与验收矩阵

[学习计划](LEARNING_PLAN.md) · [全部课件](README.md#课程总目录) · [当前学习进度](LEARNING_PROGRESS.md)

审查日期：2026-09-21。依据用户“检查整个课件、允许增加课时”的要求，对原 39 节的目标、概念、示例、练习、前置与验收逐项检查。结果是：原主线合理，但知识深度与实践连接不足；仅把 39 个文件备齐不能称为系统性覆盖。

本次保留原教案，新增 **26 节，共 65 节**。原 13 个 week 目录改作主题模块编号，每模块 4～7 节，允许跨自然周。每节建议 2～4 小时；实际模型、框架联调和项目验收可能另需时间，不再以原 13 周时限压缩内容。

## 完整性如何检查

本课程的目标是独立设计、实现、评估、诊断和交付 Python Agent 应用。覆盖从模型与 Python 基础，到工具、运行时、Skills、RAG、记忆、编排、协作、协议、安全、运行和交付。不是声称包含所有论文、框架或未来技术，而是给每个关键能力一个明确位置、实验和失败验收，专项方向也写明边界与继续路径。

学习深度分为：

- **理解**：能解释机制、适用与不适用场景，并分析失败；不是认得名词。
- **机制实践**：实现或修改可运行切片，验证正常和失败路径；人工夹具不代表真实模型效果。
- **真实实验**：用选定模型、SDK/协议、数据库或服务运行，固定版本和输入，记录实际结果。
- **项目集成**：跨模块闭环，通过独立终态、权限、恢复与性能检查。

核心工程能力需要逐层走到真实实验或项目集成。专门训练、实时音视频、大规模图谱等至少完成理解和机制边界，是否建设完整专项系统由后续目标决定；不会标作已实战。下表是**教学目标**，不是用户已掌握记录。

## 逐模块审查结论

| 模块 | 原有三节已经覆盖 | 发现的不足 | 已增加课时 | 现在总课时 |
| --- | --- | --- | --- | --- |
| 01 基础 | 采样、架构、Prompt 对照 | Python 工程是隐含前提；tokenizer/注意力/推理资源缺成体系讲解 | S04 工程基础；S05 模型机制 | 5 |
| 02 可靠调用 | 能力探针、结构化、故障基线 | 服务商适配与字节/事件边界浅；Prompt 进阶和多模态未独立安排 | S04 协议适配；S05 Prompt 进阶；S06 多模态输入 | 6 |
| 03 工具 | 协议、契约权限、错误分页 | 工具目录规模、界面设计与乱序关联缺独立练习 | S04 工具发现、界面与并发契约 | 4 |
| 04 运行时 | 循环、任务状态、终态核验 | 固定决策器验证不能替代真实模型接入 | S04 同一循环的真实模型适配 | 4 |
| 05 Skills | 编写、加载、触发评估 | 包依赖、内容完整性、宿主 hooks/插件关系未讲透 | S04 包验证与生命周期 | 4 |
| 06 RAG | 基础链路；上轮补了方法说明 | 真实编码/数据库缺独立完整示例；增强和树/图挤在三节 | S04 索引；S05 增强；S06 RAPTOR；S07 GraphRAG | 7 |
| 07 记忆 | 预算、存储、冲突删除 | 缺写入候选、巩固、读取相关性及跨会话效果评估 | S04 记忆闭环与质量 | 4 |
| 08 LangGraph | 图、checkpoint、审批与重放 | 并行 reducer、子图、事件与状态迁移不够 | S04 并行/子图/流式 | 4 |
| 09 规划协作 | Workflow、计划修正、有限检查 | 多 Agent/A2A 仅作为选修标题 | S04 协作；S05 A2A | 5 |
| 10 评估观测 | 分层评分、事件、配对回归 | 样本分组、统计区间、judge 偏差、线上指标与 SDK 适配浅 | S04 统计与数据集；S05 追踪/RAGAS | 5 |
| 11 协议安全 | MCP stdio、适配、安全负例 | 远程认证与能力协商欠缺；隔离/浏览器/网络威胁未展开 | S04 远程 MCP；S05 执行与威胁 | 5 |
| 12 服务运行 | API、并发超时、部署基础 | 进程内后台非持久队列；事件重连/背压、缓存、熔断和路由欠缺 | S04 队列；S05 交互；S06 性能与降级 | 6 |
| 13 综合交付 | 需求、模拟集成、基础验收 | 模拟切片到真实工程的边界不够清楚；CI/恢复/训练路线缺独立安排 | S04 工程契约；S05 生产验收；S06 训练选型与总复盘 | 6 |

## 知识、实践与验收映射

每行指向实际教案。原有章节保留其正常/失败练习，新增课补充独立样例与验收。章节中“未运行”的外部实验仍然未运行，不能从下表推断完成。

| 能力 | 教案位置 | 主线要求 | 必须能解释或复现的失败 |
| --- | --- | --- | --- |
| Python、模块、类型、异常、with、迭代、测试、uv/Git | [W01 S04](week_01/session_04/README.md) | 机制实践 | 类型注解不校验、超时变空结果、错环境 |
| Tokenizer、embedding、注意力、自回归、训练/推理 | [W01 S05](week_01/session_05/README.md) | 理解＋采样演算 | 概率当真值、字符当 token |
| Temperature/Top-p/seed、量化、KV/cache、资源 | [W01 S01](week_01/session_01/README.md)、[W12 S06](week_12/session_06/README.md) | 真实对照 | 冷启动、长尾、变量混改 |
| 单次调用、Workflow、Agent 的选择 | [W01 S02](week_01/session_02/README.md) | 理解＋架构设计 | 固定循环误判成自主规划 |
| Prompt、Few-shot、指令/数据、任务分解、自检 | [W01 S03](week_01/session_03/README.md)、[W02 S05](week_02/session_05/README.md) | 真实对照 | 歧义、示例泄漏、一致错误、注入 |
| 消息角色、能力矩阵、多供应商协议 | [W02 S01](week_02/session_01/README.md)、[W02 S04](week_02/session_04/README.md) | 契约＋真实探针 | 能力不支持、调用 ID 丢失 |
| JSON Schema/Pydantic、严格字段与业务关系 | [W02 S02](week_02/session_02/README.md) | 机制＋真实输出 | 合法 JSON 但业务错误 |
| 流式字节、事件、答案终止 | [W02 S04](week_02/session_04/README.md) | 机制＋真实协议 | UTF-8 跨块、缺终止、坏帧 |
| 模型失败分类、基线与保留集 | [W02 S03](week_02/session_03/README.md) | 真实基线 | 截断、拒绝、空响应、分母偏差 |
| 图片/OCR/语音/交互事件 | [W02 S06](week_02/session_06/README.md) | 理解＋契约机制 | 部分转写、旧轮迟到、附件误读 |
| 工具调用与多调用关联 | [W03 S01](week_03/session_01/README.md)、[W03 S04](week_03/session_04/README.md) | 真实协议＋机制 | 重复、乱序、无结果 |
| 工具界面、Schema、分页、目录检索 | [W03 S03](week_03/session_03/README.md)、[W03 S04](week_03/session_04/README.md) | 机制＋选择实验 | 工具漏选、参数歧义、部分结果 |
| 身份、ACL、审批、输入/输出契约 | [W03 S02](week_03/session_02/README.md) | 项目集成 | 伪造身份、参数变更、损坏输出 |
| 重试、deadline、幂等、未知结果 | [W03 S03](week_03/session_03/README.md)、[W08 S03](week_08/session_03/README.md)、[W12 S02](week_12/session_02/README.md) | 项目集成 | 写已成功但回包丢失 |
| ReAct 式观察循环、步数/工具/费用预算 | [W04 S01](week_04/session_01/README.md)、[W04 S04](week_04/session_04/README.md) | 真实模型循环 | 无进展、提前完成、预算失控 |
| 任务状态、追问、更正、取消、实际完成证据 | [W04 S02](week_04/session_02/README.md)、[W04 S03](week_04/session_03/README.md) | 项目集成 | 旧目标动作、虚假成功 |
| Skill 内容结构、触发、按需加载 | [W05 S01](week_05/session_01/README.md)、[W05 S02](week_05/session_02/README.md) | 真实激活实验 | 误触发、漏触发、路径逃逸 |
| Skill 版本回退、包依赖、插件/hooks | [W05 S03](week_05/session_03/README.md)、[W05 S04](week_05/session_04/README.md) | 机制＋集成 | 同版本改内容、权限膨胀 |
| 解析/OCR/表格/清洗、各类 chunking | [W06 S01](week_06/session_01/README.md)、[W06 S04](week_06/session_04/README.md) | 真实数据对照 | 条件被切断、表头丢失 |
| 元数据、父子块、Hypothetical Questions | [W06 S01](week_06/session_01/README.md) | 机制＋对照 | 生成问题被当事实、父块越权 |
| 真实 Embedding、距离/归一化、向量数据库、ANN | [W06 S04](week_06/session_04/README.md) | 真实索引实验 | 同维不同模型、零向量、过滤错误 |
| BM25、混合检索、RRF、候选预算 | [W06 S02](week_06/session_02/README.md)、[W06 S05](week_06/session_05/README.md) | 机制＋消融 | 候选缺失、重复融合 |
| HyDE、Multi-Query、分解、Step-Back | [W06 S05](week_06/session_05/README.md) | 方法比较＋至少一种真实实验 | 查询漂移、假设内容当证据 |
| Cross-encoder、BGE/Cohere、MMR | [W06 S02](week_06/session_02/README.md)、[W06 S05](week_06/session_05/README.md) | 真实重排＋机制比较 | 找不回漏召回、相关但无依据 |
| 压缩、位置重排、Token 预算 | [W07 S01](week_07/session_01/README.md) | 真实对照 | 否定/例外丢失、位置影响 |
| 引用、无答案、冲突、数据删除/更新/ACL | [W06 S02](week_06/session_02/README.md)、[W06 S03](week_06/session_03/README.md) | 项目集成 | 旧政策、缓存泄漏、伪造来源 |
| RAPTOR 摘要树、GraphRAG 图/社区 | [W06 S06](week_06/session_06/README.md)、[W06 S07](week_06/session_07/README.md) | 理解＋结构机制＋选型实验 | 摘要失真、错误边、派生权限 |
| Agentic RAG、检索规划、停止与追问 | [W09 S02](week_09/session_02/README.md) | 真实迭代对照 | 无限补查、没有证据却完成 |
| 状态/对话/长期记忆、语义/情节/程序性记忆 | [W07 S02](week_07/session_02/README.md)、[W07 S04](week_07/session_04/README.md) | 机制＋跨会话实验 | 一次要求永久化、错误巩固 |
| 记忆候选、冲突、过期、删除和投毒 | [W07 S03](week_07/session_03/README.md)、[W07 S04](week_07/session_04/README.md) | 项目集成 | 旧请求复活、来源混淆 |
| LangGraph State/Node/Edge、迁移等价 | [W08 S01](week_08/session_01/README.md) | 真框架对照 | 覆盖更新丢状态 |
| Checkpoint、interrupt、审批恢复、重放 | [W08 S02](week_08/session_02/README.md)、[W08 S03](week_08/session_03/README.md) | 真实重启实验 | 节点重跑导致重复副作用 |
| Reducer、并行、Send/Command、子图/流事件 | [W08 S04](week_08/session_04/README.md) | 真框架＋契约 | 冲突合并、旧 schema |
| 路由/串行/并行、计划执行、反思修正 | [W09 S01](week_09/session_01/README.md)、[W09 S02](week_09/session_02/README.md)、[W09 S03](week_09/session_03/README.md) | 真实策略对照 | 依赖未满足、无依据自检 |
| 多 Agent 主管/交接/并行、全局预算 | [W09 S04](week_09/session_04/README.md) | 机制＋真实比较 | 重复劳动、冲突、子任务超预算 |
| A2A 发现、Task、Artifact、消息/事件 | [W09 S05](week_09/session_05/README.md) | 理解＋生命周期；SDK 通信实验 | 终态改写、重复通知、假产物 |
| 检索/生成/工具/轨迹/终态的分层指标 | [W10 S01](week_10/session_01/README.md) | 项目评估 | 文字好但工具失败 |
| RAGAS、人工校准、失败/NaN 处理 | [W10 S01](week_10/session_01/README.md)、[W10 S05](week_10/session_05/README.md) | 真实评分对照 | 错误高分、评分器截断 |
| 数据集/近重复/组划分/合成/保留 | [W10 S04](week_10/session_04/README.md) | 机制＋真实评价设计 | 近重复泄漏、标签污染 |
| 配对、波动、区间、pass@k 与可靠性 | [W10 S03](week_10/session_03/README.md)、[W10 S04](week_10/session_04/README.md) | 统计机制＋实测 | 小样本过度推断、平均掩盖退化 |
| Trace/Span/log/metrics、OTel、脱敏与版本 | [W10 S02](week_10/session_02/README.md)、[W10 S05](week_10/session_05/README.md) | 追踪接入 | 缺父子关联、敏感正文、高基数 |
| 线上反馈、漂移、shadow/canary、SLO | [W10 S05](week_10/session_05/README.md)、[W13 S05](week_13/session_05/README.md) | 设计＋受控演练 | 影子重复写、反馈延迟 |
| MCP Host/Client/Server、tools/resources/prompts | [W11 S01](week_11/session_01/README.md)、[W11 S02](week_11/session_02/README.md) | 真 SDK 联调 | 协议错误与工具错误混淆 |
| 远程 MCP、传输、OAuth、scope/audience、能力协商 | [W11 S04](week_11/session_04/README.md) | 契约＋受控远程实验 | 会话当身份、旧版本误兼容 |
| 提示注入、秘密/隐私、数据外传、最小权限 | [W11 S03](week_11/session_03/README.md)、[W11 S05](week_11/session_05/README.md) | 威胁模型＋安全回归 | 不可信内容升级权限 |
| 文件/代码/网络沙箱、SSRF、供应链、浏览器核验 | [W11 S05](week_11/session_05/README.md) | 边界机制＋隔离测试 | 路径/重定向逃逸、重复点击 |
| FastAPI 任务接口、身份与多租户 | [W12 S01](week_12/session_01/README.md) | 真实接口 | 202 当完成、跨用户查状态 |
| asyncio、并发/限流、deadline、取消/退避 | [W12 S02](week_12/session_02/README.md) | 实测＋故障 | 线程未停、重试放大 |
| 持久队列、outbox、租约、fencing、死信 | [W12 S04](week_12/session_04/README.md) | 持久故障演练 | 重复投递、旧 worker 覆盖 |
| SSE、重连、背压、快照、人工审核 UX | [W12 S05](week_12/session_05/README.md) | 真实事件/界面实验 | 漏事件、超时自动批准 |
| 成本、路由/fallback、缓存、熔断和负载 | [W12 S06](week_12/session_06/README.md) | 真实性能对照 | 缓存越权、降级丢能力 |
| 健康检查、配置、部署、状态迁移/回退 | [W12 S03](week_12/session_03/README.md) | 部署演练 | 存活但不可用、不兼容恢复 |
| 需求、独立验收器、分层测试、真实综合工程 | [W13 S01](week_13/session_01/README.md)、[W13 S02](week_13/session_02/README.md)、[W13 S03](week_13/session_03/README.md)、[W13 S04](week_13/session_04/README.md) | 项目集成 | 模拟自证、写错对象、缺故障路径 |
| CI、锁版本、备份恢复、RPO/RTO、发布交付 | [W13 S05](week_13/session_05/README.md) | 完整验收 | 备份不可用、恢复丢幂等键 |
| SFT/LoRA/QLoRA、DPO/RL、奖励/蒸馏、训练边界 | [W13 S06](week_13/session_06/README.md) | 理解＋数据机制＋选型设计 | 训练解决不了权限、奖励投机与遗忘 |

## 前置依赖与当前学习衔接

1. 当前保持 **W02 S03**。继续学习先完成现有失败分类、分母题与基线待办；扩课不替用户验收。
2. 新增 W01 S04/S05 是前置补充：先做解释/小实验检测，不足处补学，不要求无依据重学原六节，也不能自动勾选新课。
3. 明确说“下一节”时，现从 W02 S03 进入 **W02 S04**，而不是跳到 W03。此变化只更新导航，不改变当前停留点或历史证据。
4. W03 工具契约 → W04 真循环 → W05 Skill → W06 RAG → W07 记忆 → W08 图持久化 → W09 规划/协作 → W10 评估 → W11 外部协议安全 → W12 服务 → W13 工程验收。
5. 各课最小块自带数据；真实扩展明确是否依赖同进程前块。框架、模型和数据库按学习需要安装，不提前改公共客户端和项目依赖。

## 集成检查点

| 检查点 | 验收证据 |
| --- | --- |
| W02 结束 | 真实能力矩阵、分类基线；格式/任务/失败分别说明 |
| W04 结束 | 真实模型选择工具、程序授权、观察反馈、有证据停止 |
| W07 结束 | Skill 按需加载、真实检索与引用、记忆纠正/隔离 |
| W09 结束 | checkpoint 重启、审批拒绝、幂等恢复；规划/协作与简单方案对比 |
| W12 结束 | 受控协议/API 联调、取消、重复投递、重连与性能边界 |
| W13 结束 | 保留集质量、安全与故障验收，部署/恢复手册可复现，用户解释和实践确认 |

## 本次验证记录与边界

- 新增 26 个独立标准库最小示例，正常和失败/边界路径已实际执行，使用隔离临时目录并禁止网络。
- 全部 65 节、13 个概览、86 个 Python 代码块语法和 1,287 个本地链接已检查；前后节构成连续导航，65 节均映射到覆盖矩阵。源码语法通过不等于 SDK 或真实模型运行通过。
- 新增真实模型/SDK 代码块只核对语法与相应接口资料，没有安装依赖、下载模型、联网实验或部署。真实效果和 SDK 运行兼容仍待对应课时实测。
- 旧课的历史运行证据保留；本次主要检查覆盖、源码引用、语法和导航，不把未重复执行的旧例写成新实测。
- 当前学习位置、原始用户反馈和历史待办保留。原 33 节后续课及新增 26 节均未开始学习。
- 公共客户端、配置、依赖和已有 Python 源码不因此次备课改动；实验输出仍只到控制台，不自动提交 Git。

## 外部资料基线与版本治理

核心方法核对 [Agent 架构](https://www.anthropic.com/engineering/building-effective-agents)、[工具设计](https://www.anthropic.com/engineering/writing-tools-for-agents)、[Skills 规范](https://agentskills.io/specification)、[LangGraph API](https://docs.langchain.com/oss/python/langgraph/graph-api)、[A2A 规范](https://a2a-protocol.org/latest/specification/)、[MCP 规范](https://modelcontextprotocol.io/specification/2026-07-28)、[Agent 评估](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)、[OpenTelemetry](https://opentelemetry.io/docs/languages/python/instrumentation/)。RAG 方法及原论文见[专项清单](week_06/RAG_ROADMAP.md)。

真实扩展采用显式教学版本：LangGraph 1.0.1、MCP Python 1.20.0、Sentence Transformers 3.3.1、Qdrant Client 1.12.1、Ragas 0.2.15 等是接口基线，不是最新版推荐或已验证锁定环境。MCP 原协议例固定 2025-06-18，新规范对照为 2026-07-28；A2A 本次只核对 v1.0 概念，不宣称内部状态例符合完整协议。引入时需固定实际依赖锁和模型 revision，跑兼容测试后才记验证通过。

今后增删内容按“能力行 → 教案 → 实验 → 失败验收 → 进度证据”维护；发现只列名词、缺前置、只用夹具或没有失败标准时视为需要补课，不视为覆盖完成。
