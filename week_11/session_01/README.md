# 第 11 周 Session 01：MCP 架构、发现与调用协议

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_10/session_05/README.md) · [下一节](../session_02/README.md)

> 材料已准备；学习状态以[进度记录](../../LEARNING_PROGRESS.md)为准。生成本教案不推进当前学习位置。

## 本节目标

区分 Host、Client、Server，追踪初始化、工具发现、调用和错误层次。

## 前置知识与学习安排

第 3 周模型工具调用协议；JSON 请求与响应。

建议用约 2 小时完成：先理解概念，再运行最小例子，最后做改动实验与验收；原 week 现为模块编号，每模块总时长按实际课时和验收安排。下面的例子自带模拟数据，不依赖其他课尚未创建的模块。

## 核心概念

Host 是承载用户与模型的应用；MCP Client 是宿主连接某服务的协议组件；Server 暴露工具、资源或提示模板。模型 tool_calls 是决策输出，MCP 是应用访问外部能力的协议；Skill 是任务方法，三者不互相替代。

本课程协议教学固定 2025-06-18 版本，后续版本以握手协商和能力集为准，不把版本字符串写死后宣称兼容所有服务器。典型流程包括 initialize 请求及协商、initialized 通知、tools/list、tools/call。请求有 ID，通知没有；响应需要与请求 ID 匹配。

协议错误通过 JSON-RPC error 表示；工具执行层失败可在 CallToolResult 中用 isError 表示。网络、发现和执行失败不能混为“没查到订单”。stdio 通过子进程标准输入输出传输协议，服务日志应走 stderr；远程通常使用 Streamable HTTP，认证、会话和授权需额外配置。

## 最小示例：可离线运行

在项目根目录运行 `uv run python -`，粘贴下面完整代码块，按 Ctrl-D 结束输入并执行；也可按[统一运行方法](../../README.md#文内示例怎么运行)通过标准输入运行。除明确标注依赖顺序的扩展外，每节最小示例独立执行。断言同时覆盖正常与失败或边界路径；输出只在控制台。

```python
# course: offline
import json

initialized = False
TOOLS = [{"name": "get_order", "description": "查询模拟订单", "inputSchema": {
    "type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}}]

def respond(request):
    global initialized
    method = request["method"]
    if method == "notifications/initialized":
        initialized = True
        return None
    identity = request["id"]
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                  "serverInfo": {"name": "mock-orders", "version": "1.0"}}
    elif not initialized:
        return {"jsonrpc": "2.0", "id": identity, "error": {"code": -32600, "message": "not_initialized"}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        if request["params"]["name"] != "get_order":
            return {"jsonrpc": "2.0", "id": identity, "error": {"code": -32602, "message": "unknown_tool"}}
        oid = request["params"]["arguments"].get("order_id")
        ok = oid == "A100"
        result = {"content": [{"type": "text", "text": "delivered" if ok else "not_found_or_forbidden"}], "isError": not ok}
    else:
        return {"jsonrpc": "2.0", "id": identity, "error": {"code": -32601, "message": "method_not_found"}}
    return {"jsonrpc": "2.0", "id": identity, "result": result}

def request(i, method, **params):
    return respond({"jsonrpc": "2.0", "id": i, "method": method, "params": params})

assert "error" in request(1, "tools/list")
print(request(2, "initialize", protocolVersion="2025-06-18"))
assert respond({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
assert request(3, "tools/list")["result"]["tools"] == TOOLS
normal = request(4, "tools/call", name="get_order", arguments={"order_id": "A100"})
failed = request(5, "tools/call", name="get_order", arguments={"order_id": "B200"})
assert normal["id"] == 4 and not normal["result"]["isError"]
assert failed["result"]["isError"]
assert "error" in request(6, "tools/call", name="shell", arguments={})
print(json.dumps([normal, failed], ensure_ascii=False))
print("PASS：顺序、关联 ID、正常结果、协议与工具错误")
```

**预期现象：**初始化前调用被拒绝；正常结果和工具错误位于 result，未知工具为 error。这是消息夹具，不是完整 MCP 协议栈或一致性测试。

**验证边界：**上述最小块已于 2026-09-21 实际离线运行。通过只说明这些夹具与断言通过，不证明模型效果、真实服务或用户已经掌握；下方扩展实验须另行记录证据。

## 实验步骤与练习

1. 给每条消息标出发起方和接收方，说明哪一步模型不参与。
2. 分别设计工具、资源 URI 和提示模板在客服场景中的用途，确认三者不会自动授予访问权。
3. 实际接入时使用官方 SDK 处理握手和传输，不将本例 respond 当生产服务。

## 常见错误

- 把 MCP 当模型调用协议或 Skill 格式。
- stdio 服务把调试日志写到 stdout。
- isError=True 却仍让 Agent 说查询成功。

## 思考题

MCP 服务能列出某个工具，是否就说明当前用户可以执行？

<details>
<summary>参考答案（先自行作答）</summary>

不说明。发现表示能力可见，执行仍要认证和资源授权；工具描述中的 readOnly 等提示也不能替代程序权限检查。

</details>

## 验收标准

- [ ] 能画出 Host、Client、Server 与模型的关系。
- [ ] 请求、通知、响应和错误可区分。
- [ ] 明确本次只测消息机制，未启动协议服务。

验收须结合你的解释、实际实验或明确反馈；查看参考答案和生成材料不自动勾选。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线最小示例：Python 3.12 标准库，无新增依赖；本次在 Python 3.12.0 隔离临时目录执行，禁止网络连接。 MCP 消息教学固定协议 2025-06-18；SDK 示例固定 mcp 1.20.0，仅核对 API/版本与语法，未启动服务或客户端。 本次未调用真实模型或外部服务，未部署。版本用于课程复现，不表示最新推荐版本；未来升级要重新核对接口并运行相应案例。

- [MCP 2025-06-18 生命周期](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)
- [MCP 2025-06-18 工具](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [官方 Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [mcp 1.20.0 说明与示例](https://pypi.org/project/mcp/1.20.0/)

## 下一节衔接

下一节用官方 Python SDK 封装订单工具，并接到执行适配层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../../week_10/session_05/README.md) · [下一节](../session_02/README.md)
