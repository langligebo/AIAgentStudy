# 第 06 模块 Session 05：查询增强、重排与检索消融实验

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

在固定任务集上检验增强是否修复具体检索缺口，而不是一次打开所有策略。

## 前置知识与学习安排

W06 S02 的 BM25/RRF，W06 S04 的真实向量接口。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

先记录基线失败类型：术语不匹配、复合问题缺一部分、候选过多、无资料或权限不足。Multi-Query 产生同一意图的多个问法；HyDE 产生用于编码的假设文档；分解拆子问题；Step-Back 抽象到一般原则。生成的中间文字不能成为回答证据，也不能自行扩大产品、时间或访问范围。

每种变换有查询预算与去重规则。保留原查询，可检查新增问法是否漂移；派生查询继承身份与版本。RRF 根据名次融合，Cross-encoder 对 query 与候选联合评分；先测候选召回，再测重排效果。MMR 则在相关性和多样性之间取舍，适用于重复候选多的情况，不等于事实校验。

实验依次是基线、加一个增强、同查询集合复测。固定 candidate_k、rerank_k、context_k 的含义，统计召回、排序、忠实度、延迟与调用量。查询更多可能提升 recall，也可能增加噪声；召回提高但删除了关键例外的压缩仍可能让答案变差。

下例在固定候选上演示范围检查、融合与去重；真实模型生成/重排另用下方接口，不拿人工名次当模型结论。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
def queries(original, variants, product, limit=3):
    result = [original]
    for q in variants:
        if product not in q: raise ValueError("query_drift")
        if q not in result: result.append(q)
        if len(result) >= limit: break
    return result

def rrf(rankings, k=60):
    scores = {}
    for ranking in rankings:
        seen = set()
        for rank, item in enumerate(ranking, 1):
            if item in seen: continue
            seen.add(item)
            scores[item] = scores.get(item, 0) + 1/(k+rank)
    return sorted(scores, key=lambda key: (-scores[key], key))

qs = queries("K1 拆封能退吗", ["K1 已开封退款条件", "K1 拆封能退吗"], "K1")
assert len(qs) == 2
assert rrf([["general", "exception"], ["exception", "gift"]])[0] == "exception"
assert rrf([[], []]) == []
assert len(rrf([["a", "a"], ["a"]])) == 1
try: queries("K1 退货", ["所有商品均无条件退款"], "K1")
except ValueError: pass
else: raise AssertionError("drift")
print("PASS：查询预算、范围、融合去重；词项规则不是完整语义漂移检测")
```

**预期现象：**共有候选得到融合支持，空召回不产生虚构证据，产品范围漂移被拒绝。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。

## 真实生成与重排接口练习：本次未运行

下面两块各自独立。生成块从项目根执行，无新增依赖，使用公共客户端；只打印中间文档，不把它当政策。真实向量召回接上一节的编码器，需在自己的练习中记录该连接的输入输出。

<!-- verify: live -->
```python
from common.llm import create_llm_client
r = create_llm_client().generate(
    "为检索编写一段假设文档，不声称它是真实政策。问题：K1 拆封后的退货限制是什么？", temperature=0.0)
if r.finish_reason != "stop" or not r.text.strip(): raise RuntimeError("假设文档未完成")
print("仅用于检索表示，不能引用为证据：", r.text)
```

重排使用 `sentence-transformers==3.3.1`：到本课运行 `uv run --with 'sentence-transformers==3.3.1' python -`。在根 config.toml 的 `[reranker]` 配置 `model_path` 为可信本地 Cross-encoder 模型目录，选择输出一个相关性分数的模型；模型权重与依赖未下载。模型版本、输入长度与截断策略需记录。

<!-- verify: external -->
```python
import tomllib
from pathlib import Path
from sentence_transformers import CrossEncoder
cfg = tomllib.loads(Path("config.toml").read_text())["reranker"]
p = Path(cfg["model_path"]).expanduser()
if not p.is_dir(): raise ValueError("需要可信本地重排模型")
model = CrossEncoder(str(p), trust_remote_code=False)
query = "K1 已使用还能退吗？"
docs = ["七天内可申请退货。", "K1 已使用不适用普通退货。", "物流查询请提供单号。"]
scores = model.predict([(query, d) for d in docs])
if scores.ndim != 1: raise ValueError("本例需要单分数模型")
print(sorted(zip(scores.tolist(), docs), reverse=True))
# 单独检查排序变化，不能预写真实模型一定将某条排第一。
```

## 实验步骤与练习

1. 准备精确词、同义词、复合问题、无答案、权限受限五类问题及正确证据 ID。
2. 分别测试 Multi-Query、HyDE、分解和 Step-Back；保留原查询，统计新增调用和错误扩展。
3. 固定候选集合运行真实重排，再只改变 rerank_k；解释找不回未召回证据。
4. 用 MMR 或去重减少重复，核验否定与例外是否仍在上下文。
5. 在 W10 指标框架中做单项消融；不要使用公开演示题当保留验收集。

## 常见错误

- 假设文档的政策被引用为事实。
- 不同变体不继承 ACL。
- 同时改变模型、分块、查询和重排后声称某一项有效。

## 思考题

为何 HyDE 生成了正确样式的答案，仍需检索？

<details>
<summary>参考答案（先自行作答）</summary>

它是检索用表示，内容可能虚构。最终答案必须由实际、有权限且有效的资料支持。

</details>

## 验收标准

- [ ] 能说明四种查询变换的输入、输出和失败条件。
- [ ] 检索/重排/生成指标分开且对照固定变量。
- [ ] 至少选择一种增强完成真实效果实验并解释不采用的策略。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [HyDE](https://aclanthology.org/2023.acl-long.99/)
- [CrossEncoder](https://www.sbert.net/docs/cross_encoder/usage/usage.html)
- [Step-Back](https://arxiv.org/abs/2310.06117)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_04/README.md) · [下一节](../session_06/README.md)
