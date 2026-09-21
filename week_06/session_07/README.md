# 第 06 模块 Session 07：GraphRAG、图检索与跨文档问题

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

理解实体关系、社区报告、局部与全局查询，避免把图的存在当作真实性。

## 前置知识与学习安排

W06 S06 的派生来源与权限、字典/图遍历。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

图检索把实体及关系作为可查询结构，适合追踪产品、订单、故障与政策之间的连接。Microsoft GraphRAG 还使用社区与摘要支持全局问题；简单的三元组遍历只覆盖图检索切片，不能声称实现其完整索引/查询系统。

实体抽取会有别名、同名、误合并，边也可能由模型幻觉产生。每个实体/边保留来源、版本和有效期；来源无效时边不能成为证据。普通向量检索善于局部语义匹配，图结构擅长明确关系，社区摘要用于主题汇总，最终仍回原文核验。

查询要限制起点、跳数、访问范围与节点数量。图关联可能把不同用户的数据连在一起，扩展每条边前都要授权，聚合计数和摘要也可能泄露。使用图并不自动解决权限、事实冲突或更新传播。

本例执行有限深度 BFS 并携带边来源；边是人工标注的可信夹具。课程要求理解和实现这一机制，再选择数据集评估是否值得建设完整 GraphRAG。相关的知识图谱、Text-to-SQL 与结构化检索应分别匹配问题和权限，不能把所有数据都强行转文本。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
from collections import deque
EDGES = [
    ("K1", "battery", "p1", "public"),
    ("battery", "warranty", "p2", "public"),
    ("K1", "customer-u2", "private1", "u2"),
    ("warranty", "K1", "p3", "public"),
]
VALID = {"p1", "p2", "p3", "private1"}
def walk(start, owner, max_hops=2):
    q, seen, proof = deque([(start,0)]), {start}, []
    while q:
        node, depth = q.popleft()
        if depth >= max_hops: continue
        for src,dst,source,scope in EDGES:
            if src != node or source not in VALID or scope not in {"public",owner}: continue
            proof.append((src,dst,source))
            if dst not in seen: seen.add(dst); q.append((dst,depth+1))
    return seen, proof

nodes, proof = walk("K1", "u1")
assert "warranty" in nodes and "customer-u2" not in nodes
assert "warranty" not in walk("K1", "u1", 1)[0]
VALID.remove("p2")
assert "warranty" not in walk("K1", "u1")[0]
assert walk("unknown", "u1")[1] == []
print("PASS：限跳、来源失效、访问边界、无关系")
```

**预期现象：**两跳找到保修关系，一跳不够；删除来源后关系不再成立，也没有跨用户扩展。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 给 K1/K-1 两个别名和同名不同产品设计实体 ID，避免错误合并。
2. 给每条边添加原文句子、版本和时间；人工审核一组抽取准确率。
3. 区分“这款电池适用什么政策”的局部查询与“主要投诉主题是什么”的全局问题，设计社区摘要流程。
4. 使用同一查询集比较文本、图与二者组合；记录构图成本、漏边、幻觉边与删除重建。
5. 复盘整个 RAG 模块：从解析到答案的每个错误都应有归属，不能用复杂架构掩盖解析失败。

## 常见错误

- 无来源的三元组被当作事实。
- 图遍历不断扩大导致成本失控。
- 只检查结果节点权限，不检查边和社区摘要。

## 思考题

两个模型抽取了相同关系，能否跳过原文验证？

<details>
<summary>参考答案（先自行作答）</summary>

不能，相同输入可能导致相同幻觉。需要来源支持、实体消歧与任务相关性检查。

</details>

## 验收标准

- [ ] 能区分基础图检索与完整 GraphRAG。
- [ ] 有限跳数、访问过滤和失效传播有效。
- [ ] 知道全局问题需要怎样的聚合证据与评价。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [GraphRAG 查询模式](https://microsoft.github.io/graphrag/query/overview/)
- [GraphRAG 索引](https://microsoft.github.io/graphrag/index/overview/)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_06/README.md) · [下一节](../../week_07/session_01/README.md)
