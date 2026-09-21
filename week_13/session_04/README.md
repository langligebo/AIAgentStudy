# 第 13 模块 Session 04：综合工程分层与端到端契约测试

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

把各节机制连成同一个可替换、可诊断的系统，验收真实边界而非函数数量。

## 前置知识与学习安排

前十二模块核心机制；原 W13 S01～03 为基础项目检查点。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

整合架构应分清入口（CLI/HTTP/事件）、应用任务服务、运行时、模型/检索/工具适配、状态存储与业务系统。业务契约不应依赖某个模型 SDK 的原始字段。相同服务可被 CLI 和 HTTP 调用，避免复制授权与业务判断。

项目必须有一条纵向闭环：缺信息→追问→检索与订单核验→方案→用户审批→受控模拟写入→核验→带来源回复。每次替换一个边界，用契约测试确保模型、LangGraph、MCP、队列和存储交换的身份/任务/版本一致。依赖注入支持离线失败重放，真实联调再验证协议。

测试层次分单元、适配契约、集成、端到端、故障与安全回归。对真实模型用任务标准而非逐字快照；对确定协议字段严格断言。测试应从系统外观察状态与副作用，不能只断言被测函数自己报告 ok。

下例用独立订单/工单观察核验结果，特意构造说谎实现。它是端到端验收器的机制切片，不是已交付全部 Agent。正式项目需要在学习实践中连接已有实现，并补齐仍未实现的适配器。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
CASES = [
    {"id":"normal","owner":"u1","order":"A100","approved":True,"expected":"success","writes":1},
    {"id":"no_approval","owner":"u1","order":"A100","approved":False,"expected":"waiting_approval","writes":0},
    {"id":"forbidden","owner":"u2","order":"A100","approved":True,"expected":"forbidden","writes":0},
]
def implementation(case, store):
    if case["owner"] != "u1": return "forbidden"
    if not case["approved"]: return "waiting_approval"
    store.append({"order":case["order"],"owner":case["owner"]})
    return "success"

def evaluate(system):
    failures=[]
    for case in CASES:
        store=[]
        status=system(case,store)
        right = status == case["expected"] and len(store)==case["writes"]
        if status=="success":
            right = right and any(t["owner"]==case["owner"] and t["order"]==case["order"] for t in store)
        if not right: failures.append(case["id"])
    return failures

assert evaluate(implementation) == []
assert "normal" in evaluate(lambda case,store: "success")
def wrong_order(case,store):
    status=implementation(case,store)
    if store: store[0]["order"]="other"
    return status
assert "normal" in evaluate(wrong_order)
print("PASS：终态与实际副作用独立核验、虚假成功拒绝")
```

**预期现象：**正常实现满足三类用例，说谎或写错订单被独立验收器抓出。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 画清每个模块接口和身份来源，先连接 CLI→任务服务→只读工具→终态。
2. 加入真实模型和检索，再加入 Skill、记忆、checkpoint、MCP；每替换一层复验正常及一个故障，不同时改所有 Prompt。
3. 增加审批写入与核验，接 HTTP 和队列；复用业务服务，不新写绕过授权的快捷路径。
4. 运行缺字段、无证据、权限、更正、取消、响应丢失、重启、重复投递、版本迁移全链路案例。
5. 把实际未实现项列入进度，不能用固定夹具通过勾选真实集成。

## 常见错误

- 只演示一条 happy path。
- 测试和实现共享同一个“是否成功”布尔值。
- 为框架接入复制模型服务配置。

## 思考题

为什么不能把所有课程代码块直接拼成生产 Agent？

<details>
<summary>参考答案（先自行作答）</summary>

它们演示不同机制和抽象层，有各自夹具与范围；必须设计统一契约、替换依赖、处理跨边界失败并做真实联调。

</details>

## 验收标准

- [ ] 同一任务跨模块身份、版本和证据一致。
- [ ] 验收通过来自独立观察而非自述。
- [ ] 至少一条真实模型与真实框架/协议链路有可复现证据。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Python 测试组织](https://docs.python.org/3.12/library/unittest.html)
- [Agent 评估方法](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../session_05/README.md)
