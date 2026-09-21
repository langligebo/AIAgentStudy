"""可靠调用教学实验：默认离线故障注入，--mode baseline 才请求模型。"""

import argparse
import json
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from time import perf_counter

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.llm import LLMConnectionError, LLMResponse, ToolCall, create_llm_client
from week_01.session_03.cases import Case
from week_01.session_03.main import check_output
from week_01.session_03.prompts import OUTPUT, ROLE, RULES, TASK
from week_02.session_03.cases import DATASET_VERSION, SPLITS

PROMPT_VERSION = "week02-s03-v1"
OPTIONS = {"temperature": 0.0, "seed": 42, "max_tokens": 256, "context_tokens": 4096}
SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"enum": ["咨询", "投诉", "售后", None]},
        "needs_clarification": {"type": "boolean"},
    },
    "required": ["category", "needs_clarification"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Result:
    status: str
    elapsed_s: float
    detail: str = ""
    response: LLMResponse | None = None
    json_ok: bool = False
    schema_ok: bool = False


def build_messages(message: str) -> list[dict]:
    # 不接收 Case.expected，避免将评分答案放进模型输入。
    return [
        {"role": "system", "content": "\n".join((ROLE, TASK, *RULES, OUTPUT))},
        {"role": "user", "content": message},
    ]


def evaluate_call(call: Callable[[], LLMResponse], case: Case) -> Result:
    started = perf_counter()
    try:
        response = call()
    except LLMConnectionError as exc:
        return Result("connection_or_timeout", perf_counter() - started, str(exc))
    except (RuntimeError, ValueError, OSError) as exc:
        return Result("call_error", perf_counter() - started, str(exc))
    except KeyboardInterrupt:
        return Result("interrupted", perf_counter() - started, "用户中断")
    elapsed = perf_counter() - started
    if response.finish_reason == "length":
        return Result("truncated", elapsed, "输出被截断，不进行业务评分", response)
    if response.finish_reason != "stop":
        return Result("unknown_finish", elapsed, "结束原因不是已知的 stop", response)
    if response.tool_calls:
        return Result("unexpected_tools", elapsed, "分类任务不执行工具", response)
    if not response.text.strip():
        return Result("empty", elapsed, "没有可验收的分类文本", response)
    check = check_output(response.text, case, response.finish_reason)
    if not check.json_ok:
        status = "invalid_json"
    elif not check.schema_ok:
        status = "invalid_schema"
    elif not check.task_ok:
        status = "wrong_answer"
    else:
        status = "ok"
    return Result(status, elapsed, check.detail, response, check.json_ok, check.schema_ok)


def run_faults() -> int:
    case = Case("F01", "送错颜色让我很不满，我要求换货。", "投诉")
    good = '{"category":"投诉","needs_clarification":false}'
    scenarios = [
        ("正常回答", LLMResponse(good, "stop"), "ok"),
        ("网络超时", LLMConnectionError("模拟超时"), "connection_or_timeout"),
        ("接口错误", RuntimeError("模拟 HTTP 400：请求参数错误"), "call_error"),
        ("空回答", LLMResponse(" ", "stop"), "empty"),
        ("合法 JSON 但截断", LLMResponse(good, "length"), "truncated"),
        ("未知结束原因", LLMResponse(good, "unknown"), "unknown_finish"),
        ("意外工具调用", LLMResponse("", "stop", tool_calls=(ToolCall("get_order", {}),)), "unexpected_tools"),
        ("JSON 损坏", LLMResponse('{"category":', "stop"), "invalid_json"),
        ("字段类型错误", LLMResponse('{"category":"投诉","needs_clarification":"false"}', "stop"), "invalid_schema"),
        ("分错类别", LLMResponse('{"category":"售后","needs_clarification":false}', "stop"), "wrong_answer"),
        ("文本拒答需复核", LLMResponse("我不能回答这个问题。", "stop"), "invalid_json"),
        ("模拟用户中断", KeyboardInterrupt(), "interrupted"),
    ]
    mismatches = 0
    print("离线故障注入：不连接模型；通过表示程序识别了预设结果。")
    for name, value, expected in scenarios:
        def fake_call(value=value):
            if isinstance(value, BaseException):
                raise value
            return value
        result = evaluate_call(fake_call, case)
        passed = result.status == expected
        mismatches += not passed
        print(f"{name}: {result.status}；预期 {expected}；{'通过' if passed else '未通过'}")
    print(f"故障场景匹配：{len(scenarios) - mismatches}/{len(scenarios)}；这不是模型能力报告。")
    return int(mismatches > 0)


def print_summary(results: list[Result], planned: int, complete: bool) -> None:
    print(f"\n已尝试/计划：{len(results)}/{planned}")
    print(f"收到响应对象：{sum(r.response is not None for r in results)}")
    print(f"JSON 通过：{sum(r.json_ok for r in results)}；契约通过：{sum(r.schema_ok for r in results)}")
    successes = sum(r.status == "ok" for r in results)
    print(f"任务成功：{successes}/{planned}")
    if complete:
        print(f"端到端任务成功率：{successes / planned:.1%}")
    else:
        print("运行未完成，不给出完整成功率；剩余样本未运行，不是已验证的模型错误。")
    print("状态分布：", dict(Counter(r.status for r in results)))
    if results:
        times = [r.elapsed_s for r in results]
        print(f"全部已尝试调用：中位数 {median(times):.3f}s；最大值 {max(times):.3f}s（含失败等待）")
    success_times = [r.elapsed_s for r in results if r.status == "ok"]
    if success_times:
        print(f"成功调用耗时中位数：{median(success_times):.3f}s；小样本不报告稳定性结论。")


def run_baseline(client, cases: tuple[Case, ...], repeat: int) -> int:
    planned = len(cases) * repeat
    print(f"模型：{client.model}；服务：{client.provider}；超时设置：{client.timeout}s")
    print(f"Prompt 版本：{PROMPT_VERSION}；数据版本：{DATASET_VERSION}；参数：{OPTIONS}")
    print(f"计划 {len(cases)} 条输入 × {repeat} 轮 = {planned} 次请求；不自动重试。", flush=True)
    results = []
    exit_code, aborted = 0, False
    try:
        for round_index in range(1, repeat + 1):
            for case in cases:
                print(f"\n轮次 {round_index} / {case.case_id}：{case.message}", flush=True)
                result = evaluate_call(
                    lambda: client.chat(build_messages(case.message), response_schema=SCHEMA, **OPTIONS),
                    case,
                )
                results.append(result)
                print(f"状态：{result.status}；调用耗时：{result.elapsed_s:.3f}s；{result.detail}")
                if result.response is not None:
                    response = result.response
                    print(f"原始回答：{response.text!r}；结束原因：{response.finish_reason}")
                    input_tokens = response.input_tokens if response.input_tokens is not None else "未知"
                    output_tokens = response.output_tokens if response.output_tokens is not None else "未知"
                    print(f"输入 token：{input_tokens}；输出 token：{output_tokens}")
                print("预期答案（仅供评分）：", json.dumps(case.expected, ensure_ascii=False), flush=True)
                if result.status in {"call_error", "connection_or_timeout"}:
                    exit_code = 1
                if result.status in {"connection_or_timeout", "interrupted"}:
                    aborted = True
                    if result.status == "interrupted":
                        exit_code = 130
                    break
            if aborted:
                break
    except KeyboardInterrupt:
        exit_code, aborted = 130, True
    print_summary(results, planned, complete=not aborted and len(results) == planned)
    print("硬件、量化、服务版本、内存峰值未自动采集；需另行注明。结果仅适用于当前样本和条件。")
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["faults", "baseline"], default="faults")
    parser.add_argument("--split", choices=list(SPLITS), default="dev")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--model", help="临时覆盖共享配置中的模型")
    parser.add_argument("--host", help="临时覆盖共享配置中的地址")
    parser.add_argument("--timeout", type=float, help="临时覆盖请求超时秒数")
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat 必须大于 0")
    if args.mode == "faults":
        return run_faults()
    try:
        client = create_llm_client(host=args.host, model=args.model, timeout=args.timeout)
    except (OSError, ValueError) as exc:
        parser.error(f"模型配置错误：{exc}")
    print(f"真实模型基线：split={args.split}；保留集不得用于反复调参。")
    return run_baseline(client, SPLITS[args.split], args.repeat)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n用户中断。", file=sys.stderr)
        raise SystemExit(130)
