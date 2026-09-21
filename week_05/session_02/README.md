# 第 05 周 Session 02：Skill 发现、选择与渐进加载

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

先提供元数据供选择，再读取被选 Skill 正文和必要资料，记录加载过程。

## 前置知识与学习安排

上一节 Skill 文件结构；工具白名单。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

发现阶段只列名称和描述，避免每轮塞入所有说明。激活阶段可以由用户显式指定，也可以由模型从目录中选择；两者都要经过宿主允许列表。读取正文之后再按需要加载引用资料，称为渐进式加载。

模型输出的 skill_name 也属于不可信参数。路径必须映射到受控目录，不能允许 `../` 或符号链接逃出范围。实际部署还应限制文件大小、资源和脚本依赖；路径校验不是完整操作系统沙箱。

本例使用手工元数据目录，避免让教学重点变成 YAML 解析。selector 以规则模拟模型，不把关键词准确率当作真实激活能力。运行时记录 discover→activate→read→decision；只将文件放到磁盘并不会完成这条调用链。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from pathlib import Path
from tempfile import TemporaryDirectory

CATALOG = {"aftersales": "已购退换货", "product-info": "购买前规格咨询"}

def select(request, explicit=None):
    if explicit is not None:
        return explicit if explicit in CATALOG else None
    return "aftersales" if "退货" in request else "product-info" if "蓝牙" in request else None

with TemporaryDirectory() as tmp:
    root = Path(tmp).resolve()
    for name in CATALOG:
        folder = root / name
        folder.mkdir()
        (folder / "SKILL.md").write_text(f"# {name}\n先核对信息，再使用已授权工具。", encoding="utf-8")
    trace = [{"event": "discover", "names": list(CATALOG)}]
    def load(name, relative="SKILL.md"):
        if name not in CATALOG:
            raise ValueError("unknown_skill")
        base = (root / name).resolve()
        if not base.is_relative_to(root):
            raise ValueError("path_escape")
        target = (base / relative).resolve()
        if not target.is_relative_to(base):
            raise ValueError("path_escape")
        text = target.read_text(encoding="utf-8")
        if len(text) > 10000:
            raise ValueError("content_budget")
        trace.append({"event": "read", "skill": name, "file": relative})
        return text
    name = select("我想退货")
    trace.append({"event": "activate", "skill": name})
    body = load(name)
    trace.append({"event": "decision", "action": "ask_order_id", "loaded": bool(body)})
    assert select("你好") is None
    assert select("退货", explicit="unregistered") is None
    try:
        load("aftersales", "../../secret.txt")
    except ValueError as exc:
        assert str(exc) == "path_escape"
    else:
        raise AssertionError("路径越界未被阻止")
    assert len([x for x in trace if x["event"] == "read"]) == 1
    print(trace)
    print("PASS：按需加载、不适用、未知 Skill、路径越界")
```

**预期现象：**只加载 aftersales 的正文；问候不激活；越界路径被拒绝。决策记录是夹具，实际模型是否使用 Skill 要另测。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 增加 reference 文件，只在步骤需要时调用 load(name, relative)，检查读取次数。
2. 把第 4 周运行时的决策上下文加上选中的 body，同时保留工具预算和审批规则。
3. 为两个相似 Skill 写互斥描述，用相同请求比较显式选择与模型选择；无适合项允许返回 none。

## 常见错误

- 把所有 Skill 正文永久写入 system 消息。
- 让模型提供任意绝对路径作为 Skill。
- 把发现成功当作执行成功，没有检查正文是否真的进上下文。

## 思考题

用户显式选择 Skill 时，是否还需要权限检查？

<details>
<summary>参考答案（先自行作答）</summary>

需要。显式选择授权使用该方法，不代表授权其中所有外部操作。读取范围、脚本执行和写工具仍由各自的安全边界限制。

</details>

## 验收标准

- [ ] 轨迹包含发现、激活、读取、使用。
- [ ] 没有适用 Skill 时能不加载。
- [ ] 引用只能读取受控 Skill 范围。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 Skills 为文件协议，无 Python SDK 依赖；按核对日的官方规范编写，教学检查不是完整规范验证器。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Agent Skills 文件规范](https://agentskills.io/specification)
- [宿主如何接入 Skills](https://agentskills.io/client-implementation/adding-skills-support)

## 下一节衔接

下一节用固定样本评估正确触发、误触发和版本回归。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
