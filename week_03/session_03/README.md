# 第 03 周 Session 03：工具错误、选择与重试边界

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

把协议错误、业务无结果、部分成功分开，并按动作风险决定能否重试。

## 前置知识与学习安排

工具注册表、结构化结果、可信上下文。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

工具选择错误发生在“该调用哪个工具”；参数错误发生在“用什么参数”；执行错误发生在选对且输入有效之后。三者要分开统计。相似工具需要用输入对象和用途区分，例如按订单查物流与按产品查政策。

`ok=True, items=[]` 可以表示查无匹配，和网络失败不同。分页有 `next_cursor` 时只收到一部分；页面预算耗尽应报告 `partial`，不能宣称“所有订单”。每页都重新做访问过滤，不能仅保护第一页。

只读操作的临时失败可在总预算内重试；参数错误应修参数而非原样重发。写入超时可能已经成功，应返回 `unknown` 并核对状态或使用受服务端保障的幂等键。固定最多重试次数只限制成本，不能解决重复写入。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
CATALOG = {"get_order": "按 order_id 查状态", "get_policy": "按 product 查规则"}
CASES = [
    ("get_order", "get_order", True),
    ("get_policy", "get_order", True),  # 故意选错工具
    ("get_order", "get_order", False), # 故意传错参数
]
selection = sum(expected == actual for expected, actual, _ in CASES)
arguments = sum(valid for _, _, valid in CASES)
end_to_end = sum(expected == actual and valid for expected, actual, valid in CASES)
print("工具正确/参数正确/端到端：", selection, arguments, end_to_end, "分母", len(CASES))

def fetch_all(page_budget):
    pages = {None: {"items": ["A100"], "next_cursor": "p2"},
             "p2": {"items": ["A101"], "next_cursor": None}}
    items, cursor = [], None
    for _ in range(page_budget):
        page = pages[cursor]
        items.extend(page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            return {"status": "complete", "items": items}
    return {"status": "partial", "items": items, "next_cursor": cursor}

def policy(kind, error, attempt, limit=2):
    if kind == "write" and error == "timeout":
        return "reconcile_unknown"
    if error == "invalid_arguments":
        return "repair_arguments"
    if kind == "read" and error == "timeout" and attempt < limit:
        return "retry_with_backoff"
    return "stop"

assert fetch_all(2)["status"] == "complete"
assert fetch_all(1)["status"] == "partial"
assert policy("write", "timeout", 1) == "reconcile_unknown"
assert policy("read", "timeout", 1) == "retry_with_backoff"
assert policy("read", "timeout", 2) == "stop"
assert policy("read", "invalid_arguments", 1) == "repair_arguments"
print(fetch_all(1), fetch_all(2))
print("PASS：分页完整与截断、可重试读取与未知写入分开")
```

**预期现象：**三个教学样本中工具正确 2、参数有效 2、两项同时正确 1；单页预算返回 partial，两页完整。这里评估的是手写夹具，不是模型选择能力。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 给固定案例加一条不需要工具的问候；预期工具为 none，避免强行调用。
2. 为分页加入重复游标故障，限制重复页面，不能死循环。
3. 将本周执行器接入第 1 节真实工具请求，用同一开发集分别记选择、参数和任务结果；本次仅准备操作步骤。

## 常见错误

- 仅在收到成功响应的样本上计算任务成功率。
- 把空列表、超时、只拿到第一页都写成“没有订单”。
- 写请求超时就自动重试两次。

## 思考题

设置最多重试两次，能避免重复创建工单吗？

<details>
<summary>参考答案（先自行作答）</summary>

不能。第一次可能已创建但响应丢失。需要查询业务状态或服务端幂等保证；无法核对时保持结果未知。次数限制防止无限循环，不证明业务安全。

</details>

## 验收标准

- [ ] 同一批样本分开统计选择、参数、端到端结果。
- [ ] 部分结果附带截断状态。
- [ ] 写入超时触发核对而不是直接重发。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

工具协议说明如何表达请求，执行器决定能否执行，错误与选择评估解释失败发生在哪一层。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 能把工具声明、模型提出的调用和程序返回的观察关联起来，处理一轮中的多个调用。 |
| [Session 02](../session_02/README.md) | 实现一个只允许已注册操作的执行器，并在创建模拟工单前完成参数、订单归属和审批核对。 |
| [Session 03](../session_03/README.md) | 把协议错误、业务无结果、部分成功分开，并按动作风险决定能否重试。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 模型接入复用项目 common.llm；环境有 ollama 0.6.2，但公共客户端当前通过标准库 HTTP 实现，服务端版本和真实工具能力仍需实测。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Ollama 工具调用](https://docs.ollama.com/capabilities/tool-calling)

## 下一节衔接

本节完成本模块前三节的阶段复盘，接着学习新增的[Session 04](../session_04/README.md)；原下一模块安排顺延，历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
