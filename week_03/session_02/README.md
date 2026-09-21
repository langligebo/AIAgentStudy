# 第 03 周 Session 02：工具执行器：契约、业务与权限

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

实现一个只允许已注册操作的执行器，并在创建模拟工单前完成参数、订单归属和审批核对。

## 前置知识与学习安排

上一节调用消息；第二周字段校验与业务校验。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

执行器处在模型和业务系统之间。推荐顺序是：定位注册工具 → 校验参数 → 核验可信身份及资源归属 → 核验业务前提和审批 → 执行 → 校验返回契约。返回也可能损坏，不能只校验模型输入。

身份应来自登录会话或本例传入的可信上下文，不是模型生成的 `user_id`。只读工具仍然需要访问控制。写工具还需核对授权内容；本课将审批绑定到 `(动作, 订单, 原因)`，任意字段变化都会使审批失效。

例子区分 `invalid_arguments`、`not_found_or_forbidden`、`approval_required` 与 `invalid_result`。对外合并不存在与越权，避免通过错误信息枚举他人的订单；内部可有脱敏原因码。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from dataclasses import dataclass

ORDERS = {"A100": "u1", "B200": "u2"}
TICKETS = {}
@dataclass(frozen=True)
class Context:
    user_id: str
    approved: tuple | None = None

def create_ticket(order_id, reason):
    ticket_id = f"T{len(TICKETS) + 1}"
    TICKETS[ticket_id] = {"order_id": order_id, "reason": reason}
    return {"ticket_id": ticket_id, "order_id": order_id}

REGISTRY = {"create_ticket": create_ticket}
def dispatch(name, args, context):
    if name not in REGISTRY:
        return {"ok": False, "error": "unknown_tool"}
    if (not isinstance(args, dict) or set(args) != {"order_id", "reason"}
        or any(type(v) is not str or not v.strip() for v in args.values())):
        return {"ok": False, "error": "invalid_arguments"}
    if ORDERS.get(args["order_id"]) != context.user_id:
        return {"ok": False, "error": "not_found_or_forbidden"}
    if context.approved != (name, args["order_id"], args["reason"]):
        return {"ok": False, "error": "approval_required"}
    result = REGISTRY[name](**args)
    if (not isinstance(result, dict) or set(result) != {"ticket_id", "order_id"}
        or type(result["ticket_id"]) is not str
        or result["order_id"] != args["order_id"]):
        # 已执行过写入，损坏的回包不能证明“未创建”。
        return {"ok": False, "error": "invalid_result", "outcome": "unknown"}
    return {"ok": True, "data": result}

args = {"order_id": "A100", "reason": "键盘损坏"}
ctx = Context("u1", ("create_ticket", "A100", "键盘损坏"))
assert dispatch("create_ticket", args, ctx)["ok"]
assert len(TICKETS) == 1
for case, changed, user in [
    ("越权", {**args, "order_id": "B200"}, ctx),
    ("更改原因", {**args, "reason": "改变主意"}, ctx),
    ("伪造身份字段", {**args, "user_id": "u2"}, ctx),
    ("未审批", args, Context("u1")),
]:
    result = dispatch("create_ticket", changed, user)
    assert not result["ok"]
    print(case, result)
assert len(TICKETS) == 1
REGISTRY["create_ticket"] = lambda **kw: {"ticket_id": 123, "order_id": kw["order_id"]}
assert dispatch("create_ticket", args, ctx)["outcome"] == "unknown"
print("PASS：正常创建 1 张；拒绝 4 类错误；识别损坏回包")
```

**预期现象：**只有已授权请求创建工单；四类非法请求不增加数量；输出契约失败标为 unknown。示例不含持久幂等，不能用于自动重复写入。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 画出执行器检查顺序，指出哪一项仅靠 Prompt 无法保证。
2. 将订单号改为空串、数字、不存在的订单；观察拒绝发生在执行前。
3. 替换工具返回字段，确认即使模型参数正确也会出现执行后结果未知；不要增加自动重试。

## 常见错误

- 从 args 读取 user_id 当可信身份。
- 批准某订单后允许模型任意改原因或订单。
- 输出字段不合法就宣布工单未创建。

## 思考题

只读工具为什么也需要权限检查？

<details>
<summary>参考答案（先自行作答）</summary>

读操作可能泄露其他客户订单、地址或政策范围。是否写入与能否访问是不同维度，身份与资源归属都应由服务验证。

</details>

## 验收标准

- [ ] 越权、未审批、参数变化都在写入前被拦截。
- [ ] 能区分输入拒绝与执行后返回损坏。
- [ ] 不在模型可控字段里决定用户身份。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 模型接入复用项目 common.llm；环境有 ollama 0.6.2，但公共客户端当前通过标准库 HTTP 实现，服务端版本和真实工具能力仍需实测。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Ollama 工具调用](https://docs.ollama.com/capabilities/tool-calling)

## 下一节衔接

下一节把这些错误带回决策过程，研究工具选错、分页和有限重试。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
