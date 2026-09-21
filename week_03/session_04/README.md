# 第 03 模块 Session 04：工具界面设计、检索选择与并发契约

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

把工具目录设计成模型能选择、执行器能约束、并发时能关联结果的接口。

## 前置知识与学习安排

第三模块前三节与 W01 S04。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

工具过多、名称相似、描述冗长会影响选择。先按任务和可信权限形成允许集合，再从允许集合检索候选；可分页或渐进发现，不必把所有工具塞进每次 Prompt。没有适用工具时应返回 none，不能为了完成任务扩大权限。

工具界面要写清输入单位、日期/时区、枚举、默认值、输出大小、分页游标和错误可重试性。返回契约还应表达 evidence_id、partial、freshness。工具 JSON Schema 是给模型的提示与协议，执行器仍逐字段验证；schema 更新须做兼容测试。

并发只用于互不依赖的读取。每次调用关联唯一 ID，聚合按 ID 而不是完成顺序。依赖订单查询结果的政策查询必须等输入齐备；对共享资源的写入要串行化或用业务事务处理。某分支失败时需明确全局失败还是允许部分结果。

下例演示目录过滤和结果关联，不声称实现向量工具检索或异步执行。工具检索本身也要评估漏选：真实需要的工具未进入候选集合，模型再聪明也无法调用。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
CATALOG = {
    "get_order": {"scope": "orders:read", "tags": {"订单", "物流"}},
    "get_policy": {"scope": "policy:read", "tags": {"政策", "退货"}},
    "create_ticket": {"scope": "tickets:write", "tags": {"工单"}},
}
def discover(terms, scopes):
    return [name for name, meta in CATALOG.items()
            if meta["scope"] in scopes and meta["tags"] & set(terms)]

def correlate(requests, responses):
    ids = [r["id"] for r in requests]
    if len(set(ids)) != len(ids): raise ValueError("duplicate_request")
    out = {}
    for r in responses:
        if r["id"] not in ids or r["id"] in out: raise ValueError("unexpected_or_duplicate")
        out[r["id"]] = r
    if set(out) != set(ids): raise ValueError("missing_response")
    return [out[i] for i in ids]

assert discover(["订单", "工单"], {"orders:read"}) == ["get_order"]
assert discover(["问候"], {"orders:read"}) == []
requests = [{"id": "a"}, {"id": "b"}]
assert [r["id"] for r in correlate(requests, [{"id": "b"}, {"id": "a"}])] == ["a", "b"]
for bad in [[{"id": "a"}], [{"id": "a"}, {"id": "a"}], [{"id": "a"}, {"id": "x"}]]:
    try: correlate(requests, bad)
    except ValueError: pass
    else: raise AssertionError("bad correlation accepted")
print("PASS：允许目录、无需工具、乱序关联与缺失拒绝")
```

**预期现象：**无授权工具不出现在候选中；乱序结果归位，缺失或重复不会静默覆盖。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 为现有工具写完整说明，增加单位、输出样例和不适用场景。
2. 用相似名称、缺字段、无需工具样本分别测选择率与候选召回率。
3. 把两个独立读取接到 asyncio.TaskGroup，分别测试必须全部成功与允许部分返回；依赖读取保持顺序。
4. 设计 schema v1→v2 迁移，旧调用明确拒绝或转换，不能默默改变金额单位。

## 常见错误

- 检索后才做权限过滤，却已把私有工具说明传给模型。
- 用完成先后对应工具调用。
- 顶层有最大轮数就允许单轮无限工具调用。

## 思考题

两次调用相同工具但订单不同，能只用工具名关联吗？

<details>
<summary>参考答案（先自行作答）</summary>

不能。需要调用级 ID 或供应商明确支持的关联协议；名称不能区分同工具多次调用，当前 Ollama 教学客户端的串行顺序限制必须保留。

</details>

## 验收标准

- [ ] 工具说明能消除至少一个参数歧义。
- [ ] 多调用结果一一对应且部分失败不丢。
- [ ] 工具检索漏选与模型选错分开评估。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [工具接口设计](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [Python TaskGroup](https://docs.python.org/3.12/library/asyncio-task.html)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../../week_04/session_01/README.md)
