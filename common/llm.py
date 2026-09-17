"""统一的模型调用入口；目前实现 Ollama，后续可增加其他服务的适配器。"""

import json
from dataclasses import dataclass
from typing import ClassVar, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from common.config import OllamaConfig, load_ollama_config


@dataclass(frozen=True)
class LLMResponse:
    """实验代码只使用统一字段，不依赖服务商的原始 JSON 结构。"""

    text: str
    finish_reason: str
    output_tokens: int | None = None


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


@dataclass(frozen=True)
class OllamaClient:
    base_url: str
    model: str
    timeout: float
    provider: ClassVar[str] = "ollama"

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
