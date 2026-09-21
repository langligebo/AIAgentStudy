# 第 10 周 Session 01：分层评估与评分器校准

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_09/session_05/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

分别定位格式、检索、工具选择、轨迹和业务终态错误，并认识模型评分的边界。

## 前置知识与学习安排

第 2 周三层校验，第 6 周检索评估，第 9 周终态检查。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

最终回答正确与否只是一层。完整客服任务还要看字段格式、证据命中、工具和 Skill 选择、执行顺序、授权及业务终态。多层指标能区分“资料找错”与“找对后说错”，避免随意修改 Prompt。

代码评分适合明确契约和真实状态；人工评分适合模糊质量判断；模型评分适合辅助批量筛查，但需要用人工标注样本校准。模型可能受措辞、长度和自信语气影响，不能因为输出一个分数就当作客观真值。

本例用固定模型评分标签演示校准，统计与人工判断的一致率和错误接受数。安全或实际写入结果必须使用可检查事实，模型“觉得已创建”不能覆盖数据库无记录。评分器也需要版本和测试集，不要调到迎合所有展示样本。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import json

DB = {"T1": {"order": "A100"}}
CASES = [
    {"id": "ok", "raw": '{"ticket":"T1"}', "retrieval": True, "tool": True, "skill": True,
     "trace": True, "human": True, "judge": True},
    {"id": "bad_json", "raw": '{ticket:T1}', "retrieval": True, "tool": True, "skill": True,
     "trace": True, "human": False, "judge": False},
    {"id": "phantom", "raw": '{"ticket":"T9"}', "retrieval": True, "tool": True, "skill": True,
     "trace": True, "human": False, "judge": True},
    {"id": "unauthorized_trace", "raw": '{"ticket":"T1"}', "retrieval": True, "tool": True, "skill": True,
     "trace": False, "human": False, "judge": True},
]

def grade(case):
    try:
        value = json.loads(case["raw"])
    except json.JSONDecodeError:
        value = None
    schema = isinstance(value, dict) and set(value) == {"ticket"} and type(value["ticket"]) is str
    state = bool(schema and value["ticket"] in DB and DB[value["ticket"]]["order"] == "A100")
    layers = {"schema": schema, "retrieval": case["retrieval"], "tool": case["tool"],
              "skill": case["skill"], "trace": case["trace"], "business_state": state}
    return layers, all(layers.values())

for case in CASES:
    layers, success = grade(case)
    assert success == case["human"]
    print(case["id"], layers, "端到端", success)
agreement = sum(c["judge"] == c["human"] for c in CASES) / len(CASES)
false_accept = sum(c["judge"] and not c["human"] for c in CASES)
assert agreement == 0.5 and false_accept == 2
print("模拟评分器一致率", agreement, "错误接受", false_accept)
print("PASS：正常、格式错误、虚假工单、不合规轨迹和评分器误判")
```

**预期现象：**只有 ok 通过端到端验收；夹具评分器错误接受两项，因此即使最终文字像成功也不能批准。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## RAG 补充：RAGAS 与检索、生成指标

RAGAS 是评估工具体系，不是一项可以概括全部质量的分数。下面先学习指标与证据需求，再决定是否接 SDK；不把一个手算函数叫作 RAGAS 实现。

| 指标 | 在问什么 | 所需依据与限制 |
| --- | --- | --- |
| Precision@k | 选定前 k 个结果中有多少相关 | 需要人工/程序相关性标签；本课不足 k 时用实际返回数量，明确约定 |
| Recall@k | 已知应召回的证据有多少被前 k 命中 | 需要足够完整的标注集合；无答案样本另计拒答 |
| MRR / nDCG | 第一条相关证据多靠前 / 多级相关性排序怎样 | 排名与标注相关性；不能代替答案检查 |
| RAGAS Context Precision | 相关上下文是否排在无关内容前面 | 有多种需要/不需要 reference 的实现，应按具体指标核对；不是简单的 Precision@k 同义词 |
| RAGAS Context Recall | 支持参考答案的必要信息是否由检索上下文覆盖 | LLM 版本常按参考答案的陈述作支持性判断；不等同于片段 ID 集合的 Recall@k |
| Faithfulness | 回答中的陈述是否受检索上下文支持 | 需要回答和上下文；忠于过期或错误文档也可能得高分，不等于现实正确 |
| Answer/Response Relevancy、Correctness | 是否答到问题、与参考事实是否一致 | 各自需要问题或参考答案；不要与 faithful 混用 |

具体定义参阅 [Context Precision](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)、[Context Recall](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/)、[Faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/)。核对日期：2026-09-21；SDK 接口可能变化，使用前固定版本和指标变体。本次不新增依赖或评分服务调用。

最小例子只用人工相关性和陈述支持标签，验证分母与边界；自动“拆陈述、判断支持”还需要经过校准的评分器，不能省略后冒充真实效果。

```python
# course: offline
from math import isclose

