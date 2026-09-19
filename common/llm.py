"""统一的模型调用入口；目前实现 Ollama，后续可增加其他服务的适配器。"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from common.config import OllamaConfig, load_ollama_config


class LLMConnectionError(RuntimeError):
    """连接或读取超时，实验可据此停止后续请求。"""


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


@dataclass(frozen=True)
class LLMResponse:
    """实验代码只使用统一字段，不依赖服务商的原始 JSON 结构。"""

    text: str
    finish_reason: str
    output_tokens: int | None = None
    input_tokens: int | None = None
    tool_calls: tuple[ToolCall, ...] = ()


class LLMClient(Protocol):
    """模型客户端约定，后续适配器实现相同接口即可供 Session 使用。

    seed 和 top_k 是可选能力；新增适配器时，不支持的显式参数应报错，
    不能静默忽略。max_tokens 表示最大输出 token 数。
    """

    @property
    def provider(self) -> str: ...

    @property
    def base_url(self) -> str: ...

    @property
    def model(self) -> str: ...

    @property
    def timeout(self) -> float: ...

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        seed: int | None = None,
        top_k: int | None = None,
    ) -> LLMResponse: ...

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
        seed: int | None = None,
        context_tokens: int | None = None,
        response_schema: dict | None = None,
        tools: list[dict] | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> LLMResponse: ...


@dataclass(frozen=True)
class OllamaClient:
    base_url: str
    model: str
    timeout: float
    provider: ClassVar[str] = "ollama"

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
        seed: int | None = None,
        context_tokens: int | None = None,
        response_schema: dict | None = None,
        tools: list[dict] | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> LLMResponse:
        """显式传入历史；提供 on_text 时逐段展示，完成后才返回完整响应。

        本阶段的流式接口只处理文本，不接受同时传入 tools。
        不缓存会话、不执行工具、不自动重试。
        """
        if not messages:
            raise ValueError("messages 不能为空。")
        for message in messages:
            if (
                not isinstance(message, dict)
                or message.get("role") not in ("system", "user", "assistant", "tool")
                or not isinstance(message.get("content"), str)
            ):
                raise ValueError("每条消息需要合法的 role 和字符串 content。")
        if type(max_tokens) is not int or max_tokens <= 0:
            raise ValueError("max_tokens 必须是正整数。")
        if context_tokens is not None and (type(context_tokens) is not int or context_tokens <= 0):
            raise ValueError("context_tokens 必须是正整数。")
        if tools and on_text is not None:
            raise ValueError("当前客户端仅支持文本流式响应；工具请求请使用非流式调用。")

        options = {"temperature": temperature, "num_predict": max_tokens}
        if seed is not None:
            options["seed"] = seed
        if context_tokens is not None:
            options["num_ctx"] = context_tokens
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": on_text is not None,
            "options": options,
        }
        if response_schema is not None:
            payload["format"] = response_schema
        if tools is not None:
            payload["tools"] = tools
        request = Request(
            f"{self.base_url.rstrip('/')}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if on_text is None:
                    result = json.load(response)
                else:
                    parts = []
                    for line in response:
                        if not line.strip():
                            continue
                        chunk = json.loads(line)
                        self._check_chat_envelope(chunk)
                        message = chunk.get("message", {})
                        if not isinstance(message, dict):
                            raise RuntimeError("Ollama 的 message 必须是对象。")
                        if message.get("tool_calls"):
                            raise RuntimeError("文本流中出现工具调用，当前客户端不支持该组合。")
                        text = message.get("content", "")
                        if not isinstance(text, str):
                            raise RuntimeError("Ollama 的 message.content 必须是字符串。")
                        if text:
                            parts.append(text)
                            on_text(text)
                        if chunk["done"]:
                            result = {**chunk, "message": {"role": "assistant", "content": "".join(parts)}}
                            break
                    else:
                        raise RuntimeError("Ollama 流在 done=true 前结束，已显示的片段不能算完整回答。")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama 返回 HTTP {exc.code}：{detail}") from exc
        except URLError as exc:
            raise LLMConnectionError(f"无法连接 Ollama（{self.base_url}）：{exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMConnectionError("模型请求或读取响应超时。") from exc
        except OSError as exc:
            raise LLMConnectionError(f"读取 Ollama 响应失败：{exc}") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError("Ollama 返回的内容不是有效 JSON。") from exc

        self._check_chat_envelope(result)
        if not result["done"]:
            raise RuntimeError("Ollama 未返回完整响应。")
        message = result.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Ollama 的 message 必须是对象。")
        text = message.get("content", "")
        if not isinstance(text, str):
            raise RuntimeError("Ollama 的 message.content 必须是字符串。")
        raw_calls = message.get("tool_calls", [])
        if not isinstance(raw_calls, list):
            raise RuntimeError("Ollama 的 tool_calls 必须是数组。")
        calls = []
        for call in raw_calls:
            function = call.get("function") if isinstance(call, dict) else None
            if (
                not isinstance(function, dict)
                or not isinstance(function.get("name"), str)
                or not function["name"].strip()
                or not isinstance(function.get("arguments"), dict)
            ):
                raise RuntimeError("Ollama 返回了无效的工具名称或参数结构。")
            calls.append(ToolCall(function["name"], function["arguments"]))
        finish_reason = result.get("done_reason", "unknown")
        if not text.strip() and not calls and finish_reason != "length":
            raise RuntimeError("Ollama 返回了空回答，且没有工具调用。")
        return LLMResponse(
            text=text,
            finish_reason=finish_reason,
            output_tokens=result.get("eval_count"),
            input_tokens=result.get("prompt_eval_count"),
            tool_calls=tuple(calls),
        )

    @staticmethod
    def _check_chat_envelope(result: object) -> None:
        if not isinstance(result, dict):
            raise RuntimeError("Ollama 返回的内容不是 JSON 对象。")
        if result.get("error"):
            raise RuntimeError(f"Ollama 错误：{result['error']}")
        if type(result.get("done")) is not bool:
            raise RuntimeError("Ollama 响应缺少合法的 done 标记。")

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 512,
        top_p: float = 0.9,
        seed: int | None = None,
        top_k: int | None = None,
    ) -> LLMResponse:
        """一次独立、非流式请求；不携带历史上下文，也不自动重试。"""
        if not prompt.strip():
            raise ValueError("prompt 不能为空。")
        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "top_p": top_p,
        }
        if seed is not None:
            options["seed"] = seed
        if top_k is not None:
            options["top_k"] = top_k
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        request = Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.load(response)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama 返回 HTTP {exc.code}：{detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"无法连接 Ollama（{self.base_url}）：{exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError("模型请求超时，请增加请求超时配置。") from exc
        except ValueError as exc:
            raise RuntimeError("Ollama 返回的内容不是有效 JSON。") from exc

        if not isinstance(result, dict):
            raise RuntimeError("Ollama 返回的内容不是 JSON 对象。")
        if result.get("error"):
            raise RuntimeError(f"Ollama 错误：{result['error']}")
        if result.get("done") is not True:
            raise RuntimeError("Ollama 未返回完整响应。")
        if not isinstance(result.get("response"), str) or not result["response"].strip():
            raise RuntimeError("Ollama 返回了空回答，无法用于比较。")
        return LLMResponse(
            text=result["response"],
            finish_reason=result.get("done_reason", "unknown"),
            output_tokens=result.get("eval_count"),
        )


def create_llm_client(
    *, host: str | None = None, model: str | None = None, timeout: float | None = None
) -> LLMClient:
    """读取共享配置并应用临时覆盖；今后在这里选择其他服务的适配器。"""
    defaults = load_ollama_config()
    config = OllamaConfig(
        host=host if host is not None else defaults.host,
        model=model if model is not None else defaults.model,
        timeout=timeout if timeout is not None else defaults.timeout,
    )
    return OllamaClient(base_url=config.host, model=config.model, timeout=config.timeout)
