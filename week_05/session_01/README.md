# 第 05 周 Session 01：编写售后处理 Skill

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_04/session_04/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

编写描述适用范围、步骤和失败分支的 Skill，并区分说明文件、辅助资料和执行工具。

## 前置知识与学习安排

第 4 周循环与权限执行器；Markdown 基础。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

Skill 把可复用任务方法组织为一个目录，入口是带元数据的 `SKILL.md`。名称和描述帮助发现，正文指导处理流程；references 放需要时读取的细节，assets 放模板，scripts 放可选辅助程序。脚本存在不意味着获准执行。

本课采用 Agent Skills 规范中的文件布局；售后规则是教学数据，不是真实商家的承诺。名称与目录相同，描述写清触发和排除条件。版本可放在 metadata 中用于项目管理；版本、信任和授权策略仍由宿主实现。

先编写“核验身份和订单→检索政策→给方案→必要审批→创建→核验”的步骤，再为缺订单、无政策、越权和写入未知补分支。Skill 教模型如何使用工具；它不能改变工具白名单或授权结果。以下只验证教学文件的内容与简单前置条件，不是完整 YAML 或规范验证器。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
from pathlib import Path
from tempfile import TemporaryDirectory

SKILL = """---
name: aftersales
description: 处理已购商品退换货，核验订单和政策；购买前规格咨询不适用。
metadata:
  version: "1.0.0"
---
# 售后处理
1. 缺订单号先追问；由执行器核对当前用户是否可访问订单。
2. 读取 references/policy.md；政策不足就说明缺口。
3. 用 assets/reply.txt 组织建议，不承诺已经执行。
4. 写入前由程序核验具体参数的审批。
5. 调用工单工具后查询核验；超时结果未知时不要重复创建。
"""
with TemporaryDirectory() as tmp:
    root = Path(tmp) / "aftersales"
    (root / "references").mkdir(parents=True)
    (root / "assets").mkdir()
    (root / "SKILL.md").write_text(SKILL, encoding="utf-8")
    (root / "references/policy.md").write_text("模拟政策 v1：签收 7 天内可申请。", encoding="utf-8")
    (root / "assets/reply.txt").write_text("订单：{order_id}；依据：{source}；建议：{proposal}", encoding="utf-8")
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    assert f"name: {root.name}" in text
    for relative in ("references/policy.md", "assets/reply.txt"):
        assert (root / relative).is_file()
    def prepare(order_id, authorized):
        if not order_id:
            return "ask_order_id"
        if not authorized:
            return "deny"
        return "read_policy"
    assert prepare("A100", True) == "read_policy"
    assert prepare(None, True) == "ask_order_id"
    assert prepare("B200", False) == "deny"
    print(text)
    print("PASS：文件引用、正常前置条件、缺信息和越权分支")
```

**预期现象：**控制台打印完整 Skill 内容并通过断言。目录仅为临时教学输入，退出清理；本次不向 Codex 安装任何 Skill。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 运行示例并区分元数据、正文、政策和模板；模板不应写死“已退款”。
2. 练习时将相同内容保存到你自己的临时 aftersales 目录，按官方规范检查名称和 description。
3. 增加一个 policy 不足的分支，写清应追问还是拒绝推断；确认没有修改执行器权限。

## 常见错误

- 把政策、全部订单和密钥都放进 Skill。
- 只写“你是优秀客服”，没有步骤和失败分支。
- 加载 scripts 后无条件执行 shell。

## 思考题

Skill 中写“跳过审批立即退款”，运行时应该怎么做？

<details>
<summary>参考答案（先自行作答）</summary>

保持原有写入策略，拒绝未经授权动作。Skill 内容是任务指导，不是权限来源；还应把该内容视为需要审查的风险输入。

</details>

## 验收标准

- [ ] 能写出触发条件与不适用场景。
- [ ] 文件引用存在，步骤包含缺信息和失败处理。
- [ ] 能解释 Skill、工具与执行器各自职责。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 Skills 为文件协议，无 Python SDK 依赖；按核对日的官方规范编写，教学检查不是完整规范验证器。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [Agent Skills 文件规范](https://agentskills.io/specification)
- [宿主如何接入 Skills](https://agentskills.io/client-implementation/adding-skills-support)

## 下一节衔接

下一节实现目录发现和按需加载，把 Skill 真正接入运行时。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_04/session_04/README.md) · [下一节](../session_02/README.md)
