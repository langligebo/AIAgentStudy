# 第 09 周 Session 02：动态计划、重新规划与 Skill 复用

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

校验模型提出的计划，在观察或目标变化后废止过期步骤，并限制重新规划成本。

## 前置知识与学习安排

第 5 周 Skill、第 4 周任务版本与执行预算。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

计划是可修改的动作候选，不是执行授权。可以让模型提出查订单、查政策、给方案，再由运行时校验工具名、依赖、目标版本、预算和审批。允许步骤并不代表输入和权限已通过，执行时仍走执行器。

每次环境观察可能否定计划前提；用户改成“只查询进度”时，原退货计划中的写步骤应失效。记录 goal_revision，让旧计划不能在新目标上继续；重新规划也消耗预算，不能无限用“再想一次”回避终止。

Skill 提供任务方法，计划器可以引用一个已允许 Skill 的步骤。宿主仍负责加载和执行。下面以确定性计划器讲解协议，真实模型输出可用第二周结构化校验后转换成同样的数据；不把模拟 plan() 当作模型推理。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
ALLOWED = {"get_order", "get_policy", "propose", "create_ticket"}

def plan(goal, revision):
    steps = ["get_order"] if goal == "查询状态" else ["get_order", "get_policy", "propose"]
    return {"revision": revision, "skill": "aftersales" if goal == "退货" else None, "steps": steps}

def validate(candidate, revision, budget):
    if candidate["revision"] != revision:
        return "stale_plan"
    if not candidate["steps"] or len(candidate["steps"]) > budget:
        return "budget"
    seen = set()
    for step in candidate["steps"]:
        if step not in ALLOWED:
            return "unknown_action"
        if step == "get_policy" and "get_order" not in seen:
            return "dependency_error"
        if step == "create_ticket":
            return "requires_separate_approval"
        seen.add(step)
    return "valid"

revision = 1
old_plan = plan("退货", revision)
assert validate(old_plan, revision, 3) == "valid"
revision += 1  # 用户改为只查询，执行前再校验。
assert validate(old_plan, revision, 3) == "stale_plan"
new_plan = plan("查询状态", revision)
assert new_plan["steps"] == ["get_order"]
assert validate(new_plan, revision, 3) == "valid"
assert validate({**new_plan, "steps": ["get_policy"]}, revision, 3) == "dependency_error"
assert validate({**new_plan, "steps": ["shell"]}, revision, 3) == "unknown_action"
assert validate({**new_plan, "steps": ["create_ticket"]}, revision, 3) == "requires_separate_approval"
assert validate(old_plan, 1, 1) == "budget"
print("旧计划：", old_plan, "新计划：", new_plan)
print("PASS：重规划、旧版本拒绝、依赖、白名单、写入和预算")
```

**预期现象：**用户改目标后旧计划被拒绝，新计划只查询；缺依赖、未知动作、超预算与未审批写入均被阻止。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## RAG 补充：查询分解与 Agentic RAG

把“退货资格与赠品处理”拆成两个取证需求，记录每一项是否有来源支持。固定代码总查两次属于 Workflow；若模型根据缺口决定改问法、换受控来源、补查、追问或结束，才是本课程讨论的 Agentic RAG。运行时始终掌握工具白名单、身份、预算和终态检查。

Multi-Query 是同意图多种表达，查询分解是分别解决必要子问题，Step-Back 是先提取更一般的原则；定义和对照见[第六周 Session 02](../../week_06/session_02/README.md)。子问题间有依赖时必须按序执行，不能因为是多个查询就并行。

下面使用固定决策夹具验证运行时：第一轮只查到退货，第二轮补齐赠品后才结束；重复动作或未取证就完成都被拒绝。它没有真实模型自主决策，不能作为 Agent 效果证明。

```python
# course: offline
REQUIRED = {"return_rule", "gift_rule"}
INDEX = {"退货资格": {"return_rule": "policy-v2#return"},
         "赠品处理": {"gift_rule": "policy-v2#gift"}}

def run(decisions, budget=2):
    evidence, seen, trace = {}, set(), []
    calls = 0
    for action, query in decisions:
        if action == "finish":
            status = "answered" if REQUIRED <= evidence.keys() else "insufficient_evidence"
            return status, trace
        if action != "search":
            return "unknown_action", trace
        if calls >= budget:
            return "budget_exhausted", trace
        if query in seen:
            return "no_progress", trace
        seen.add(query)
        calls += 1
        observed = INDEX.get(query, {})
        evidence.update(observed)
        trace.append({"query": query, "observed": observed, "missing": sorted(REQUIRED-evidence.keys())})
    return "incomplete", trace

normal = [("search", "退货资格"), ("search", "赠品处理"), ("finish", None)]
status, trace = run(normal)
assert status == "answered" and trace[0]["missing"] == ["gift_rule"]
assert run([("search", "退货资格"), ("finish", None)])[0] == "insufficient_evidence"
assert run([("search", "无关"), ("search", "无关")])[0] == "no_progress"
assert run(normal, budget=1)[0] == "budget_exhausted"
print(status, trace)
print("PASS：补齐证据、提前完成拒绝、无进展与预算停止")
```

真实实验使用公共 LLM 客户端生成下一动作，并把执行器返回的证据与缺口交回模型；参数须按第三周校验，每次搜索保持当前用户 ACL。模型只说“足够了”不能覆盖未解决的必需子问题。用户改订单或目标时，继承本节 goal_revision 检查，旧计划及证据需重验。

对照固定查询 Workflow 和动态补检索：统计必要条款覆盖、正确拒答、无依据结论、查询/模型调用次数与等待。接到第十周消融实验，不能用“Agentic”名称直接推断优于普通 RAG。[知识清单](../../week_06/RAG_ROADMAP.md)

补充验收：能解释谁选择补查；重复/预算耗尽可退出；一项缺证据时不回答成全部确定。离线块只需 Python 3.12；真实查询生成和知识库检索未运行。

## 实验步骤与练习

1. 加入最大重规划次数 2，连续制造新观察，第三次应交回用户或终止。
2. 让真实模型以结构化对象提出 steps，只使用允许枚举，仍保留程序校验。
3. 把 Skill 版本记入计划，并在版本切换时决定哪些未执行步骤需重新确认。

## 常见错误

- 拿到计划就逐项执行，不检查状态是否变化。
- 把计划中的“用户同意”作为审批证据。
- 重规划无限消耗模型调用。

## 思考题

计划的步骤都在白名单里，是否就能保证业务正确？

<details>
<summary>参考答案（先自行作答）</summary>

不能。合法名称还可能有错误参数、错误依赖、越权资源或缺审批；执行前的业务契约不可省略。

</details>

## 验收标准

- [ ] 计划版本绑定目标版本。
- [ ] 用户改目标后旧写步骤失效。
- [ ] 重新规划和执行都有独立预算。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Python asyncio 任务与并发](https://docs.python.org/3.12/library/asyncio-task.html)

## 下一节衔接

下一节用真实终态验收计划，并只做有限修正。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
