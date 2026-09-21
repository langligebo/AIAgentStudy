# 第 11 周 Session 02：Python MCP 服务与客户端适配

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

把订单查询封装为 MCP 工具，将发现的元数据转换为模型工具说明，并保留可信身份和错误状态。

## 前置知识与学习安排

上一节协议流程、工具执行器和 asyncio。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

服务端负责业务与权限，客户端负责协议会话，宿主适配层将 MCP inputSchema 转成模型工具参数描述。若连接多个服务器，应使用命名空间防冲突，内部映射到固定 server 和 tool，不让模型指定任意服务 URL 或进程命令。

本节服务示例使用官方 `mcp` 包中的 FastMCP，不是另一个同名第三方包。只暴露一个订单号参数；用户身份由受信宿主启动上下文模拟提供，真实部署必须改为已认证请求上下文。环境变量并非多用户认证方案。

离线示例测试元数据转换与错误保留；后面的完整 server/client 示例需要额外依赖，当前未安装和启动。客户端必须先 initialize，再发现和调用，检查 isError 后才可把观察交给模型。工具文本仍是不可信内容，不能变成系统权限。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
REMOTE = [{"name": "get_order", "description": "查询当前用户的模拟订单", "inputSchema": {
    "type": "object", "properties": {"order_id": {"type": "string"}},
    "required": ["order_id"], "additionalProperties": False}}]
MAPPING = {"orders__get_order": ("orders", "get_order")}

def descriptors():
    return [{"type": "function", "function": {
        "name": "orders__" + t["name"], "description": t["description"], "parameters": t["inputSchema"]}}
        for t in REMOTE if "orders__" + t["name"] in MAPPING]

def adapt_result(result):
    if not isinstance(result, dict) or not isinstance(result.get("content"), list):
        raise ValueError("invalid_protocol_result")
    return {"ok": not result.get("isError", False), "content": result["content"]}

def resolve(name):
    if name not in MAPPING:
        raise ValueError("unregistered_remote_tool")
    return MAPPING[name]

assert descriptors()[0]["function"]["parameters"] == REMOTE[0]["inputSchema"]
assert resolve("orders__get_order") == ("orders", "get_order")
normal = adapt_result({"isError": False, "content": [{"type": "text", "text": "delivered"}]})
failure = adapt_result({"isError": True, "content": [{"type": "text", "text": "forbidden"}]})
assert normal["ok"] and not failure["ok"]
for bad in ("shell", "https://untrusted/tool"):
    try:
        resolve(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("不应动态接入未知服务")
try:
    adapt_result({"error": "disconnected"})
except ValueError:
    pass
else:
    raise AssertionError("连接失败不能伪装成正常结果")
print(descriptors(), normal, failure)
print("PASS：元数据映射、命名空间、失败保留、未知服务拒绝")
```

**预期现象：**模型看到 orders__get_order；宿主映射到已连接服务的 get_order；isError 不丢失，未知名称和协议错误被拒绝。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

### 官方 SDK 练习（本次未启动服务）

固定 `mcp==1.20.0`。练习时将以下两块分别保存为临时 `/tmp/course_mcp_server.py` 与 `/tmp/course_mcp_client.py`。这是完整示例，没有待实现的课程模块。仅在本机测试数据上运行。

服务端：

```python
# course: optional
import os
from mcp.server.fastmcp import FastMCP

server = FastMCP("course-orders")
# 仅为本机单用户练习；不是远程认证机制。
TRUSTED_USER = os.environ.get("COURSE_TRUSTED_USER")
ORDERS = {"A100": {"owner": "u1", "status": "delivered"}}

@server.tool()
def get_order(order_id: str) -> dict:
    """查询当前已认证用户的模拟订单，不返回其他用户信息。"""
    row = ORDERS.get(order_id)
    if row is None or row["owner"] != TRUSTED_USER:
        raise ValueError("not_found_or_forbidden")
    return {"order_id": order_id, "status": row["status"]}

if __name__ == "__main__":
    server.run(transport="stdio")
```

客户端：

```python
# course: optional
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command=sys.executable, args=["/tmp/course_mcp_server.py"],
                                   env={"COURSE_TRUSTED_USER": "u1"})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            discovered = await session.list_tools()
            allowed = {"get_order"}
            tools = [{"type": "function", "function": {"name": "orders__" + t.name,
                      "description": t.description or "", "parameters": t.inputSchema}}
                     for t in discovered.tools if t.name in allowed]
            assert tools and tools[0]["function"]["name"] == "orders__get_order"
            for oid, expected_error in (("A100", False), ("B200", True)):
                result = await session.call_tool("get_order", arguments={"order_id": oid})
                assert bool(result.isError) == expected_error
                print(oid, result.model_dump(mode="json"))
            print("模型工具目录：", tools)

if __name__ == "__main__":
    asyncio.run(main())
```

运行客户端会按固定路径启动服务子进程，不需要另开服务终端：

```bash
uv run --with 'mcp==1.20.0' python /tmp/course_mcp_client.py
```

预计 A100 返回状态，B200 返回执行错误。它只测试本地 stdio；没有验证远程认证、TLS 或 Streamable HTTP，不能直接暴露为局域网多用户服务。此处不调用真实模型，实际与模型的联调仍待课堂完成。
## 实验步骤与练习

1. 运行下面的真实 SDK 练习后，比较 tools/list 的 inputSchema 与离线声明差异。
2. 集成模型时把转换后的 tools 交给公共 client.chat；只按白名单映射 dispatch，再把成功或错误观察回传，不在此复制客户端。
3. 把可信用户换成 u2 并请求 A100，验证服务端拒绝；不要向模型增加 user_id 参数绕过身份上下文。

## 常见错误

- 把 mcp.server.fastmcp 与独立 fastmcp 包混用。
- 客户端同名工具发生碰撞。
- 让模型传用户 ID 决定服务授权。

## 思考题

为什么客户端做了身份检查，服务端还应检查订单归属？

<details>
<summary>参考答案（先自行作答）</summary>

服务端是数据访问的最终边界。客户端可能有漏洞或被替换，服务不能只信工具参数；它必须把已认证身份与资源归属对应起来。

</details>

## 验收标准

- [ ] 元数据能正确映射，返回错误不丢。
- [ ] 服务端权限不能被参数覆盖。
- [ ] SDK 通信是否实跑独立记录。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 MCP 消息教学固定协议 2025-06-18；SDK 示例固定 mcp 1.20.0，仅核对 API/版本与语法，未启动服务或客户端。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [MCP 2025-06-18 生命周期](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)
- [MCP 2025-06-18 工具](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [官方 Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [mcp 1.20.0 说明与示例](https://pypi.org/project/mcp/1.20.0/)

## 下一节衔接

下一节用恶意资料和越权请求验证边界，而不是仅给 Prompt 加一句安全提醒。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_01/README.md) · [下一节](../session_03/README.md)
