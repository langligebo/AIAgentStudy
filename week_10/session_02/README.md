# 第 10 周 Session 02：结构化追踪与实验复现

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

用任务和步骤标识串联请求、观察和状态，记录版本并避免在日志中泄露凭据。

## 前置知识与学习安排

结构化结果与评估分层；JSON。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

一条轨迹至少能回答：哪个任务、哪个步骤、调用了什么、得到什么状态、为何停止。每轮记录模型、Prompt、Skill、数据与流程版本以及参数；只记模型名字无法复现，因为服务、量化和运行条件也可能改变行为。

日志以事件组织，例如 tool_requested、tool_observed、task_finished。请求事件不是成功事件；只有观察和终态核对支持完成。耗时使用单调时钟，展示时间用于关联，不要用墙钟差作可靠耗时。

本课程默认 JSON 行只输出控制台。凭据与敏感用户正文尽量不进入事件：使用允许字段列表，比匹配所有可能的密钥名更容易审查。下面另外演示已知秘密脱敏；它只处理所声明结构，不能保证任意异常文本安全。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import json
from time import perf_counter

VERSIONS = {"model": "config.toml 中的模型，真实运行时读取", "prompt": "support-v1",
            "skill": "aftersales-v1", "data": "policy-v2", "flow": "loop-v1",
            "temperature": 0.0, "seed": 42}
SECRET_FIELDS = {"authorization", "api_key", "password", "cookie"}

def redact(value):
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in SECRET_FIELDS else redact(item)
                for key,item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value

private = {"headers": {"Authorization": "Bearer teaching-secret"}, "items": [{"api_key": "fake-key"}]}
safe = json.dumps(redact(private))
assert "teaching-secret" not in safe and "fake-key" not in safe
start = perf_counter()
events = [
    {"task_id": "task1", "step_id": 1, "event": "tool_requested", "tool": "get_order", "order_id": "A100"},
    {"task_id": "task1", "step_id": 1, "event": "tool_observed", "status": "ok", "source": "mock-orders"},
    {"task_id": "task1", "step_id": 2, "event": "task_finished", "status": "needs_approval"},
]
allowed = {"task_id", "step_id", "event", "tool", "order_id", "status", "source"}
for event in events:
    assert set(event) <= allowed
    print(json.dumps({**event, "versions": VERSIONS, "elapsed": perf_counter()-start}, ensure_ascii=False))
assert events[0]["event"] != "tool_observed"
assert events[-1]["status"] != "success"
assert len({(e["task_id"],e["step_id"]) for e in events}) == 2
print("PASS：请求与观察关联、脱敏、版本和非成功终态")
```

**预期现象：**控制台有三条关联事件，终态仍为 needs_approval；版本字段是教学夹具，真正模型版本须在运行时补齐。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 增加一次工具超时事件，确保不会打印原始请求头或整个异常响应。
2. 拿一条失败轨迹，依据 task_id、step_id 找出最后成功步骤和未确定的动作。
3. 补齐真实实验的客户端版本、模型标签或可用摘要、Prompt 版本、Skill 引用版本及资源条件，只保留必要简短证据。

## 常见错误

- 日志写了 requested 就认定 completed。
- 打印全部 messages，包括地址、密钥和内部文档。
- 记录版本为空却说实验可复现。

## 思考题

脱敏函数处理了 api_key，是否就能放心打印所有异常？

<details>
<summary>参考答案（先自行作答）</summary>

不能。异常可能包含其他字段名、URL 参数或自由文本秘密。应控制事件字段和错误码，避免采集不必要敏感内容，再对已知字段脱敏。

</details>

## 验收标准

- [ ] 可从事件顺序重建动作。
- [ ] 日志能区分请求、观察和终态。
- [ ] 凭据不出现在示例输出，版本缺项明确。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Agent 评估的任务、轨迹与结果](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## 下一节衔接

下一节用同样的版本清单做重复对照和回归门槛。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
