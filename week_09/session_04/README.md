# 第 09 模块 Session 04：多 Agent 分工、交接与协作评估

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

能选择单 Agent、主管分工或交接模式，并把总预算、证据和责任传下去。

## 前置知识与学习安排

任务状态、工具边界、规划与结果验证。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

多个角色 Prompt 不自动构成有效协作。先判断任务能否拆成独立、可验收的子任务：订单核查与政策研究可分工，但写入审批仍由统一执行器处理。主管模式汇总子任务结果；handoff 转移对话处理责任；并行委员会比较多个结果。每种都增加沟通、状态一致性和成本问题。

交接包应包括目标、所需输出、已知事实及来源、约束、截止时间、剩余预算、可信身份作用域与返回地址。不能把所有历史和凭据复制给每个子 Agent。子任务返回结构化结果和证据，主管要处理冲突、部分失败和来源缺失，不以投票替代事实核验。

总预算是共享资源：预分配或原子扣减，避免每个子 Agent 都得到完整预算。取消与目标更正要使旧任务输出失效；只有父任务可以决定接纳结果，不允许子任务无限递归委派。

下例是确定性协作调度夹具，验证预算和交接；真实比较需要相同模型、工具、任务集下运行单 Agent 与多 Agent，统计成功率、时间、总 token、重复劳动和冲突率。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
from dataclasses import dataclass
@dataclass
class Budget:
    left: int
    def reserve(self, amount):
        if amount <= 0 or amount > self.left: raise ValueError("budget")
        self.left -= amount

def accept(packet, result, current_revision):
    if packet["revision"] != current_revision: return "stale"
    if result["task_id"] != packet["task_id"]: return "wrong_task"
    if not result.get("evidence"): return "unverified"
    if result.get("scope") != packet["scope"]: return "scope_mismatch"
    return "accepted"

budget = Budget(5); budget.reserve(2); budget.reserve(2)
assert budget.left == 1
try: budget.reserve(2)
except ValueError: pass
else: raise AssertionError("overspend")
packet = {"task_id":"policy-1", "revision":1, "scope":"u1"}
result = {"task_id":"policy-1", "evidence":["p1"], "scope":"u1"}
assert accept(packet,result,1) == "accepted"
assert accept(packet,result,2) == "stale"
assert accept(packet,{**result,"evidence":[]},1) == "unverified"
assert accept(packet,{**result,"scope":"u2"},1) == "scope_mismatch"
print("PASS：总预算、交接关联、旧目标与无证据拒绝")
```

**预期现象：**两个子任务不能超额分配总预算；旧任务和缺证据结果不进入主管答案。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 为客服任务画出单 Agent、主管分工、handoff 三种责任图。
2. 设计订单/政策两个子任务，明确谁保留对话责任、谁能申请写操作。
3. 接公共模型分别跑两种实现，保持总预算相同，不给多 Agent 免费额外轮次。
4. 测试子任务超时、互相矛盾、返回别人的证据和父任务取消，所有结果经过主管校验。

## 常见错误

- 多 Agent 数量越多越好。
- 把子 Agent 自述成功当业务完成。
- 每个分支独立重试导致成本相乘。

## 思考题

三个子 Agent 都同意退款，是否可以跳过审批？

<details>
<summary>参考答案（先自行作答）</summary>

不可以。建议数量不改变权限和事实。退款资格由政策与订单证据核验，执行仍需授权。

</details>

## 验收标准

- [ ] 能解释至少两种协作模式及不适用情况。
- [ ] 交接包含来源/约束且不泄露凭据。
- [ ] 用真实任务指标判断协作是否值得。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [多 Agent 研究系统的实践](https://www.anthropic.com/engineering/multi-agent-research-system)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../session_05/README.md)
