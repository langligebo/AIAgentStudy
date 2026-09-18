# AI Agent 开发学习

使用 Python 学习 AI Agent 开发，按周组织内容，每周包含若干 Session。

## 学习入口

- [13 周学习计划](LEARNING_PLAN.md)：每周 3 个 Session，包含知识点、实践任务和验收标准。
- [第一周学习笔记](week_01/week1-llm-agent-basics.md)：LLM 基础、Agent 与工作流、Prompt 实验。
- [第一周 Session 01](week_01/session_01/README.md)：Ollama Temperature 对比实验。
- [第一周 Session 02](week_01/session_02/README.md)：单次模型调用、Workflow 与 Agent 的区别及架构练习。
- [第一周 Session 03](week_01/session_03/README.md)：Prompt 对比、Few-shot 与三层输出校验。

主线使用“知识库客服助手”贯穿学习，从模型调用、工具和 Skill，逐步加入检索、记忆、状态恢复、评估、安全及服务化。后续周和 Session 随学习进度创建；课程验收以实际实验记录为准。

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

建议在项目根目录用模块方式启动，例如 `uv run python -m week_01.session_01.main`，这样可以直接导入 `common`。现有第一周脚本也继续支持直接文件路径运行。

配置路径根据模块位置定位，不随终端当前目录变化。第一周实验的 `--host`、`--model`、`--timeout` 可临时覆盖配置，只影响本次运行；配置文件缺失或不合法时会明确报错。

## 目录约定

- 每周一个目录，使用两位编号：`week_01/`、`week_02/`……
- 每周的 Session 按需创建：`session_01/`、`session_02/`……
- 每个 Session 可以包含自己的 `README.md`、Python 示例和练习文件。
- 各周共用根目录的 Python 环境和依赖配置。
- 模型调用统一使用 `common.llm.create_llm_client()`，连接配置集中在 `config.toml`。
- 实验回答、耗时及统计默认只打印到控制台，不自动保存结果文件。

目前已创建第一周目录：

```text
AIAgentStudy/
├── pyproject.toml
├── config.toml
├── common/
│   ├── __init__.py
│   ├── config.py
│   └── llm.py
├── README.md
├── LEARNING_PLAN.md
└── week_01/
    ├── week1-llm-agent-basics.md
    ├── session_01/
    │   ├── README.md
    │   └── main.py
    ├── session_02/
    │   └── README.md
    └── session_03/
        ├── README.md
        ├── cases.py
        ├── prompts.py
        └── main.py
```

第一周 Session 01 是 Ollama Temperature 对比实验，详见 [运行说明](week_01/session_01/README.md)。在项目根目录运行：

```bash
uv run python week_01/session_01/main.py
```

API 密钥等本地配置放在 `.env` 中，该文件已加入 Git 忽略规则。
