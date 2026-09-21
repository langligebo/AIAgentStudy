# AI Agent 开发学习

使用 Python 学习 AI Agent 开发，按周组织内容，每周包含若干 Session。

## 学习入口

- [学习进度](LEARNING_PROGRESS.md)：当前仍为**第 02 周 Session 03**，历史待办与实验、验收证据分别记录。
- [教学约定](AGENTS.md)：先读取已保存教案，再按实际进度讲解。
- [65 节学习计划](LEARNING_PLAN.md)：每周安排、实践任务和验收标准。
- [全课程覆盖审查](CURRICULUM_AUDIT.md)：按能力、实践、前置和验收核对缺口，明确新增课与专项边界。
- [RAG 知识清单与课程映射](week_06/RAG_ROADMAP.md)：分块、混合检索、查询增强、重排、进阶架构及 RAGAS；明确实践深度。
- [当前课件：第二周 Session 03](week_02/session_03/README.md)：失败分类、离线故障注入、开发集与保留集、模型基线。

主线是“知识库客服助手”。全部 **13 个主题模块、65 节教案和 13 个模块概览**已保存；原 week 目录保留，实际学习可跨周。新增 26 节及原后续 33 节均未开始学习。说“继续学习”接当前停留点，“下一节”取下一份课件，“发我课件”返回当前文件；不会反复生成，未完成验收也不会自动勾选。

## 课程总目录

模块编号保持原目录；按同模块 Session 顺序学习。当前仍停在 W02 S03，新增早期基础课先做检测、缺项补学，不默认已掌握。

