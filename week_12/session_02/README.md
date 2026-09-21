# 第 12 周 Session 02：并发、超时、限流与取消传播

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

限制并发和总耗时，仅对可重试读取退避，并在取消后停止启动后续动作。

## 前置知识与学习安排

asyncio、只读与写入、幂等和 unknown。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

并发限制控制同时占用资源的操作数，限流控制时间窗口内的请求速率，二者不相同。总 deadline 应覆盖排队、退避和所有尝试；每次调用 timeout 不代表整任务有时间上限。

读取的 429 或临时错误可有限重试，遵循 Retry-After，并加入退避与必要抖动避免同时冲击服务。参数错误和权限错误不该原样重试。写请求超时先按第 8 周核对或幂等处理，不能直接套读取重试器。

CancelledError 通常应在清理后继续抛出。取消 asyncio.to_thread 外层等待并不停止已运行的同步线程，也不能撤回远端请求；当前公共 LLM 客户端是同步的，后续服务化需明确线程或异步适配及底层超时，不能宣称取消已终止推理。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import asyncio

class RateLimited(Exception):
    pass

async def main():
    semaphore = asyncio.Semaphore(2)
    active = peak = 0
    async def bounded_read():
        nonlocal active, peak
        async with semaphore:
            active += 1
            peak = max(peak, active)
            try:
                await asyncio.sleep(0)
                return "order"
            finally:
                active -= 1
    assert await asyncio.gather(*(bounded_read() for _ in range(5))) == ["order"] * 5
    assert peak <= 2 and active == 0
    async def retry_read(outcomes):
        for attempt, outcome in enumerate(outcomes[:3]):
            try:
                if outcome == 429:
                    raise RateLimited()
                return "ok"
            except RateLimited:
                if attempt == min(len(outcomes), 3) - 1:
                    return "rate_limit_exhausted"
                await asyncio.sleep(0.001 * 2**attempt) # 教学退避；线上还要读取 Retry-After。
    assert await retry_read([429, 200]) == "ok"
    assert await retry_read([429, 429, 429]) == "rate_limit_exhausted"
    try:
        async with asyncio.timeout(0.01):
            await asyncio.Event().wait()
    except TimeoutError:
        print("deadline_exceeded")
    else:
        raise AssertionError("应超时")
    started = asyncio.Event()
    events = []
    async def job():
        try:
            started.set()
            await asyncio.Event().wait()
            events.append("write_started")
        finally:
            events.append("cleanup")
    worker = asyncio.create_task(job())
    await started.wait()
    worker.cancel()
    try:
        await worker
    except asyncio.CancelledError:
        events.append("cancel_propagated")
    assert events == ["cleanup", "cancel_propagated"]
    print("peak", peak, events)
    print("PASS：并发、限流恢复及耗尽、超时、取消阻止后续动作")

asyncio.run(main())
```

**预期现象：**并发峰值最多 2；一次 429 后读取成功，连续三次则停止；deadline 超时；取消传播且没有 write_started。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 将超时范围移到包含排队与重试的外层，检查总耗时受控。
2. 加入写入回包丢失，断言没有进入 retry_read，而是使用幂等键核对。
3. 对服务接口制造重复提交、取消和客户端断开，明确“断开状态连接”与“显式取消”的不同契约。

## 常见错误

- Semaphore 被当作每秒请求限流。
- 每次重试都有 30 秒超时却允许任务无限延长。
- 吞掉 CancelledError 后继续创建工单。

## 思考题

取消正在等待同步模型请求的协程，为什么不能保证模型停止计算？

<details>
<summary>参考答案（先自行作答）</summary>

取消通常只影响本地等待；同步线程和远端推理可能继续。需要客户端支持的取消机制、连接处理与服务端协议，并核对已发生动作；本项目当前客户端没有通用取消协议。

</details>

## 验收标准

- [ ] 并发与总 deadline 有明确边界。
- [ ] 读取重试有限，写入未知单独处理。
- [ ] 取消后无新动作且清理执行。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 服务示例固定 FastAPI 0.120.0、Uvicorn 0.38.0；Pydantic 使用现有 2.13.5，未验证这组服务依赖的联合运行，安装时须核对锁定结果。Docker 演练未执行。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [FastAPI 后台任务及边界](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [FastAPI 0.120.0](https://pypi.org/project/fastapi/0.120.0/)
- [Uvicorn 0.38.0](https://pypi.org/project/uvicorn/0.38.0/)
- [asyncio 取消与超时](https://docs.python.org/3.12/library/asyncio-task.html)
- [Dockerfile 指令](https://docs.docker.com/reference/dockerfile/)

## 下一节衔接

下一节组织配置、健康检查和版本发布回退演练。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
