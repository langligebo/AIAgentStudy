# 第 07 模块 Session 04：记忆写入、检索与巩固评估

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

把长期记忆做成有来源、有用途、可纠正的闭环，而不是无限保存聊天。

## 前置知识与学习安排

第七模块前三节与检索评估。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

长期记忆可按用途理解：语义记忆保存已确认事实/偏好，情节记忆记录一次任务及结果，程序性记忆保存经过验证的方法。Skill 是显式方法载体，不能自动把一次成功的模型轨迹提升为通用规则。

写入流程应包含候选抽取、必要性判断、确认/来源、去重、冲突与版本、保存；读取按身份、任务相关性、时间和优先级筛选。热门但无关的旧事实不该占据上下文。时间衰减不是删除策略，删除还要影响索引、缓存和在途更新。

巩固可把多次事件整理成摘要，但要保留证据，不把失败经验总结成错误的事实。记忆投毒可能来自用户输入、文档或模型自述；可信身份只说明是谁说的，不自动证明事实是真的。记忆候选与生效记录分开，未经确认的关键个人信息不自动采用。

评估包括写入精确率/召回、读取相关性、冲突处理、遗忘/删除成功和最终任务影响。下面以规则模拟候选审核与检索，不代表真实模型能正确抽取记忆。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
MEMORY = []
def propose(owner, key, value, source, confirmed):
    if source != "user" or not confirmed: return "pending"
    if key not in {"language", "reply_style"}: return "not_needed"
    for m in MEMORY:
        if m["owner"] == owner and m["key"] == key: m["active"] = False
    MEMORY.append(dict(owner=owner,key=key,value=value,source=source,active=True))
    return "saved"

def recall(owner, needed):
    return {m["key"]:m["value"] for m in MEMORY if m["owner"]==owner and m["active"] and m["key"] in needed}

assert propose("u1","language","中文","user",True) == "saved"
assert propose("u1","language","英语","model",False) == "pending"
assert recall("u1",{"language"}) == {"language":"中文"}
assert recall("u2",{"language"}) == {}
assert propose("u1","language","英语","user",True) == "saved"
assert recall("u1",{"language"}) == {"language":"英语"}
assert recall("u1",{"address"}) == {}
print("PASS：候选/生效分离、作用域、更正与按需读取")
```

**预期现象：**模型猜测不会覆盖已确认偏好，更正使旧值退出后续读取。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 对 12 条含暂时请求、长期偏好和模型猜测的对话标注“该记/不该记”。
2. 为候选抽取接公共模型，再独立测规则门控与抽取质量；保留不确定项。
3. 比较无记忆、全部历史、结构化按需记忆在同一多会话任务上的表现。
4. 制造错误巩固、冲突、删除与缓存残留，检查下一轮输出是否仍引用旧事实。

## 常见错误

- 用户一次请求永久提升成偏好。
- 记忆命中就自动执行写操作。
- 用检索相似度代表记忆可信度。

## 思考题

用户今天说“这次用英语”，应该覆盖长期语言偏好吗？

<details>
<summary>参考答案（先自行作答）</summary>

不应默认覆盖。它是本次作用域的约束；长期变更需要相应意图或确认。

</details>

## 验收标准

- [ ] 能区分三类记忆与任务状态。
- [ ] 记忆写入与读取都有评价样本。
- [ ] 投毒、更正、跨用户和删除情形不静默出错。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [上下文与记忆工程](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../../week_08/session_01/README.md)