relevant = {"return_rule", "gift_rule"}
retrieved = ["bluetooth", "return_rule", "gift_rule"]

def retrieval_metrics(ids, gold, k):
    if k <= 0:
        raise ValueError("k must be positive")
    top = list(dict.fromkeys(ids))[:k]
    hits = sum(item in gold for item in top)
    precision = hits / len(top) if top else 0.0
    recall = hits / len(gold) if gold else None
    first = next((rank for rank,item in enumerate(top,1) if item in gold), None)
    return precision, recall, 1/first if first else 0.0

precision, recall, mrr = retrieval_metrics(retrieved, relevant, 3)
assert isclose(precision, 2/3) and recall == 1.0 and mrr == 0.5
assert retrieval_metrics([], relevant, 3) == (0.0, 0.0, 0.0)
assert retrieval_metrics([], set(), 3)[1] is None
claims_supported_by_context = [True, False]  # “七天内申请”有依据，“自动退款”没有。
faithfulness_fixture = sum(claims_supported_by_context)/len(claims_supported_by_context)
assert faithfulness_fixture == 0.5
# 无陈述时不能除零或凭空当作完美答案；另外评估正确拒答。
def supported_ratio(labels):
    return sum(labels)/len(labels) if labels else None
assert supported_ratio([]) is None
print("Precision@3 / Recall@3 / MRR:", precision, recall, mrr)
print("人工支持标签比例：", faithfulness_fixture)
print("PASS：命中与排序、空检索、空真值和缺支持陈述；未调用 RAGAS")
```

接入练习顺序：准备 `user_input/retrieved_contexts/response/reference` 中指标实际需要的字段→固定评分模型和 Prompt/库版本→用人工案例校准→测原回答及添加无依据承诺后的变化。若评分超时或返回无效数据，标失败/未评分，不记作 0 或 1 分。

项目当前 `common.llm` 不是 RAGAS SDK 的原生接口，不能直接把 client 对象传给任意评分类并声称可运行。实际接入时需按所固定版本实现评分适配，在适配器内复用公共客户端；如指标需要 Embedding，也要补对应能力契约。本次只准备指标课和离线演算，SDK 集成仍未实现、未验证。

<details>
<summary>Faithfulness=1 是否表示答案一定正确？</summary>

不表示。它衡量相对所给上下文的支持关系；若上下文本身错、过期或属于另一产品，回答仍可能忠实却错误。还需答案事实、文档版本、适用范围和任务结果检查。

</details>

补充验收：分清检索 ID 指标和 RAGAS 的上下文/陈述指标；能解释零分母与评分失败；知道忠实度不能替代正确性。

## 实验步骤与练习

1. 增加检索未命中、选错 Skill 和选错工具三条样本，观察哪个分层首先失败。
2. 写明确人工评分准则，找两次独立判断不一致的样本，先修标准再调模型评分器。
3. 真实模型评分实验固定评分 Prompt 与版本，同时保留人工对照；本次不调用评分模型。

## 常见错误

- 只评回答可读性，不检查工单。
- 让同一模型自评自证而不校准。
- 丢掉格式失败样本后算正确率。

## 思考题

有工单记录但写入绕过了审批，能否算任务成功？

<details>
<summary>参考答案（先自行作答）</summary>

不能。成功标准包括授权与过程约束，业务终态只是其中一层；未经授权的成功副作用也属于失败。

</details>

## 验收标准

- [ ] 能将失败归到具体层。
- [ ] 代码评分与人工证据一致。
- [ ] 模型评分器的误接受单独记录。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Agent 评估的任务、轨迹与结果](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## 下一节衔接

下一节把评分所需证据连成脱敏、可追溯的运行记录。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_09/session_05/README.md) · [下一节](../session_02/README.md)

## SDK 衔接补充

[W10 S05](../session_05/README.md) 已提供 Ragas 0.2.15 通过公共客户端的 Faithfulness 适配代码与调用预算。该扩展尚未安装或执行；本节的人工标签计算仍不是 RAGAS 模型评分结果。