| 模块与概览 | 课时 | 全部教案 |
| --- | --- | --- |
| [01 LLM、Agent 与 Prompt 基础](week_01/README.md) | 5 | [01 Temperature 对比实验](week_01/session_01/README.md)；[02 单次模型调用、Workflow 与 Agent](week_01/session_02/README.md)；[03 Prompt 设计与输出校验](week_01/session_03/README.md)；[04 Python 工程基础与测试入口](week_01/session_04/README.md)；[05 模型机制、采样与能力边界](week_01/session_05/README.md) |
| [02 模型能力验证与可靠调用](week_02/README.md) | 6 | [01 模型能力验证与请求协议](week_02/session_01/README.md)；[02 JSON Schema、Pydantic 与业务校验](week_02/session_02/README.md)；[03 调用失败处理、能力基线与测试样本划分](week_02/session_03/README.md)；[04 服务商适配、能力契约与流式组装](week_02/session_04/README.md)；[05 Prompt 进阶、指令与数据分离](week_02/session_05/README.md)；[06 多模态输入与交互事件基础](week_02/session_06/README.md) |
| [03 工具调用与数据契约](week_03/README.md) | 4 | [01 工具调用协议](week_03/session_01/README.md)；[02 工具执行器：契约、业务与权限](week_03/session_02/README.md)；[03 工具错误、选择与重试边界](week_03/session_03/README.md)；[04 工具界面设计、检索选择与并发契约](week_03/session_04/README.md) |
| [04 手写 Agent 循环与任务状态](week_04/README.md) | 4 | [01 最小 Agent 执行循环](week_04/session_01/README.md)；[02 任务状态、追问、更正与取消](week_04/session_02/README.md)；[03 环境反馈、完成验证与退出](week_04/session_03/README.md)；[04 把真实模型接入手写循环](week_04/session_04/README.md) |
| [05 Agent Skills](week_05/README.md) | 4 | [01 编写售后处理 Skill](week_05/session_01/README.md)；[02 Skill 发现、选择与渐进加载](week_05/session_02/README.md)；[03 Skill 评估、版本与回退](week_05/session_03/README.md)；[04 Skill 包验证、依赖与宿主生命周期](week_05/session_04/README.md) |
| [06 RAG 与知识数据管理](week_06/README.md) | 7 | [01 文档解析、分块与索引](week_06/session_01/README.md)；[02 检索排序、证据引用与无答案](week_06/session_02/README.md)；[03 知识更新、删除与检索评估](week_06/session_03/README.md)；[04 解析质量、真实 Embedding 与向量索引](week_06/session_04/README.md)；[05 查询增强、重排与检索消融实验](week_06/session_05/README.md)；[06 RAPTOR 分层索引与派生证据](week_06/session_06/README.md)；[07 GraphRAG、图检索与跨文档问题](week_06/session_07/README.md) |
| [07 上下文编排与记忆](week_07/README.md) | 4 | [01 上下文选择与预算](week_07/session_01/README.md)；[02 任务、历史与长期记忆存储](week_07/session_02/README.md)；[03 记忆纠正、冲突、过期与删除](week_07/session_03/README.md)；[04 记忆写入、检索与巩固评估](week_07/session_04/README.md) |
| [08 LangGraph、持久化与人工介入](week_08/README.md) | 4 | [01 LangGraph 的 State、Node 与 Edge](week_08/session_01/README.md)；[02 Checkpoint、人工审批与恢复](week_08/session_02/README.md)；[03 重放、副作用与结果未知](week_08/session_03/README.md)；[04 LangGraph 并行状态、子图与流式事件](week_08/session_04/README.md) |
| [09 工作流、规划与结果验证](week_09/README.md) | 5 | [01 固定工作流、路由与并行依赖](week_09/session_01/README.md)；[02 动态计划、重新规划与 Skill 复用](week_09/session_02/README.md)；[03 结果验证与有限修正](week_09/session_03/README.md)；[04 多 Agent 分工、交接与协作评估](week_09/session_04/README.md)；[05 A2A 与跨 Agent 任务协议](week_09/session_05/README.md) |
| [10 评估、追踪与实验管理](week_10/README.md) | 5 | [01 分层评估与评分器校准](week_10/session_01/README.md)；[02 结构化追踪与实验复现](week_10/session_02/README.md)；[03 配对对照、回归与发布判断](week_10/session_03/README.md)；[04 数据集设计、统计不确定性与评分器偏差](week_10/session_04/README.md)；[05 追踪接入、线上反馈与 RAGAS 适配](week_10/session_05/README.md) |
| [11 MCP 与安全边界](week_11/README.md) | 5 | [01 MCP 架构、发现与调用协议](week_11/session_01/README.md)；[02 Python MCP 服务与客户端适配](week_11/session_02/README.md)；[03 提示注入、最小权限与安全回归](week_11/session_03/README.md)；[04 远程 MCP、能力协商与授权](week_11/session_04/README.md)；[05 执行隔离、浏览器动作与威胁建模](week_11/session_05/README.md) |
| [12 服务化与运行可靠性](week_12/README.md) | 6 | [01 任务式 FastAPI 接口](week_12/session_01/README.md)；[02 并发、超时、限流与取消传播](week_12/session_02/README.md)；[03 部署准备、健康检查与回退](week_12/session_03/README.md)；[04 持久任务队列、租约与事务发件箱](week_12/session_04/README.md)；[05 事件流、背压与人工审核体验](week_12/session_05/README.md)；[06 性能、路由、缓存与服务降级](week_12/session_06/README.md) |
| [13 综合项目与验收](week_13/README.md) | 6 | [01 综合项目需求与验收设计](week_13/session_01/README.md)；[02 端到端整合与故障修复](week_13/session_02/README.md)；[03 基础项目验收、演示与学习复盘](week_13/session_03/README.md)；[04 综合工程分层与端到端契约测试](week_13/session_04/README.md)；[05 CI、发布、备份恢复与生产验收](week_13/session_05/README.md)；[06 模型适配、训练路线与课程总复盘](week_13/session_06/README.md) |

## 文内示例怎么运行

先阅读本节目标与核心概念，再运行完整代码块。对于标明“可离线运行”的块，在项目根目录输入：

```bash
uv run python -
```

粘贴代码块里的完整 Python 内容（不含 Markdown 围栏），按 Ctrl-D 结束输入，程序会一次执行并把结果打印到控制台。这种方法不创建脚本或结果文件。不要只复制一半函数；注明依赖前文的块须按顺序在同一个进程执行。

- `course: offline`：完整离线最小示例，含正常与失败/边界断言；通过仅说明教学夹具通过。
- `course: live`：会访问模型，本次未执行；使用 `common.llm` 和根配置。
- `course: optional`：LangGraph、MCP、FastAPI 的完整扩展示例，已核对官方资料和语法，尚未安装依赖或运行；按对应教案在学到时实践。
- 第 3～13 周的 33 个标准库最小示例已在 Python 3.12.0 的独立临时目录实际运行，并禁止网络连接；每节另有练习和未确认验收。
- 文件布局、SQLite 与 checkpoint 例子可能生成临时教学输入或业务状态，结束后清理；原始模型回答、耗时与统计仍只输出控制台，不保存结果报告。

