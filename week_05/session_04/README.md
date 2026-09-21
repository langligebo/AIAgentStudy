# 第 05 模块 Session 04：Skill 包验证、依赖与宿主生命周期

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

把可加载的文档包变成可审查、可回退的运行时资源，区分 Skill、插件、钩子和权限。

## 前置知识与学习安排

第五模块前三节及工具执行器。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

Skill 是任务指导与配套资源，插件可以打包工具、配置与 Skill，hook/middleware 是宿主执行前后插入的代码。只有宿主实现加载、选择、资源访问和执行流程时内容才生效。文件写 allowed-tools 不能在所有实现中自动获得权限，该字段支持也随宿主而异。

一个可审查包需要规范元数据、明确依赖、相对资源路径、固定版本/内容摘要和支持的平台。读取要限制目录、大小和引用深度；执行脚本还需要进程、文件、网络、时间与输出限制。路径 resolve 能挡住部分逃逸，不是完整沙箱，也不能单靠字符串检查消除文件替换竞争。

before_tool hook 适合检查授权与预算，after_tool 适合验证输出和记录观察；任何 hook 都不能把执行失败改成成功，也不能在日志中输出凭据。允许列表取交集，未知能力默认拒绝。更新包时重新校验内容摘要、依赖与回归集，不能只相信相同的版本号。

本例验证内存清单与授权交集，不执行下载包或脚本；实际 Skill 文件解析沿用规范验证器，而不是用正则声称完整 YAML 支持。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
import hashlib
from pathlib import PurePosixPath

FILES = {"SKILL.md": b"name: aftersales", "references/policy.md": b"v1 policy"}
EXPECTED = {p: hashlib.sha256(b).hexdigest() for p, b in FILES.items()}

def validate(files, manifest):
    if set(files) != set(manifest): raise ValueError("inventory_changed")
    for name, data in files.items():
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts: raise ValueError("path_escape")
        if len(data) > 4096: raise ValueError("too_large")
        if hashlib.sha256(data).hexdigest() != manifest[name]: raise ValueError("content_changed")
    return True

def before_tool(requested, host_allowed, user_allowed):
    return requested in (set(host_allowed) & set(user_allowed))

assert validate(FILES, EXPECTED)
assert before_tool("get_order", {"get_order"}, {"get_order"})
assert not before_tool("create_ticket", {"get_order"}, {"create_ticket"})
bad = {**FILES, "references/policy.md": b"changed"}
try: validate(bad, EXPECTED)
except ValueError: pass
else: raise AssertionError("changed package accepted")
try: validate({"../secret": b"x"}, {"../secret": hashlib.sha256(b"x").hexdigest()})
except ValueError: pass
else: raise AssertionError("escape accepted")
print("PASS：清单、内容变更、路径与权限交集")
```

**预期现象：**内容被修改或资源越界时拒绝；包声明不能扩大宿主允许范围。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 为售后 Skill 记录全部引用、内容摘要、系统/包依赖与加载顺序。
2. 验证缺引用、同版本内容改变、超大文件、符号链接与不兼容依赖。
3. 设计钩子顺序：输入校验→权限→预算→执行→输出校验→脱敏观察，说明失败如何传播。
4. 在隔离环境内再测试受控脚本；不把本例清单验证当执行隔离证明。

## 常见错误

- 把校验文件清单等同于可信来源。
- 每个 hook 各自重试，造成重试乘法。
- 版本号没变就跳过回归。

## 思考题

包声称需要读取所有用户订单，宿主应该自动放行吗？

<details>
<summary>参考答案（先自行作答）</summary>

不能。兼容性或权限声明表达需求，最终允许范围由可信配置和用户授权决定，授权不足时明确不支持。

</details>

## 验收标准

- [ ] 能区分 Skill 指导、插件打包与宿主执行扩展。
- [ ] 资源和权限都可在加载/执行前拒绝。
- [ ] 同版本内容变化也触发重新审查与测试。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Agent Skills 规范](https://agentskills.io/specification)
- [Skill 接入生命周期](https://agentskills.io/client-implementation/adding-skills-support)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../../week_06/session_01/README.md)
