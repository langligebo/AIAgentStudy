# 第 06 模块 Session 06：RAPTOR 分层索引与派生证据

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

通过构建摘要层理解跨片段问题，同时保留原文追溯和更新删除。

## 前置知识与学习安排

分块、Embedding、数据版本与权限。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

RAPTOR 的主张是递归聚类并摘要，形成多层表示，使检索可从更高层聚合信息。叶子仍是原文块，摘要节点必须记录子节点和来源集合；问某产品细则时高层摘要可能太粗，不能替代叶子验证。

本节实现透明的层级索引切片：人工指定聚类和摘要，真正执行子树展开、授权与来源检查。完整 RAPTOR 还包括向量化、降维/聚类、模型摘要和跨层检索；本例没有这些学习算法，因此不把它命名为论文复现。实验阶段按论文逐个替换夹具，再和平铺检索比较。

摘要存在三类风险：失真、陈旧、跨权限混合。摘要包含无权叶子的事实时，仅在最后过滤叶子已太迟，不能把混合摘要给该用户。本例保守地拒绝整节点；工程中可按权限域构建摘要或重新生成授权范围摘要。

数据更新要沿依赖图使祖先摘要失效，重建后原子切换版本。一个摘要来源缺失即不能当作有效证据，不能因为摘要文字还在就继续使用。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
NODES = {
    "a": {"text": "K1 七天内可退，已使用除外", "children": [], "owner": "u1", "valid": True},
    "b": {"text": "赠品须退回", "children": [], "owner": "u1", "valid": True},
    "c": {"text": "VIP 补偿规则", "children": [], "owner": "u2", "valid": True},
    "s": {"text": "K1 退货与赠品要求摘要", "children": ["a","b"], "valid": True},
    "mixed": {"text": "跨用户摘要", "children": ["a","c"], "valid": True},
}
def leaves(key, visiting=None):
    visiting = set() if visiting is None else visiting
    if key in visiting: raise ValueError("cycle")
    n = NODES[key]
    if not n["valid"]: raise ValueError("stale")
    if not n["children"]: return [key]
    out = []
    for child in n["children"]: out += leaves(child, visiting | {key})
    return list(dict.fromkeys(out))

def retrieve(key, owner):
    ids = leaves(key)
    if any(NODES[i]["owner"] != owner for i in ids): raise PermissionError("mixed_scope")
    return {"summary": NODES[key]["text"], "evidence": [(i,NODES[i]["text"]) for i in ids]}

assert len(retrieve("s", "u1")["evidence"]) == 2
try: retrieve("mixed", "u1")
except PermissionError: pass
else: raise AssertionError("leaked summary")
NODES["b"]["valid"] = False
try: retrieve("s", "u1")
except ValueError: pass
else: raise AssertionError("stale summary")
print("PASS：层级展开、混合权限拒绝、失效来源阻断")
```

**预期现象：**摘要可展开到两条原文；跨用户和失效叶子使摘要不可用。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 把 8～12 段政策分成两级，先手工写摘要并核对条件遗漏。
2. 记录每个摘要的源块版本，更新或删除一个叶子，列出受影响的祖先。
3. 按论文用固定模型/聚类设置替换人工组与摘要，记录额外调用、存储和重建成本；这一步需要单独实跑验收。
4. 在局部细节题与跨文档汇总题上比较平铺检索和分层索引，不能只挑后者擅长的问题。

## 常见错误

- 只保存摘要不保存依赖来源。
- 把含私有资料的摘要称作公开信息。
- 把手工层级当完整论文算法。

## 思考题

摘要没有暴露原文 ID，是否还需要来源权限？

<details>
<summary>参考答案（先自行作答）</summary>

需要。摘要本身可能泄露原文事实，权限必须覆盖派生内容而不仅原文链接。

</details>

## 验收标准

- [ ] 能画出叶子、摘要、祖先与失效传播。
- [ ] 正常、删除和混合权限路径有验证。
- [ ] 能给出是否采用分层索引的任务证据；算法替换单独记录。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [RAPTOR 论文](https://arxiv.org/abs/2401.18059)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_05/README.md) · [下一节](../session_07/README.md)
