# 第 12 周 Session 03：部署准备、健康检查与回退

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

区分存活与就绪，检查版本和状态恢复条件，并为失败版本回退提供可执行步骤。

## 前置知识与学习安排

任务服务、持久状态、回归门槛。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

存活检查判断进程是否还能处理请求，就绪检查判断服务是否具备接收当前任务的条件。依赖不可用时可以存活但未就绪；不要每次健康检查都发一次昂贵模型请求。使用有时效的轻量依赖状态，并让未就绪实例停止接新任务。

配置分非敏感版本参数与密钥；当前项目模型地址仍以 config.toml 为准。不要在课件里引入与公共客户端冲突的另一套地址。远程密钥以后接适配器时由环境或秘密管理提供，不写进镜像、日志和仓库。

发布单元包含代码、模型配置、Prompt、Skill、知识索引和状态 Schema。回退前检查旧代码能否读新状态；版本号倒回不自动撤销数据库迁移。先停新任务、核对在途动作、保留可读 checkpoint，再切回已验证版本并做冒烟回归。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from dataclasses import dataclass

@dataclass(frozen=True)
class Release:
    code: str
    prompt: str
    skill: str
    data: str
    readable_schemas: frozenset[int]

old = Release("code-v1", "prompt-v1", "skill-v1", "data-v1", frozenset({1}))
new = Release("code-v2", "prompt-v2", "skill-v2", "data-v1", frozenset({1, 2}))

def health(process_alive, dependencies_ready, state_schema, release):
    return {"live": process_alive,
            "ready": process_alive and dependencies_ready and state_schema in release.readable_schemas}

def choose_release(current, candidate, state_schema, regression_ok):
    if state_schema not in candidate.readable_schemas:
        return current, "incompatible_state"
    if not regression_ok:
        return current, "regression_failed"
    return candidate, "switched"

assert health(True, False, 1, old) == {"live": True, "ready": False}
assert health(True, True, 1, old)["ready"]
active, status = choose_release(old, new, 1, True)
assert active == new and status == "switched"
active, status = choose_release(new, old, 2, True)
assert active == new and status == "incompatible_state"
active, status = choose_release(new, old, 1, True)
assert active == old
assert choose_release(old, new, 1, False)[1] == "regression_failed"
print("存活但未就绪：", health(True, False, 1, old))
print("允许回退后的发布单元：", active)
print("PASS：就绪、发布、回归拒绝、兼容与不兼容回退")
```

**预期现象：**依赖不可用时 live=True、ready=False；状态 Schema=2 阻止退回只能读 1 的旧版，兼容状态才可切回。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

### 本地容器演练步骤（本次未部署）

前置：已完成 Session 01，将其完整服务示例保存为一个临时演练目录中的 `course_api.py`。该服务只有内存任务状态和固定测试身份，容器化不会使它具备持久队列或正式认证。

同目录创建下面的 `Dockerfile`，这是练习时的操作，不是本次新增文件：

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.120.0 uvicorn==0.38.0
COPY course_api.py /app/course_api.py
USER 10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "course_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

`python:3.12-slim` 是可移动标签；正式复现实验还需记录实际镜像摘要及依赖锁定清单。模拟服务尚未调用公共模型客户端；整合时把 `common/` 与只读的 `config.toml` 接入应用，不改地址读取规则。

```bash
docker build -t course-agent:lesson12 .
docker run --rm --name course-agent -p 127.0.0.1:8000:8000 course-agent:lesson12
```

用另一终端查询 `http://127.0.0.1:8000/health/live` 并重复第 1 节提交/查询/取消场景。此时重启会丢内存任务，这应记录为已知限制；不要标记“重启恢复通过”。完成持久队列和 checkpoint 集成后再做停进程、恢复、拒绝审批和重复工单测试。日志保留在终端，持久数据库是业务状态而非实验输出报告。
## 实验步骤与练习

1. 按下面容器步骤在学习到本节时启动第 1 节服务；本次不构建或启动。
2. 停止依赖时让 readiness 返回失败而 liveness 仍通过，再恢复并检查接新任务。
3. 保存一个待审批任务 checkpoint，切换版本后恢复；若状态不兼容，应停止回退并明确迁移方案，不能丢任务。

## 常见错误

- 健康检查每秒消耗真实模型调用。
- 镜像包含真实密钥和实验报告。
- 回退只改标签，不验证持久状态兼容。

## 思考题

代码回到了旧版本，但 Skill 和知识索引仍是新版，算完整回退吗？

<details>
<summary>参考答案（先自行作答）</summary>

不算。行为由多个版本共同决定，应按验证过的发布清单恢复兼容组合，并重新跑关键正常与失败案例。

</details>

## 验收标准

- [ ] 存活与就绪语义清楚。
- [ ] 密钥与非敏感配置边界明确。
- [ ] 回退检查状态与行为版本兼容。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 本周复盘

任务接口管理长工作，运行控制处理资源与取消，部署回退必须验证持久状态和版本兼容。

| 本周节次 | 复盘重点 |
| --- | --- |
| [Session 01](../session_01/README.md) | 用提交、查询和取消接口管理长任务，区分 HTTP 请求成功与业务任务完成。 |
| [Session 02](../session_02/README.md) | 限制并发和总耗时，仅对可重试读取退避，并在取消后停止启动后续动作。 |
| [Session 03](../session_03/README.md) | 区分存活与就绪，检查版本和状态恢复条件，并为失败版本回退提供可执行步骤。 |

用一个本周的正常案例和一个失败案例，复述“输入 → 决策 → 执行/校验 → 观察 → 终态”。指出哪些证据来自模拟，哪些还需要真实实验；把未完成事项留在学习进度，不用补造成功记录。


## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 服务示例固定 FastAPI 0.120.0、Uvicorn 0.38.0；Pydantic 使用现有 2.13.5，未验证这组服务依赖的联合运行，安装时须核对锁定结果。Docker 演练未执行。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [FastAPI 后台任务及边界](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [FastAPI 0.120.0](https://pypi.org/project/fastapi/0.120.0/)
- [Uvicorn 0.38.0](https://pypi.org/project/uvicorn/0.38.0/)
- [asyncio 取消与超时](https://docs.python.org/3.12/library/asyncio-task.html)
- [Dockerfile 指令](https://docs.docker.com/reference/dockerfile/)

## 下一节衔接

本节完成本模块前三节的阶段复盘，接着学习新增的[Session 04](../session_04/README.md)；原下一模块安排顺延，历史待验收不变。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_02/README.md) · [下一节](../session_04/README.md)
