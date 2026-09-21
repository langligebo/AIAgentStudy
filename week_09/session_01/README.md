# 第 09 周 Session 01：固定工作流、路由与并行依赖

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_08/session_04/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

为明确业务流程选择串行、条件路由或独立并行，并用事件证明依赖顺序。

## 前置知识与学习安排

Python async/await 基础；第 4 周流程与状态。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

Workflow 的路径由代码规定，模型可以负责分类或抽取。规则明确的客服流程常适合路由：咨询去知识问答，售后去订单核验，缺信息先追问。无需为每个任务都增加自由规划。

并行的前提是输入已具备且动作独立。例如根据已知产品查询政策与查询物流可独立；根据订单返回的 product 才能查政策时，政策查询必须等订单结果。写操作与授权、版本或读取结果有依赖，不能为了快而并发。

asyncio.gather 便于并行读取。异常处理需明确：全部必需的分支失败要终止；允许部分结果时标明缺口。取消其他协程不保证远程请求撤销。例子使用 asyncio.sleep(0) 让出执行权，不代表真实网络延迟基准。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import asyncio

async def workflow(intent, order_id, policy_fails=False):
    events = []
    if intent == "greeting":
        return {"status": "answered", "events": ["greeting"]}
    if not order_id:
        return {"status": "waiting_user", "events": ["ask_order_id"]}
    events.append("order:start")
    await asyncio.sleep(0)
    product = "keyboard"
    events.append("order:end")
    async def policy():
        events.append("policy:start")
        await asyncio.sleep(0)
        if policy_fails:
            raise RuntimeError("policy_unavailable")
        return {"product": product, "days": 7}
    async def logistics():
        events.append("logistics:start")
        await asyncio.sleep(0)
        return "delivered"
    results = await asyncio.gather(policy(), logistics(), return_exceptions=True)
    failed = any(isinstance(x, Exception) for x in results)
    return {"status": "partial" if failed else "ready_for_proposal", "results": results, "events": events}

async def main():
    normal = await workflow("aftersales", "A100")
    assert normal["status"] == "ready_for_proposal"
    for event in ("policy:start", "logistics:start"):
        assert normal["events"].index("order:end") < normal["events"].index(event)
    assert (await workflow("aftersales", None))["status"] == "waiting_user"
    assert (await workflow("aftersales", "A100", True))["status"] == "partial"
    assert (await workflow("greeting", None))["events"] == ["greeting"]
    print(normal)
    print("PASS：依赖顺序、独立读取、追问、部分失败、路由")

asyncio.run(main())
```

**预期现象：**订单先完成，政策与物流读取再开始；政策失败返回 partial，不进入可执行退货结论。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 把物流改为需要订单查询返回的物流号，明确并行起点。
2. 为每条分支规定失败是否允许继续；如果政策缺失，不得进入自动写工单。
3. 在真实网络实验中再测串并行耗时，保持相同调用数量与输入，不要把 sleep(0) 作为性能证据。

## 常见错误

- 所有工具都放进 gather。
- 一条分支失败仍报告全部完成。
- 为了使用 Agent 把确定规则也交给模型随机决策。

## 思考题

工作流里有模型分类和并行调用，它就变成 Agent 了吗？

<details>
<summary>参考答案（先自行作答）</summary>

不一定。若下一步及分支由代码预先确定，它仍是 Workflow；是否使用模型或并行不是判断依据。

</details>

## 验收标准

- [ ] 依赖边能解释业务需要。
- [ ] 仅独立读取并行。
- [ ] 部分失败不会触发无依据写入。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Python asyncio 任务与并发](https://docs.python.org/3.12/library/asyncio-task.html)

## 下一节衔接

下一节把不确定路径交给受约束的计划器，并处理用户改目标。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_08/session_04/README.md) · [下一节](../session_02/README.md)
