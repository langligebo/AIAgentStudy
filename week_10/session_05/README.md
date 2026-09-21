# 第 10 模块 Session 05：追踪接入、线上反馈与 RAGAS 适配

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

把本地事件映射成可关联的观测数据，并将评分工具接到同一个模型边界。

## 前置知识与学习安排

W10 S01～04、公共客户端与任务标识。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

Trace 表示一次任务，Span 表示模型、检索或工具步骤，父子关系解释耗时发生在哪。日志记录离散事件，metrics 汇总比例/延迟；它们互补而不互相替代。跨线程、队列、服务需要传播上下文，不能仅靠打印时间猜关联。

OpenTelemetry 提供标准接口和导出方式，实验先用控制台 exporter。指标标签不要放订单号、全文或用户标识，防止高基数与数据泄露；请求 ID 留在有访问控制的追踪中。Token usage 缺失应为 unknown；缓存命中和重试要单独计量。

线上质量要考虑用户反馈偏差、延迟业务结果和数据漂移。shadow 模式不得重复执行写操作，canary 要有清晰回退门槛。SLO 是一段时间内可量化的承诺，如有效任务的成功率、P95 完成时间；既看技术成功，也看真实任务成功。

RAGAS 是评价实现，不是正确性真值。固定版本、样本字段、评分模型和提示；评分失败/NaN 不得按满分统计。下方适配复用 common.llm，限制调用预算，不能直接把项目 LLMResponse 当 SDK 返回类型。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
from contextlib import contextmanager
from time import perf_counter
from uuid import uuid4
EVENTS = []
@contextmanager
def span(name, parent=None):
    sid = uuid4().hex; start = perf_counter(); status = "ok"
    try: yield sid
    except Exception:
        status = "error"; raise
    finally:
        EVENTS.append({"span_id":sid,"parent":parent,"name":name,"status":status,
                       "duration":perf_counter()-start})

with span("task") as root:
    with span("retrieve",root): pass
    try:
        with span("tool",root): raise TimeoutError("private text must not be logged")
    except TimeoutError: pass
assert len(EVENTS) == 3
assert all(e["duration"] >= 0 for e in EVENTS)
assert sum(e["status"]=="error" for e in EVENTS) == 1
assert "private" not in str(EVENTS)
assert all(e["parent"]==root for e in EVENTS if e["name"] != "task")
print("PASS：父子关联、错误与最小字段；非 OpenTelemetry SDK", EVENTS)
```

**预期现象：**子步骤关联到任务，错误保留，私有异常正文不输出。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。

## OpenTelemetry 控制台扩展：未安装、未运行

独立执行下块：`uv run --with 'opentelemetry-api==1.38.0' --with 'opentelemetry-sdk==1.38.0' python -`。版本作为教学基线；不需要 Collector、不导出文件、不连接外部平台。上方标准库 trace 夹具不能代替此 SDK 实验。

<!-- verify: external -->
```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
tracer = provider.get_tracer("course.agent", "1.0")
try:
    with tracer.start_as_current_span("task"):
        with tracer.start_as_current_span("retrieve") as child:
            child.set_attribute("course.evidence_count", 2)
        with tracer.start_as_current_span("tool", record_exception=False) as child:
            try:
                raise TimeoutError("教学故障")
            except TimeoutError:
                child.set_status(Status(StatusCode.ERROR, "timeout"))
                child.set_attribute("course.result", "unknown")
    provider.force_flush()
finally:
    provider.shutdown()
