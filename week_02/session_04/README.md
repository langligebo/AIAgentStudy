# 第 02 模块 Session 04：服务商适配、能力契约与流式组装

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

知道换服务时哪些字段必须保留，并处理跨字节边界、终止事件与残缺响应。

## 前置知识与学习安排

第二周 Session 01～03；W01 S04 的异常与迭代知识。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

统一客户端应统一业务可依赖的含义，同时保留服务差异：模型名称、请求 ID、finish reason、usage 缺失、工具调用 ID、结构化输出限制、错误类型。能力矩阵应明确支持/不支持/未验证，不能为了让接口一样而静默忽略参数。

流式响应存在三个边界：网络字节、传输事件、语义完整答案。一个 UTF-8 字符或 JSON 可能跨数据块；HTTP 200 也可能在流中返回错误。Ollama 使用 NDJSON 的教学路径与某些服务的 SSE 不同，不能用同一个逐行 JSON 解析器处理所有协议。

下例解码任意切分的 UTF-8 字节，逐行解析，再要求结束事件；缺结束事件、坏 JSON、残余半帧都失败。这里的 size 限制是资源策略，文本片段只能展示“生成中”。工具参数流应完整组装、验证后执行，绝不收到半个参数就调用工具。

当前 common.llm 支持文本流及非流式 tools，明确拒绝二者同时使用；没有通用 tool_call_id，也未实现其他服务商。新增 DeepSeek 或其他适配器时先补协定测试，再接真实开发集；语义不支持时显式返回能力错误。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
import codecs
import json

def assemble(chunks):
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer, answer, done = "", [], False
    for chunk in chunks:
        buffer += decoder.decode(chunk)
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if not line: continue
            if len(line.encode()) > 4096: raise ValueError("frame_limit")
            obj = json.loads(line)
            if done: raise ValueError("after_done")
            if obj.get("error"): raise ValueError("stream_error")
            if type(obj.get("done")) is not bool: raise ValueError("done_type")
            text = obj.get("text", "")
            if not isinstance(text, str): raise ValueError("text_type")
            answer.append(text); done = obj["done"]
            if sum(len(part) for part in answer) > 8192: raise ValueError("answer_limit")
        if len(buffer.encode()) > 4096: raise ValueError("frame_limit")
    buffer += decoder.decode(b"", final=True)
    if buffer or not done: raise ValueError("incomplete")
    return "".join(answer)

raw = ('{"text":"订单","done":false}\n{"text":"已发货","done":true}\n').encode()
assert assemble([raw[i:i+1] for i in range(len(raw))]) == "订单已发货"
frames = [json.dumps({"text": "x"*2000, "done": i == 2}) + "\n" for i in range(3)]
assert len(assemble(["".join(frames).encode()])) == 6000
for bad in [raw.split(b"\n")[0] + b"\n", b'{broken}\n', b'{"done":true}']:
    try: assemble([bad])
    except (ValueError, UnicodeError): pass
    else: raise AssertionError("incomplete accepted")
print("PASS：字节切分、完整组装、半帧与缺终止拒绝")
```

**预期现象：**逐字节输入仍拼出中文完整回答；三类损坏流均拒绝。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 解释 decoder、buffer、done 三种状态为何不能合并。
2. 增加显式流中错误、非法类型、超长帧测试。
3. 为现有客户端列能力矩阵，并设计新适配器的相同契约测试，不先修改学习实验。
4. 学到远程调用时，校对对应官方 API，集中配置和密钥；正常、429、401、截断与未知 usage 都要测试。

## 常见错误

- 把 usage 未提供记作零费用。
- 丢掉调用 ID 或改变消息顺序。
- 降级到弱模型却仍声称原安全/格式能力保持。

## 思考题

流结束但没有终止事件，可以用已显示的 JSON 吗？

<details>
<summary>参考答案（先自行作答）</summary>

不能作为成功结果；网络可能在语义完成前断开。应标残缺，按动作风险决定是否重试，禁止依靠局部工具参数执行写操作。

</details>

## 验收标准

- [ ] 流中显示的文字不能提前算业务成功。
- [ ] 能指出当前公共客户端的能力缺口。
- [ ] 新服务参数、错误与工具结果关联有可核对的契约。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Ollama 流式协议](https://docs.ollama.com/api/streaming)
- [Python 增量解码](https://docs.python.org/3.12/library/codecs.html)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_03/README.md) · [下一节](../session_05/README.md)
