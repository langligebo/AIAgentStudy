"""固定样本的能力探针；只调用模型，不执行模型提出的工具请求。"""

import json
from dataclasses import asdict
from time import perf_counter

from common.llm import LLMClient, LLMResponse


PROBES = {
    "instruction": ("中文指令与消息角色", 1),
    "structured": ("接口级结构化输出", 1),
    "history": ("带历史与不带历史的对照", 3),
    "stream": ("非流式与文本流式对照", 2),
    "tools": ("最小工具调用探针", 1),
    "limits": ("输出截断观察", 1),
}
OPTIONS = {"temperature": 0.0, "seed": 42, "max_tokens": 256, "context_tokens": 4096}
ORDER_ID = "QX-731"
EXPECTED_ORDER = {"order_id": ORDER_ID, "status": "待查询"}
ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "order_id": {"type": "string"},
        "status": {"type": "string", "enum": ["待查询"]},
    },
    "required": ["order_id", "status"],
    "additionalProperties": False,
}
ORDER_MESSAGES = [
    {"role": "system", "content": "你是订单信息提取助手。只输出 JSON，不编造订单的实际状态。"},
    {
        "role": "user",
        "content": f"提取消息中的订单号：请查一下订单 {ORDER_ID}。尚未执行查询，status 必须为待查询。"
        + "输出遵守以下 JSON Schema：" + json.dumps(ORDER_SCHEMA, ensure_ascii=False),
    },
]
ORDER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_order",
        "description": "查询指定订单的实际状态。需要订单号，不能凭空编造查询结果。",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "待查询的订单号"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
    },
}


def send(client: LLMClient, messages: list[dict], **overrides) -> LLMResponse:
    """打印教学请求与响应；HTTP 处理始终在 common.llm 中。"""
    options = {**OPTIONS, **overrides}
    print("发送 messages：", json.dumps(messages, ensure_ascii=False, indent=2), flush=True)
    if "response_schema" in options:
        print("输出 Schema：", json.dumps(options["response_schema"], ensure_ascii=False), flush=True)
    if "tools" in options:
        print("工具定义：", json.dumps(options["tools"], ensure_ascii=False), flush=True)
    response = client.chat(messages, **options)
    print(f"\n完整回答：{response.text!r}", flush=True)
    if response.tool_calls:
        print("工具请求：", json.dumps([asdict(call) for call in response.tool_calls], ensure_ascii=False))
    print(
        f"结束原因：{response.finish_reason}；输入 token：{response.input_tokens}；"
        f"输出 token：{response.output_tokens}", flush=True,
    )
    return response


def matches_text(response: LLMResponse, expected: str) -> bool:
    return response.finish_reason == "stop" and not response.tool_calls and response.text.strip() == expected


def matches_order(response: LLMResponse) -> bool:
    if response.finish_reason != "stop" or response.tool_calls:
        return False
    try:
        value = json.loads(response.text)
    except ValueError:
        return False
    # 固定样本直接比对完整对象，同时检查字段、取值与实际提取结果。
    return value == EXPECTED_ORDER


def probe_instruction(client: LLMClient) -> tuple[bool, str]:
    response = send(client, [
        {"role": "system", "content": "你是中文指令测试助手。只输出用户指定的四个汉字，不加其他内容。"},
        {"role": "user", "content": "请只输出这四个汉字：学习助手"},
    ])
    return matches_text(response, "学习助手"), "期望仅返回“学习助手”；一个样本不证明所有中文指令都可靠。"


def probe_structured(client: LLMClient) -> tuple[bool, str]:
    response = send(client, ORDER_MESSAGES, response_schema=ORDER_SCHEMA)
    return matches_order(response), "期望 " + json.dumps(EXPECTED_ORDER, ensure_ascii=False) + "；接口约束后仍需校验。"


def probe_history(client: LLMClient) -> tuple[bool, str]:
    system = {"role": "system", "content": "根据本次 messages 中的对话回答。没有提供订单号时只回答：未提供。"}
    history = [system, {"role": "user", "content": f"我的订单号是 {ORDER_ID}。请只回答：收到"}]
    first = send(client, history)
    question = {"role": "user", "content": "我刚才提供的订单号是什么？只输出订单号；若不知道，只输出：未提供"}
    print("\n对照一：带上此前真实的 user 和 assistant 消息。")
    with_history = send(client, [*history, {"role": "assistant", "content": first.text}, question])
    print("\n对照二：只发送 system 和当前问题。")
    without_history = send(client, [system, question])
    passed = (
        matches_text(first, "收到")
        and matches_text(with_history, ORDER_ID)
        and matches_text(without_history, "未提供")
    )
    return passed, "期望首轮“收到”、带历史返回订单号、不带历史返回“未提供”；历史由程序随请求提交。"


def probe_stream(client: LLMClient) -> tuple[bool, str]:
    print("\n先使用非流式请求。")
    regular = send(client, ORDER_MESSAGES, response_schema=ORDER_SCHEMA)
    print("\n再逐段打印流式文本；这里只展示片段，尚不认定完整成功。", flush=True)
    started = perf_counter()
    first_text_delay = None

    def show_piece(text: str) -> None:
        nonlocal first_text_delay
        if first_text_delay is None:
            first_text_delay = perf_counter() - started
        print(text, end="", flush=True)

    streamed = send(client, ORDER_MESSAGES, response_schema=ORDER_SCHEMA, on_text=show_piece)
    if first_text_delay is not None:
        print(f"首段可见文本延迟：{first_text_delay:.2f} 秒（客户端观察值）")
    return (
        matches_order(regular) and matches_order(streamed),
        "期望两次完整 JSON 的数据都正确；不要求空格、字段顺序或分块方式相同。",
    )


def probe_tools(client: LLMClient) -> tuple[bool, str]:
    response = send(client, [
        {"role": "system", "content": "需要订单实际状态时，使用提供的工具获取，不要编造状态。"},
        {"role": "user", "content": f"请调用 get_order 查询订单 {ORDER_ID} 的状态。"},
    ], tools=[ORDER_TOOL])
    calls = response.tool_calls
    passed = (
        response.finish_reason in ("stop", "tool_calls")
        and len(calls) == 1
        and calls[0].name == "get_order"
        and calls[0].arguments == {"order_id": ORDER_ID}
    )
    print("本实验到此停止，没有实现或执行 get_order，也没有查询真实订单。")
    return passed, "检查结构化工具名与参数；普通文本写着“调用工具”不算通过。"


def probe_limits(client: LLMClient) -> tuple[bool, str]:
    print("本项临时将 max_tokens 改为 1，观察输出预算耗尽；context_tokens 仍为 4096。")
    response = send(client, [
        {"role": "user", "content": "请从数字 1 写到 50，用逗号分隔，必须写完，不能省略或概括。"},
    ], max_tokens=1)
    if response.finish_reason == "length":
        return True, "观察到输出截断；通过的是截断观察，不是“写完 50 个数字”的任务。"
    return False, "本次未观察到 length，不据此断言模型没有输出限制；结合原始回答和结束原因分析。"


RUNNERS = {
    "instruction": probe_instruction,
    "structured": probe_structured,
    "history": probe_history,
    "stream": probe_stream,
    "tools": probe_tools,
    "limits": probe_limits,
}
