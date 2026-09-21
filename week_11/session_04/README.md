# 第 11 模块 Session 04：远程 MCP、能力协商与授权

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

把本地 stdio 实验扩展到远程信任边界，理解认证、授权和版本兼容的不同职责。

## 前置知识与学习安排

第十一模块前三节与第二模块 HTTP 协议。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

本地 stdio 由宿主启动子进程，远程 HTTP 服务可能由多个用户同时使用。握手成功只证明协商完成，不能证明身份或业务权限。Host 管理用户同意和会话，Server 根据已验证身份检查工具/资源；Prompts 和 Resources 也不能绕过访问控制。

现有课程例固定 MCP 2025-06-18 与 mcp 1.20.0；2026-09-21 核对的 latest 指向 2026-07-28。旧 SDK 不应被宣称支持最新所有能力。本节旧版传输依据固定 2025-06-18 Streamable HTTP 文档，升级时逐项检查传输、会话、发现和授权变化，保留兼容测试。

远程授权需要可信 issuer、目标 resource/audience、有效期、scope 与具体资源权限。OAuth 的授权码/PKCE、资源元数据发现和回调验证属于专门实现；不要自写几行 JWT 解码就叫认证，也不要把上游 access token 原样转发给任意工具服务器。此处代码仅接受“认证组件已经验证”的声明夹具。

能力协商还涉及 resources、prompts、tools，以及 sampling、elicitation、roots 等方向的支持差异。服务端请求模型采样或用户信息不代表可以自动获准；宿主仍控制数据和调用预算。新版可选能力逐项标支持/不支持/未验证，不能用一个布尔 MCP_supported 概括。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
def authorize(claims, resource, action, owner, now=100):
    # claims 仅代表已由可信组件验证过签名/issuer 的结果，不解析原始 token。
    if not claims.get("verified"): return "unauthenticated"
    if claims["issuer"] != "trusted-issuer" or claims["aud"] != resource: return "wrong_target"
    if claims["exp"] <= now: return "expired"
    if action not in claims["scopes"]: return "insufficient_scope"
    if claims["subject"] != owner: return "forbidden_resource"
    return "allowed"

claims = {"verified":True,"issuer":"trusted-issuer","aud":"orders-service",
          "exp":200,"scopes":{"orders:read"},"subject":"u1"}
assert authorize(claims,"orders-service","orders:read","u1") == "allowed"
assert authorize(claims,"another-service","orders:read","u1") == "wrong_target"
assert authorize(claims,"orders-service","orders:read","u2") == "forbidden_resource"
assert authorize(claims,"orders-service","orders:write","u1") == "insufficient_scope"
assert authorize(claims,"orders-service","orders:read","u1",200) == "expired"
assert authorize({**claims,"verified":False},"orders-service","orders:read","u1") == "unauthenticated"
print("PASS：声明后的授权策略；不是 OAuth/JWT 实现")
```

**预期现象：**正确身份及 scope 可读，错误 audience、过期、越权均被拒绝。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 用时序图区分客户端、资源服务器、授权服务器与用户同意。
2. 对当前 SDK 建版本/传输/能力矩阵，读固定版本规范，不用 latest 示例直接替换旧代码。
3. 到本课时在本地受控 HTTP 测试服务中验证握手、401、scope 不足、会话恢复及断线；不暴露真实业务。
4. 加入资源读取、模板获取、分页发现、连接关闭和取消；每类错误不能折叠成业务无结果。
5. 比较新版授权发现要求与旧例，升级前运行兼容和负例；本次不升级公共依赖。

## 常见错误

- 用 session_id 当用户认证。
- 能 tools/list 就能执行所有工具。
- 解析 token payload 未验签就相信 subject。

## 思考题

模型生成一个 user_id 参数，能否用于远程 MCP 授权？

<details>
<summary>参考答案（先自行作答）</summary>

不能。身份来自可信认证上下文；模型参数仅是请求数据，不能替换请求者身份。

</details>

## 验收标准

- [ ] 能画出授权与业务权限的完整路径。
- [ ] 旧版教学例与新规范能力有明确边界。
- [ ] 未经验证的声明、跨用户资源和错误 audience 均拒绝。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [MCP 2025-06-18 传输](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
- [MCP 2026-07-28 授权](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [当前协议规范](https://modelcontextprotocol.io/specification/2026-07-28)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../session_05/README.md)
