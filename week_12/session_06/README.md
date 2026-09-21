# 第 12 模块 Session 06：性能、路由、缓存与服务降级

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

在相同质量约束下测成本与延迟，不通过放宽授权换取速度。

## 前置知识与学习安排

第十二模块并发与限流、第十模块指标。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

性能分析分排队、模型 prefill/首字、decode、工具、检索、重排与持久化。测冷/热启动、P50/P95、峰值并发、内存和 token；平均延迟不能代表长尾。batch、KV/prefix cache、推理量化属于不同优化层，实际收益要在当前模型/硬件上测。

模型路由可按能力与任务难度选择成本，但低价模型必须满足结构化、工具与语言要求；fallback 不得放宽权限、丢失调用 ID 或把截断答案当成功。上游不可用时可明确降级为只读/人工，不能悄悄编造响应。

缓存分模型前缀缓存、精确业务缓存和语义答案缓存。缓存键要含身份作用域、数据/Prompt/模型版本与影响结果的参数；权限变更、政策更新和用户更正要失效。相似问题并不一定相同资格，语义缓存需额外业务判定；未确认写入绝不能缓存成成功。

熔断器限制持续调用故障依赖，half-open 探测要受限；它与每用户配额、速率限制、并发信号量和总 deadline 是不同控制。下例演示安全缓存键与带能力限制的选择，不产生真实性能或费用结论。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
import json
from hashlib import sha256

def cache_key(owner, query, data_version, model_version):
    fields = [owner,query,data_version,model_version]
    return sha256(json.dumps(fields).encode()).hexdigest()

def route(models, needs, ceiling):
    valid = [m for m in models if needs <= m["caps"] and m["cost"] <= ceiling and m["healthy"]]
    return min(valid,key=lambda m:m["cost"])["name"] if valid else "unavailable"

models = [{"name":"small","caps":{"text"},"cost":1,"healthy":True},
          {"name":"large","caps":{"text","tools"},"cost":3,"healthy":True}]
assert route(models,{"text"},3) == "small"
assert route(models,{"tools"},3) == "large"
assert route(models,{"tools"},1) == "unavailable"
assert cache_key("u1","退货",1,"m1") != cache_key("u2","退货",1,"m1")
assert cache_key("u1","退货",1,"m1") != cache_key("u1","退货",2,"m1")
models[1]["healthy"] = False
assert route(models,{"tools"},3) == "unavailable"
print("PASS：能力路由、预算、缓存隔离；费用为人工相对单位")
```

**预期现象：**工具任务不会降到没有工具能力的模型，跨用户/数据版本缓存键不同。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 为实际 Agent 分阶段计时，固定任务和模型条件，分别测冷/热与长尾。
2. 一次只打开一种优化，统计质量、费用、排队与错误；未知硬件/价格不填零。
3. 模拟依赖连续失败，添加熔断/受限探测与配额；区别于写入幂等核对。
4. 测试政策更新、用户更正和权限撤销对缓存的影响，再设计模型路由回归。

## 常见错误

- 认为缓存命中就无需重新鉴权。
- 只看 tokens/s，不看任务完成时间。
- fallback 返回答案却没声明能力缺失。

## 思考题

两位用户的问题相同，能否复用同一退货资格答案？

<details>
<summary>参考答案（先自行作答）</summary>

不能默认复用，资格可能依赖各自订单、时间、身份和政策版本；必须先验证缓存适用范围与权限。

</details>

## 验收标准

- [ ] 性能指标对应实际阶段且有尾延迟。
- [ ] 缓存键与失效策略覆盖身份和版本。
- [ ] 优化不降低预设质量和安全门槛。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Ollama 性能与资源说明](https://docs.ollama.com/faq)
- [OpenTelemetry 指标](https://opentelemetry.io/docs/concepts/signals/metrics/)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_05/README.md) · [下一节](../../week_13/session_01/README.md)
