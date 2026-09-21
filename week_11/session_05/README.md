# 第 11 模块 Session 05：执行隔离、浏览器动作与威胁建模

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

给文件、代码、浏览器和网络工具建立可测试的边界，明确沙箱保护的范围。

## 前置知识与学习安排

第三模块授权、第五模块脚本边界、第十一模块提示注入。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

攻击面不止提示注入：工具参数可触发路径遍历、命令注入、SSRF、数据外传、依赖投毒或资源耗尽；模型输出还可能进入 SQL/HTML/终端等解释器。按资产、攻击入口、信任边界、可发生副作用设计威胁模型，再把每条风险变成测试，而不是只收集恶意关键词。

代码执行应放在受限进程/容器或更强隔离中，使用非特权用户、只读基础文件、明确可写目录、无默认凭据、网络出口允许范围、CPU/内存/时间/输出上限。容器不是绝对安全边界；不把模型生成代码直接放进主进程 eval/exec，也不对可控字符串使用 shell=True。

浏览器 Agent 需观察→定位→动作→再观察；按钮点击成功不等于业务提交成功。DOM/页面文本是不可信资料，跨域跳转、文件下载上传、登录与外部提交有各自范围。可逆测试网页上验证元素消失、弹窗、旧页面与重复点击；状态未明先核对，不盲点重试。

网络允许列表还要处理 DNS、重定向与实际连接 IP，不是只解析一次 hostname。下面验证动作意图与路径约束，不发网络请求、不执行代码；它没有解决 TOCTOU 或操作系统隔离，完整执行隔离需在受控环境单独测试。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

def allowed_url(url):
    p = urlsplit(url)
    return (p.scheme == "https" and p.hostname == "support.example.test"
            and p.port in {None,443} and p.username is None and p.password is None)

def target(root, relative):
    p = (root / relative).resolve()
    if not p.is_relative_to(root.resolve()): raise PermissionError("escape")
    return p

def verify_click(before, after):
    return before["task"] == after["task"] and after["status"] == "confirmed" and bool(after.get("receipt"))

with TemporaryDirectory() as directory:
    root = Path(directory)
    assert target(root,"draft.txt").parent == root.resolve()
    try: target(root,"../secret")
    except PermissionError: pass
    else: raise AssertionError("escape")
assert allowed_url("https://support.example.test/help")
assert not allowed_url("https://support.example.test.evil.test/help")
assert not allowed_url("http://127.0.0.1/admin")
assert not verify_click({"task":"t1"},{"task":"t1","status":"clicked"})
assert verify_click({"task":"t1"},{"task":"t1","status":"confirmed","receipt":"mock-1"})
print("PASS：意图检查、路径边界、动作后核验；不是网络或执行沙箱")
```

**预期现象：**越界路径与相似域名拒绝，点击状态不能替代确认凭证。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 列出订单、凭据、知识库和运行主机四类资产，追踪输入到执行器的路径。
2. 在隔离测试目录设计读外部文件、联网、无限运行和超大输出四类负例，不在工作主机直接执行恶意脚本。
3. 在本地测试页实现查询按钮与确认状态，分别制造失效定位、重复点击和延迟确认；记录实际 DOM/业务结果。
4. 为网络工具设计重定向和 DNS 变化的连接时检查，再做受控测试；不得将本例允许列表直接用于生产防 SSRF。
5. 把结构性边界与模型抗注入成功率分开计量，加入持续安全回归。

## 常见错误

- 把检测到注入当已阻止副作用。
- 仅验证路径字符串，不验证真实文件/进程边界。
- 把测试页运行通过视为所有网站都可自动操作。

## 思考题

脚本在容器里运行，为什么还要限制凭据和网络？

<details>
<summary>参考答案（先自行作答）</summary>

容器里的程序仍可能读取挂载数据、使用环境密钥或向外发送信息；隔离、最小数据和网络策略要共同生效。

</details>

## 验收标准

- [ ] 能按威胁、控制点、测试证据组织风险。
- [ ] 每个外部动作都有执行前授权与执行后核验。
- [ ] 能说明代码示例未覆盖的沙箱与网络风险。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [OWASP LLM 风险](https://owasp.org/projects/top-10-for-large-language-model-applications)
- [Python subprocess](https://docs.python.org/3.12/library/subprocess.html)
- [Docker 安全机制](https://docs.docker.com/engine/security/)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_04/README.md) · [下一节](../../week_12/session_01/README.md)
