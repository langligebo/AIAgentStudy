# 第 01 模块 Session 04：Python 工程基础与测试入口

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

能独立阅读契约、定位异常，并用可替换依赖测试一个业务函数。

## 前置知识与学习安排

第一周函数、字典与循环；当前已到第二周时先做本节检测，缺项再补。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

Agent 工程用到的不只是会写 Prompt：模块导入、虚拟环境、类型、异常、迭代器、上下文管理器、HTTP 状态和测试共同决定能否诊断失败。类型标注帮助表达意图，不自动校验运行时 JSON；`bool` 又是 `int` 的子类，金额等字段需按业务约束校验。

依赖注入把“调用谁”与“怎样判断结果”分开。测试中换成明确的假服务，可以稳定制造断网、缺字段和越权；网络错误不能被转换成正常空结果。捕获具体异常并保留原因，不使用裸 `except` 吞掉取消或程序错误。

环境检查依次用 `uv run python --version`、`uv run python -c "import sys; print(sys.executable)"` 确认解释器，查看 pyproject 与 uv.lock，再用 `uv run python -m unittest discover -s tests -v` 运行现有测试。锁文件用于依赖复现，API、模型和数据版本仍需单独记录。Git diff 用于查看自己的变化，学习练习不自动提交。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
import json
from dataclasses import dataclass
from typing import Protocol
import unittest

class Reader(Protocol):
    def get(self, order_id: str) -> str: ...

@dataclass(frozen=True)
class Order:
    order_id: str
    amount: int

def load(reader: Reader, order_id: str) -> Order:
    obj = json.loads(reader.get(order_id))
    if set(obj) != {"order_id", "amount"}:
        raise ValueError("fields")
    if obj["order_id"] != order_id or type(obj["amount"]) is not int or obj["amount"] < 0:
        raise ValueError("business_contract")
    return Order(**obj)

class Fake:
    def __init__(self, value): self.value = value
    def get(self, order_id):
        if isinstance(self.value, Exception): raise self.value
        return self.value

class ContractTests(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(load(Fake('{"order_id":"A100","amount":100}'), "A100").amount, 100)
    def test_bad_type(self):
        with self.assertRaises(ValueError):
            load(Fake('{"order_id":"A100","amount":true}'), "A100")
    def test_network_is_not_empty(self):
        with self.assertRaises(TimeoutError): load(Fake(TimeoutError()), "A100")
    def test_unknown_field(self):
        with self.assertRaises(ValueError): load(Fake('{"order_id":"A100"}'), "A100")

result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests))
assert result.wasSuccessful()
print("PASS：契约、异常传播、可替换依赖")
```

**预期现象：**4 个测试通过，超时保持超时，布尔金额被拒绝。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 解释每个类型与异常的职责，再运行示例。
2. 增加畸形 JSON、负金额、订单错配测试，预测失败层。
3. 从现有 tests 中选一个测试，指出被测公共客户端、模拟响应和断言；读 traceback 定位源行。
4. 在独立小函数中使用 with 管理临时资源，再解释生成器的惰性执行与列表的区别。

## 常见错误

- 把类型注解当输入校验。
- 为了测试调用真实订单系统。
- 忽略解释器路径，包安装到另一环境。

## 思考题

为什么不把 TimeoutError 返回成空字典？

<details>
<summary>参考答案（先自行作答）</summary>

空字典会把基础设施失败伪装成业务无结果，下游可能错误回复没有订单。错误类别应保留到调用者。

</details>

## 验收标准

- [ ] 能创建与运行 unittest，且失败时看到具体断言。
- [ ] 能区分 JSON、业务、网络异常。
- [ ] 能解释模块、venv、依赖声明与锁文件作用。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Python unittest](https://docs.python.org/3.12/library/unittest.html)
- [Python typing](https://docs.python.org/3.12/library/typing.html)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../session_05/README.md)
