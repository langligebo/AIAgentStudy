"""比较同一 prompt 在不同 temperature 下的输出，仅在控制台展示结果。"""

import argparse
import sys
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from time import perf_counter


# 兼容直接运行脚本；以 python -m 运行时，项目根目录已在导入路径中。
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.llm import create_llm_client


DEFAULT_PROMPT = (
    "请为一个帮助程序员学习 AI Agent 的学习助手起 3 个中文名字。"
    "每个名字后附一句不超过 20 字的介绍。只输出三行，不要其他说明。"
)
TEMPERATURES = (0.0, 0.5, 1.0)
# 每组内使用不同种子，各温度组复用相同种子，方便配对比较。
SEEDS = (42, 43, 44)
# max_tokens 由 Ollama 适配器转换为 num_predict。
FIXED_OPTIONS = {"top_p": 0.9, "top_k": 40, "max_tokens": 512}


def summarize(results: list[dict]) -> list[dict]:
    """按温度统计文本差异；字符相似度不代表语义相似度或回答质量。"""
    summaries = []
    for temperature in TEMPERATURES:
        group = [row for row in results if row["temperature"] == temperature]
        texts = [row["output"].strip() for row in group]
        pairs = list(combinations(texts, 2))
        # 关闭 autojunk，避免较长中文回答中的重复字符被当作噪声忽略。
        similarities = [
            SequenceMatcher(None, a, b, autojunk=False).ratio() for a, b in pairs
        ]
        summaries.append(
            {
                "temperature": temperature,
                "completed_runs": len(group),
                "unique_outputs": len(set(texts)),
                "identical_pairs": sum(a == b for a, b in pairs),
                "total_pairs": len(pairs),
                "mean_character_similarity": (
                    sum(similarities) / len(similarities) if similarities else None
                ),
                "truncated_outputs": sum(row["finish_reason"] == "length" for row in group),
            }
        )
    return summaries


def print_summary(results: list[dict]) -> None:
    """输出完整或中途停止的实验统计；结果只保存在本次进程内存中。"""
    print("\nTemperature 对比统计")
    print("| 温度 | 完成次数 | 不同输出数 | 完全相同的配对 | 平均字符相似度 | 截断次数 |")
    print("| --- | --- | --- | --- | --- | --- |")
    for row in summarize(results):
        similarity = row["mean_character_similarity"]
        score = f"{similarity:.1%}" if similarity is not None else "—"
        print(
            f"| {row['temperature']:.1f} | {row['completed_runs']}/{len(SEEDS)} | "
            f"{row['unique_outputs']} | {row['identical_pairs']}/{row['total_pairs']} | "
            f"{score} | {row['truncated_outputs']} |"
        )
    print("统计仅忽略回答首尾空白；不足两次时不计算字符相似度。")
    print("字符相似度衡量文字重合程度，不代表语义一致或回答质量。")
    print("如发生截断，应提高 FIXED_OPTIONS 中的 max_tokens 后重跑完整实验。")
    print("每组仅 3 次，结果用于学习观察，不足以证明普遍规律。")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="临时覆盖 config.toml 中的模型名")
    parser.add_argument("--host", help="临时覆盖 config.toml 中的服务地址")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="全部 9 次请求共用的 prompt")
    parser.add_argument("--timeout", type=float, help="临时覆盖 config.toml 中的请求超时秒数")
    args = parser.parse_args()
    if not args.prompt.strip():
        parser.error("prompt 不能为空。")
    try:
        client = create_llm_client(host=args.host, model=args.model, timeout=args.timeout)
    except (OSError, ValueError) as exc:
        parser.error(f"模型配置错误：{exc}")

    print(
        f"服务：{client.provider}\n地址：{client.base_url}\n模型：{client.model}\n"
        f"请求超时：{client.timeout} 秒\nPrompt：{args.prompt}\n"
        f"每组种子：{list(SEEDS)}\n固定参数：{FIXED_OPTIONS}",
        flush=True,
    )
    results = []
    exit_code = 0
    try:
        for temperature in TEMPERATURES:
            for run, seed in enumerate(SEEDS, start=1):
                print(f"\n[temperature={temperature:.1f}, 第 {run}/3 次, seed={seed}]", flush=True)
                started = perf_counter()
                response = client.generate(
                    args.prompt, temperature=temperature, seed=seed, **FIXED_OPTIONS
                )
                elapsed = perf_counter() - started
                results.append(
                    {
                        "temperature": temperature,
                        "output": response.text,
                        "finish_reason": response.finish_reason,
                    }
                )
                print(response.text, flush=True)
                token_count = response.output_tokens if response.output_tokens is not None else "未知"
                print(
                    f"耗时：{elapsed:.2f} 秒；结束原因：{response.finish_reason}；"
                    f"输出 token：{token_count}",
                    flush=True,
                )
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"\n实验停止：temperature={temperature:.1f}，第 {run} 次：{exc}", file=sys.stderr)
        exit_code = 1
    except KeyboardInterrupt:
        print("\n实验已被用户中断。", file=sys.stderr)
        exit_code = 130

    print(f"\n已完成 {len(results)}/{len(TEMPERATURES) * len(SEEDS)} 次回答。")
    print_summary(results)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