```

预期控制台出现同一 trace 下的 task/retrieve/tool，tool 为 ERROR。这里的根 span 只覆盖编排结束，业务是否成功仍由业务验收器判定。扩展练习将上下文跨队列传递，并测试断链与脱敏；不要把用户正文或令牌放进 attributes。

## RAGAS SDK 适配练习：未安装、未调用模型

固定历史教学 API `ragas==0.2.15`，避免将 stable 文档的新接口与旧例混用。到本节从项目根执行 `uv run --with 'ragas==0.2.15' python -`，完整复制下块。依赖解析和运行兼容仍需实际环境验证；本次只有语法与对应 tag 源码核对。此例只接 Faithfulness，不包含需要 Embedding 的其他指标。

评分器可能发出多次模型请求；这里共用 8 次上限，SDK 网络重试限制为一次尝试，格式修复也受总调用数约束。`asyncio.to_thread` 取消不强制终止同步 HTTP，请求超时仍由公共配置控制。样本是课程公开模拟数据。

<!-- verify: live-external -->
```python
import asyncio
from threading import Lock
from langchain_core.outputs import Generation, LLMResult
from ragas import SingleTurnSample
from ragas.llms import BaseRagasLLM
from ragas.metrics import Faithfulness
from ragas.run_config import RunConfig
from common.llm import create_llm_client

class CourseJudge(BaseRagasLLM):
    def __init__(self):
        super().__init__()
        self.client = create_llm_client()
        self.left = 8
        self.lock = Lock()
        self.set_run_config(RunConfig(max_retries=1))
    def generate_text(self, prompt, n=1, temperature=0.0, stop=None, callbacks=None):
        if n != 1 or stop: raise ValueError("adapter only supports n=1 without stop sequences")
        with self.lock:
            if self.left <= 0: raise RuntimeError("judge_budget")
            self.left -= 1
        r = self.client.generate(prompt.to_string(), temperature=temperature or 0.0, max_tokens=1024)
        if r.finish_reason != "stop" or not r.text.strip(): raise RuntimeError("judge_incomplete")
        return LLMResult(generations=[[Generation(text=r.text, generation_info={"finish_reason":r.finish_reason})]])
    async def agenerate_text(self, prompt, n=1, temperature=None, stop=None, callbacks=None):
        return await asyncio.to_thread(self.generate_text, prompt, n, temperature, stop, callbacks)
    def is_finished(self, response):
        return all(g.generation_info.get("finish_reason") == "stop" for row in response.generations for g in row)

async def main():
    scorer = Faithfulness(llm=CourseJudge())
    for answer in ["K1 已使用不适用普通退货。", "K1 使用一年后仍可无条件退货。"]:
        sample = SingleTurnSample(user_input="K1 用过能退吗？", response=answer,
                                  retrieved_contexts=["K1 已使用不适用普通退货。"])
        score = await scorer.single_turn_ascore(sample)
        print(answer, score)
asyncio.run(main())
```

## 实验步骤与练习

1. 把现有控制台事件映射到 trace/span，保留 task_id 与 action_id 的业务关联。
2. 按本节固定 1.38.0 的 OTel 扩展在隔离环境运行，先导出到控制台，再按实际依赖锁记录版本。
3. 用下方 RAGAS 适配先给正常/虚构答案评分，再与人工支持标签比较，不预设模型分数。
4. 设计只读 shadow 与小流量发布，保留取消、超时、数据漂移和反馈迟到的处理。

## 常见错误

- 把追踪系统当聊天全文仓库。
- 评分失败从分母删除。
- 线上影子实验再次创建工单。

## 思考题

HTTP 200 比例接近 100%，能证明 Agent 可用吗？

<details>
<summary>参考答案（先自行作答）</summary>

不能。请求可以技术完成而任务失败、引用错误或产生错误副作用；需要业务终态与分层指标。

</details>

## 验收标准

- [ ] 可跨步骤定位耗时与失败，同时不泄露数据。
- [ ] 真实评分通过公共客户端且有预算。
- [ ] 观测、线上质量与回退门槛相连接。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [Ragas 0.2.15 适配基类](https://github.com/explodinggradients/ragas/blob/v0.2.15/src/ragas/llms/base.py)
- [Ragas 0.2.15 Faithfulness](https://github.com/explodinggradients/ragas/blob/v0.2.15/src/ragas/metrics/_faithfulness.py)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_04/README.md) · [下一节](../../week_11/session_01/README.md)
