# 第 12 周 Session 01：任务式 FastAPI 接口

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_11/session_05/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

用提交、查询和取消接口管理长任务，区分 HTTP 请求成功与业务任务完成。

## 前置知识与学习安排

任务状态、可信身份、异步基础。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

长任务接口可以先返回 202 和 task_id，客户端再查询状态或订阅进度。202 只表示接收，不表示已创建工单。任务记录和身份要绑定；查询与取消同样检查 owner，不能靠随机 ID 当访问控制。

取消是请求停止，需在动作前检查并传播到执行中的协程；如果已发出写请求，要记录并核对副作用。流式进度只展示事件，不提供成功证明。断开流也不一定取消任务，应由产品接口定义。

FastAPI 的进程内后台执行适合本机教学，但不是持久任务队列；多个 worker 不共享内存字典，重启会丢状态。下面先测状态核心，再给真实 HTTP 示例。CLI 与 HTTP 应调用相同任务服务，而不是各复制一套业务。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from uuid import uuid4

tasks, keys = {}, {}

def submit(owner, order_id, key):
    identity = (owner, key)
    if identity in keys:
        existing = tasks[keys[identity]]
        if existing["order_id"] != order_id:
            raise ValueError("idempotency_conflict")
        return existing["id"]
    task_id = str(uuid4())
    tasks[task_id] = {"id": task_id, "owner": owner, "order_id": order_id,
                      "status": "queued", "events": ["accepted"]}
    keys[identity] = task_id
    return task_id

def get(owner, task_id):
    task = tasks.get(task_id)
    if task is None or task["owner"] != owner:
        raise PermissionError("not_found_or_forbidden")
    return task

def cancel(owner, task_id):
    task = get(owner, task_id)
    if task["status"] in {"queued", "running"}:
        task["status"] = "cancelled"
        task["events"].append("cancelled_before_next_action")

def tick(task_id):
    task = tasks[task_id]
    if task["status"] == "cancelled":
        return
    task["events"].append("read_order")
    task["status"] = "success"  # 这里只完成模拟读取，无外部写入。

tid = submit("u1", "A100", "request1")
assert submit("u1", "A100", "request1") == tid
assert get("u1", tid)["status"] == "queued"
tick(tid)
assert get("u1", tid)["status"] == "success"
other = submit("u1", "A101", "request2")
cancel("u1", other)
tick(other)
assert "read_order" not in get("u1", other)["events"]
try:
    get("u2", tid)
except PermissionError:
    pass
else:
    raise AssertionError("跨用户读取未被阻止")
try:
    submit("u1", "B200", "request1")
except ValueError:
    pass
else:
    raise AssertionError("同键异参未被阻止")
print(list(tasks.values()))
print("PASS：接收不等于成功、查询隔离、取消与重复提交")
```

**预期现象：**任务先 queued，再 tick 才 success；取消任务没有 read_order 事件；跨用户查询和同键异参被拒绝。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

### FastAPI 最小服务（本次未安装或启动）

固定教学依赖 `fastapi==0.120.0`、`uvicorn==0.38.0`。练习时把完整块保存为 `/tmp/course_api.py`。演示只监听本机、只读模拟订单；固定测试令牌只用于课程，不能用于正式认证。

```python
# course: optional
import asyncio
from contextlib import asynccontextmanager, suppress
from uuid import uuid4
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

tasks, workers, dedup = {}, {}, {}

@asynccontextmanager
async def lifespan(app):
    yield
    pending = list(workers.values())
    for worker in pending:
        worker.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

app = FastAPI(lifespan=lifespan)

class Submit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    order_id: str = Field(min_length=1)
    request_key: str = Field(min_length=1)

def identity(authorization):
    users = {"Bearer course-u1": "u1", "Bearer course-u2": "u2"}
    if authorization not in users:
        raise HTTPException(401, "invalid_test_token")
    return users[authorization]

def owned(user, task_id):
    row = tasks.get(task_id)
    if row is None or row["owner"] != user:
        raise HTTPException(404, "task_not_found")
    return row

async def work(task_id):
    row = tasks[task_id]
    try:
        row["status"] = "running"
        await asyncio.sleep(2)  # 模拟等待，便于取消实验。
        order = {"A100": "u1", "B200": "u2"}.get(row["order_id"])
        if order != row["owner"]:
            row["status"] = "failed"
            row["error"] = "not_found_or_forbidden"
            return
        row["events"].append("order_observed")
        row["status"] = "success"
    except asyncio.CancelledError:
        row["status"] = "cancelled"
        row["events"].append("cancelled")
        raise