既有第一、二周独立脚本继续保留；本次不新增后续全部实验脚本，不提前安装整套框架依赖。材料准备、离线验证、真实实验和学习验收详见学习进度。

## 环境准备

使用 Python 3.12 或更高版本，通过 uv 管理项目环境和依赖：

```bash
uv sync
```

根据实际学习内容添加依赖：

```bash
uv add <包名>
```

## 统一配置

所有周和 Session 的 Ollama 地址、默认模型、请求超时统一从根目录 [config.toml](config.toml) 读取：

```toml
[ollama]
host = "http://192.168.31.98:11434"
model = "qwen2.5:14b"
timeout = 300
```

端口按 Ollama 默认的 `11434` 配置。根据你提供的模型列表，也可以将 `model` 改为 `qwen2.5:3b`。模型运行在该服务器上，请确保服务可通过上述地址访问。

以后新增 Session 时复用 [模型调用模块](common/llm.py)。它通过 [配置读取模块](common/config.py) 获取配置，Session 只传入 prompt 和实验参数：

```python
from common.llm import create_llm_client

client = create_llm_client()
response = client.generate("用一句话解释 AI Agent。", temperature=0.0)
print(response.text)
```

调用关系：`Session → common.llm → 模型服务`。统一返回 `text`（回答）、`finish_reason`（结束原因）和 `output_tokens`（输出 token 数，可为空）。目前只实现 Ollama；后续接入 DeepSeek 或 OpenAI API 时，在调用模块增加适配器并扩展配置与客户端创建逻辑，实验的比较逻辑可以复用。不同服务对 `seed`、`top_k` 等参数的支持需要分别确认。

第二周开始使用 `client.chat(messages)` 传入带角色的消息；支持 `response_schema`、非流式工具请求及 `on_text` 文本流式展示。返回值新增 `input_tokens` 与 `tool_calls`，第一周的 `generate()` 用法不变。`context_tokens` 当前映射到 Ollama 的 `num_ctx`，其他服务接入时需明确能力差异。

建议在项目根目录用模块方式启动，例如 `uv run python -m week_01.session_01.main`，这样可以直接导入 `common`。现有第一周脚本也继续支持直接文件路径运行。

配置路径根据模块位置定位，不随终端当前目录变化。第一周实验的 `--host`、`--model`、`--timeout` 可临时覆盖配置，只影响本次运行；配置文件缺失或不合法时会明确报错。

## 目录约定

- 每周一个目录，使用两位编号：`week_01/`、`week_02/`……
- 每模块包含 4～7 个 Session，按上述目录取用；独立脚本按学习需要补充。
- 每个 Session 可以包含自己的 `README.md`、Python 示例和练习文件。
- 各周共用根目录的 Python 环境和依赖配置。
- 模型调用统一使用 `common.llm.create_llm_client()`，连接配置集中在 `config.toml`。
- 实验回答、耗时及统计默认只打印到控制台，不自动保存结果文件。

课程目录（保留现有代码，后续各节目前以文内示例为主）：

```text
AIAgentStudy/
├── pyproject.toml
├── config.toml
├── common/
│   ├── __init__.py
│   ├── config.py
│   └── llm.py
├── README.md
├── AGENTS.md
├── LEARNING_PROGRESS.md
├── LEARNING_PLAN.md
├── week_01/
│   ├── week1-llm-agent-basics.md
│   ├── session_01/
│   ├── session_02/
│   └── session_03/
├── week_02/
│   ├── README.md
│   ├── session_01/
│   │   ├── README.md
│   │   ├── probes.py
│   │   └── main.py
│   ├── session_02/
│   │   └── README.md
│   └── session_03/
│       ├── README.md
│       ├── cases.py
│       └── main.py
├── week_03/ ... week_13/
│   ├── README.md
│   ├── session_01/README.md
│   ├── session_02/README.md
│   └── session_03/README.md
└── tests/
    └── test_week02_protocol.py
```

第一周 Session 01 是 Ollama Temperature 对比实验，详见 [运行说明](week_01/session_01/README.md)。在项目根目录运行：

```bash
uv run python week_01/session_01/main.py
```

API 密钥等本地配置放在 `.env` 中，该文件已加入 Git 忽略规则。
