"""对比三种 Prompt 的客服分类表现，所有回答和统计仅打印到控制台。"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.llm import create_llm_client
from week_01.session_03.cases import Case, TEST_CASES
from week_01.session_03.prompts import VARIANTS, build_prompt


GENERATION_OPTIONS = {
    "temperature": 0.0,
    "seed": 42,
    "top_p": 0.9,
    "top_k": 40,
    "max_tokens": 512,
}


@dataclass(frozen=True)
class CheckResult:
    json_ok: bool
    schema_ok: bool
    task_ok: bool
    detail: str


def reject_non_json_constant(value: str) -> None:
    # Python 的 JSON 解析器默认接受 NaN / Infinity，本实验按标准 JSON 拒绝它们。
    raise ValueError(f"{value} 不是标准 JSON 值")


def check_output(raw: str, case: Case, finish_reason: str = "stop") -> CheckResult:
    """原样解析 → 校验字段契约 → 比对预期答案；不清洗或修复模型输出。"""
    try:
        value = json.loads(raw, parse_constant=reject_non_json_constant)
    except (ValueError, RecursionError) as exc:
        return CheckResult(False, False, False, f"JSON 解析失败：{exc}")

    if not isinstance(value, dict):
        return CheckResult(True, False, False, "顶层必须是 JSON 对象")
    if set(value) != {"category", "needs_clarification"}:
        return CheckResult(True, False, False, "字段必须恰好为 category 和 needs_clarification")
    if value["category"] not in ("咨询", "投诉", "售后", None):
        return CheckResult(True, False, False, "category 不在允许范围内")
    if type(value["needs_clarification"]) is not bool:
        return CheckResult(True, False, False, "needs_clarification 必须是布尔值")
    if (value["category"] is None) != value["needs_clarification"]:
        return CheckResult(True, False, False, "空类别必须与需要澄清对应")

    # 即使截断前碰巧形成合法 JSON，也不将截断响应计为任务成功。
    if finish_reason == "length":
        return CheckResult(True, True, False, "响应被截断，请提高 max_tokens 后重跑完整实验")
    if value != case.expected:
        return CheckResult(True, True, False, "字段合法，但分类或澄清决策与预期答案不符")
    return CheckResult(True, True, True, "三层校验通过")


def print_summary(
    results: list[tuple[str, CheckResult | None]],
    variants: list[str],
    case_count: int,
    complete: bool,
) -> None:
    print("\n三版 Prompt 对比统计")
    print("| 版本 | 已尝试/计划 | 收到回答 | JSON 通过 | 字段通过 | 任务正确 |")
    print("| --- | --- | --- | --- | --- | --- |")
    for variant in variants:
        attempted = [result for name, result in results if name == variant]
        checks = [result for result in attempted if result is not None]
        scores = []
        for field in ("json_ok", "schema_ok", "task_ok"):
            count = sum(getattr(result, field) for result in checks)
            score = f"{count}/{case_count}"
            if complete:
                score += f" ({count / case_count:.1%})"
            scores.append(score)
        print(
            f"| {variant} | {len(attempted)}/{case_count} | {len(checks)} | "
            + " | ".join(scores) + " |"
        )
    print("分母为每个版本的全部计划样本；解析或字段失败不能从任务正确率的分母中删除。")
    if not complete:
        print("实验未完成：仅显示计数，尚未执行的样本不是已验证失败，不能据此比较版本效果。")
    print("这是小样本教学实验；版本 C 不保证更好，不能根据一次运行得出普遍结论。")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=["all", *VARIANTS], default="all", help="默认比较三个版本")
    parser.add_argument("--case", choices=[case.case_id for case in TEST_CASES], help="只运行指定测试消息")
    parser.add_argument("--preview", action="store_true", help="只打印实际 Prompt，不连接模型")
    parser.add_argument("--model", help="临时覆盖共享配置中的模型")
    parser.add_argument("--host", help="临时覆盖共享配置中的服务地址")
    parser.add_argument("--timeout", type=float, help="临时覆盖请求超时秒数")
    args = parser.parse_args()
    variants = list(VARIANTS) if args.variant == "all" else [args.variant]
    cases = [case for case in TEST_CASES if args.case is None or case.case_id == args.case]

    if args.preview:
        for case in cases:
            for variant in variants:
                print(f"\n[{variant}：{VARIANTS[variant]} / {case.case_id}]\n")
                print(build_prompt(variant, case.message))
        return 0

    try:
        client = create_llm_client(host=args.host, model=args.model, timeout=args.timeout)
    except (OSError, ValueError) as exc:
        parser.error(f"模型配置错误：{exc}")
    print(
        f"服务：{client.provider}\n地址：{client.base_url}\n模型：{client.model}\n"
        f"请求超时：{client.timeout} 秒\n固定参数：{GENERATION_OPTIONS}\n"
        f"计划：{len(variants)} 个版本 × {len(cases)} 条消息 = {len(variants) * len(cases)} 次调用",
        flush=True,
    )

    results: list[tuple[str, CheckResult | None]] = []
    exit_code = 0
    try:
        for case in cases:
            for variant in variants:
                print(f"\n[{variant}：{VARIANTS[variant]} / {case.case_id}]", flush=True)
                print(f"客户消息：{case.message}", flush=True)
                print(f"预期答案：{json.dumps(case.expected, ensure_ascii=False)}", flush=True)
                results.append((variant, None))
                started = perf_counter()
                response = client.generate(build_prompt(variant, case.message), **GENERATION_OPTIONS)
                elapsed = perf_counter() - started
                print(f"模型原始回答：\n{response.text}", flush=True)
                check = check_output(response.text, case, response.finish_reason)
                results[-1] = (variant, check)
                flags = ["通过" if passed else "未通过" for passed in (check.json_ok, check.schema_ok, check.task_ok)]
                print(f"JSON：{flags[0]}；字段：{flags[1]}；任务：{flags[2]}。{check.detail}")
                print(f"耗时：{elapsed:.2f} 秒；结束原因：{response.finish_reason}", flush=True)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"\n实验停止：版本 {variant} / {case.case_id}：{exc}", file=sys.stderr)
        exit_code = 1
    except KeyboardInterrupt:
        print("\n实验已被用户中断。", file=sys.stderr)
        exit_code = 130

    print_summary(results, variants, len(cases), complete=exit_code == 0)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