@app.post("/tasks", status_code=202)
async def submit(body: Submit, authorization: str | None = Header(default=None)):
    user = identity(authorization)
    key = (user, body.request_key)
    if key in dedup:
        row = tasks[dedup[key]]
        if row["order_id"] != body.order_id:
            raise HTTPException(409, "idempotency_conflict")
        return {"task_id": row["id"], "status": row["status"]}
    tid = str(uuid4())
    tasks[tid] = {"id": tid, "owner": user, "order_id": body.order_id,
                  "status": "queued", "events": ["accepted"]}
    dedup[key] = tid
    worker = asyncio.create_task(work(tid))
    workers[tid] = worker
    worker.add_done_callback(lambda done, task_id=tid: workers.pop(task_id, None))
    return {"task_id": tid, "status": "queued"}

@app.get("/tasks/{task_id}")
async def status(task_id: str, authorization: str | None = Header(default=None)):
    return owned(identity(authorization), task_id)

@app.post("/tasks/{task_id}/cancel")
async def cancel(task_id: str, authorization: str | None = Header(default=None)):
    row = owned(identity(authorization), task_id)
    worker = workers.get(task_id)
    if worker is not None and not worker.done():
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker
        row["status"] = "cancelled"
    return {"task_id": task_id, "status": row["status"]}

@app.get("/health/live")
async def live():
    return {"status": "alive"}
```

```bash
uv run --with 'fastapi==0.120.0' --with 'uvicorn==0.38.0' python -m uvicorn course_api:app --app-dir /tmp --host 127.0.0.1 --port 8000
```

在另一终端提交：

```bash
curl -sS -X POST http://127.0.0.1:8000/tasks -H 'Authorization: Bearer course-u1' -H 'Content-Type: application/json' -d '{"order_id":"A100","request_key":"demo-1"}'
```

复制返回的 `task_id`，用 `GET /tasks/{task_id}` 查询、`POST /tasks/{task_id}/cancel` 取消，均带相同测试 Authorization。正常应 queued/running 后 success；立刻取消应 cancelled；换 u2 查询应 404；同 request_key 改订单应 409。再次从头实验使用新 key。此服务不持久化，不能运行多个 worker 来共享任务；重启恢复留到持久任务层集成。
## 实验步骤与练习

1. 按下方 HTTP 示例运行，提交后连续查询状态，区分 202 与业务 success。
2. 创建后立刻取消，再观察事件中是否出现后续动作；请求已经完成时取消不能倒转终态。
3. 设计事件流：每条含 task_id、event_id、status，断线后先查询任务终态；下面使用轮询完成最小接口，流式扩展不要改变验收标准。

## 常见错误

- POST 返回 200/202 就告诉用户已办完。
- 查询和取消接口不检查用户身份。
- 进程内 BackgroundTasks 被描述为可靠队列。

## 思考题

客户端关闭状态页面后，服务器应该自动取消任务吗？

<details>
<summary>参考答案（先自行作答）</summary>

需要明确产品契约。一次查询或流式连接关闭不等于用户撤销任务；显式取消接口更清楚。若设计断开即取消，也要处理已经发出的副作用。

</details>

## 验收标准

- [ ] 提交、状态与业务终态区分。
- [ ] 任务查询和取消按用户隔离。
- [ ] 取消后不启动后续动作，进程内示例局限明确。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 服务示例固定 FastAPI 0.120.0、Uvicorn 0.38.0；Pydantic 使用现有 2.13.5，未验证这组服务依赖的联合运行，安装时须核对锁定结果。Docker 演练未执行。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [FastAPI 后台任务及边界](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [FastAPI 0.120.0](https://pypi.org/project/fastapi/0.120.0/)
- [Uvicorn 0.38.0](https://pypi.org/project/uvicorn/0.38.0/)
- [asyncio 取消与超时](https://docs.python.org/3.12/library/asyncio-task.html)
- [Dockerfile 指令](https://docs.docker.com/reference/dockerfile/)

## 下一节衔接

下一节加入异步并发、超时、限流和取消传播。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_11/session_05/README.md) · [下一节](../session_02/README.md)
