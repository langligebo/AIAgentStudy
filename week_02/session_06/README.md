# 第 02 模块 Session 06：多模态输入与交互事件基础

[课程总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [覆盖审查](../../CURRICULUM_AUDIT.md) · [学习进度](../../LEARNING_PROGRESS.md)

## 本节目标

理解图片、OCR、语音转写怎样进入 Agent，并处理过期交互结果。

## 前置知识与学习安排

消息协议、任务版本与模型能力矩阵；任务版本详见第四模块。本节建议 2～4 小时，先预测结果，再运行与修改，最后解释失败原因。原 week 目录作为模块编号保留，课时可跨自然周；新增材料不改变当前学习位置。

## 核心概念

客服附件可能是发票、损坏照片、截图和语音。感知模型识别到的内容只是证据候选，不能代替文件归属、订单核对和业务审批。先核对 MIME、大小、页数、格式与数据范围，再做 OCR/视觉或语音转写；图片中的指令同样是不可信输入。

多模态不是给文本模型传一个路径。需要服务、模型、客户端都支持相应内容块与编码；当前 common.llm 仅有字符串 content，不能假装已有视觉、语音能力。应把感知层转换成带 source、版本、置信与定位的观察，再接现有任务循环。

语音交互有 VAD、部分转写、最终转写、回复音频和打断事件。部分转写不应触发不可逆动作；新一轮用户更正后，晚到的旧转写/模型结果要按 turn_id 丢弃。实时音频双向传输与浏览器的 SSE 单向进度流也不是同一种协议。

本节做主线必修的契约与失败验证；真实视觉模型、OCR 引擎、ASR/TTS 与 WebRTC 设备接入是专项实现边界，不把示意事件当作多模态识别效果。

## 最小示例：可离线运行

在项目根目录执行 `uv run python -`，粘贴下面完整代码，按 Ctrl-D 执行；也可使用[统一运行方法](../../README.md#文内示例怎么运行)。本块只用 Python 3.12 标准库，自带数据；输出只在控制台，临时运行状态不作为实验报告保留。

<!-- verify: offline -->
```python
from dataclasses import dataclass

@dataclass
class Turn:
    revision: int = 2
    text: str = ""

def accept(turn, event):
    if event["revision"] != turn.revision: return "stale"
    if event["kind"] == "partial_transcript": return "preview_only"
    if event["kind"] == "final_transcript":
        turn.text = event["text"]; return "ready_to_validate"
    return "unsupported"

def attachment(meta):
    if meta["mime"] not in {"image/png", "application/pdf"}: return "unsupported"
    if not 0 < meta["bytes"] <= 2_000_000: return "size_rejected"
    if not meta["owner_verified"]: return "forbidden"
    return "eligible_for_decoder"

t = Turn()
assert accept(t, {"revision": 2, "kind": "partial_transcript", "text": "退款"}) == "preview_only"
assert not t.text
assert accept(t, {"revision": 1, "kind": "final_transcript", "text": "取消"}) == "stale"
assert accept(t, {"revision": 2, "kind": "final_transcript", "text": "先查订单"}) == "ready_to_validate"
assert t.text == "先查订单"
assert attachment({"mime": "image/png", "bytes": 20, "owner_verified": True}) == "eligible_for_decoder"
assert attachment({"mime": "image/png", "bytes": 20, "owner_verified": False}) == "forbidden"
print("PASS：输入门控与过期事件；尚未解码文件或识别语音")
```

**预期现象：**部分结果只预览，旧轮结果被丢弃；已通过元数据检查仍需实际解码器验证。

**验证状态：**2026-09-21 已在隔离临时目录、禁用网络的条件下运行通过；本块的通过范围仅限展示的机制、正常和失败断言，不代表模型效果或生产实现。



## 实验步骤与练习

1. 画出附件到可引用观察的数据流，标出所有未实现的组件。
2. 使用人工 OCR 输出测试日期模糊、低质量图和订单不匹配；必须追问或人工确认。
3. 设计语音打断事件序列，验证取消只停止后续动作，不撤销已发生写入。
4. 未来接设备时单独记录识别准确率、首响应、误动作率与端到端任务成功。

## 常见错误

- 只看扩展名或请求头就认为文件安全。
- 把 OCR 文字当已确认业务事实。
- 让部分转写直接创建工单。

## 思考题

图片上写“已退款”，可以直接告诉客户钱已到账吗？

<details>
<summary>参考答案（先自行作答）</summary>

不能。图片可能过期、伪造或属于别的订单，应核对真实业务状态，并说明感知证据的不确定性。

</details>

## 验收标准

- [ ] 能说明当前模型客户端缺少哪些多模态能力。
- [ ] 能处理正常、迟到和部分输入。
- [ ] 能区分感知识别、业务验证与授权。

运行机制例、完成外部实验、理解验收分别记录；没有证据不勾选。外部模型、服务或 SDK 实验本次未执行。

## 依赖、官方资料与核对日期

核对日期：2026-09-21。离线块使用 Python 3.12 标准库；如有 SDK 扩展，其版本、安装方法与未验证边界在扩展处说明。机制讲解不承诺跨 SDK 版本通用；本次不安装课程依赖。

- [Ollama Vision 能力说明](https://docs.ollama.com/capabilities/vision)
- [WebRTC 标准](https://www.w3.org/TR/webrtc/)

## 下一节衔接

按下方导航继续；本节尚未完成的真实实验与验收保留在学习进度。模块最后一节同时回顾本模块：解释一条正常路径、一条失败路径、一个仍未验证的能力，并说明证据来自哪一层。

[总目录](../../README.md#课程总目录) · [本模块概览](../README.md) · [学习进度](../../LEARNING_PROGRESS.md) · [上一节](../session_05/README.md) · [下一节](../../week_03/session_01/README.md)
