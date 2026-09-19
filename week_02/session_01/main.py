"""第二周 Session 01：模型能力与请求协议探针，结果仅在控制台展示。"""

import argparse
import sys
from pathlib import Path
from time import perf_counter


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.llm import LLMConnectionError, create_llm_client
from week_02.session_01.probes import OPTIONS, PROBES, RUNNERS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=["all", *PROBES], default="all", help="选择单项实验，默认全部")
    parser.add_argument("--list", action="store_true", help="查看实验清单，不请求模型")
    parser.add_argument("--model", help="临时覆盖共享配置中的模型")
    parser.add_argument("--host", help="临时覆盖共享配置中的地址")
    parser.add_argument("--timeout", type=float, help="临时覆盖请求超时秒数")
    args = parser.parse_args()
    names = list(PROBES) if args.probe == "all" else [args.probe]
    if args.list:
        for name in names:
            title, count = PROBES[name]
            print(f"{name:12} {title}（正常完成需 {count} 次请求）")
        return 0
    try:
        client = create_llm_client(host=args.host, model=args.model, timeout=args.timeout)
    except (OSError, ValueError) as exc:
        parser.error(f"模型配置错误：{exc}")
    print(
        f"服务：{client.provider}\n地址：{client.base_url}\n模型：{client.model}\n"
        f"请求超时：{client.timeout} 秒\n默认实验参数：{OPTIONS}\n"
        f"计划：{len(names)} 项实验，正常完成共 {sum(PROBES[name][1] for name in names)} 次请求。",
        flush=True,
    )
    status = {name: "未运行" for name in names}
    exit_code = 0
    for name in names:
        print(f"\n===== {PROBES[name][0]} =====", flush=True)
        started = perf_counter()
        try:
            passed, detail = RUNNERS[name](client)
            status[name] = "通过当前样本" if passed else "当前样本未通过"
            print(f"{status[name]}：{detail}", flush=True)
        except LLMConnectionError as exc:
            status[name] = "连接失败或超时"
            print(f"\n{name}：{exc}；停止后续请求，不自动重试。", file=sys.stderr)
            exit_code = 1
            break
        except (RuntimeError, ValueError, OSError) as exc:
            status[name] = "调用或协议失败"
            print(f"\n{name}：{exc}；此项未能完成验证，继续其他独立实验。", file=sys.stderr)
            exit_code = 1
        except KeyboardInterrupt:
            status[name] = "用户中断"
            print("\n实验已被用户中断。", file=sys.stderr)
            exit_code = 130
            break
        finally:
            print(f"本项耗时：{perf_counter() - started:.2f} 秒", flush=True)

    print("\n| 实验 | 状态 |\n| --- | --- |")
    for name in names:
        print(f"| {PROBES[name][0]} | {status[name]} |")
    print("结论仅限本次模型、服务与客户端组合及当前样本；未运行或调用失败不等于模型不支持。")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
