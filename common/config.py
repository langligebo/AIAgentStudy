"""读取项目根目录的统一配置，不依赖当前终端所在目录。"""

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.toml"


@dataclass(frozen=True)
class OllamaConfig:
    host: str
    model: str
    timeout: float

    def __post_init__(self) -> None:
        if not isinstance(self.host, str) or not self.host.strip():
            raise ValueError("ollama.host 必须是非空的 HTTP/HTTPS 服务地址。")
        address = urlsplit(self.host)
        if (
            self.host != self.host.strip()
            or any(char.isspace() for char in self.host)
            or address.scheme not in ("http", "https")
            or not address.hostname
            or address.query
            or address.fragment
            or address.username is not None
            or address.password is not None
        ):
            raise ValueError("ollama.host 必须是 HTTP/HTTPS 地址，不含空白、凭据、查询参数或片段。")
        if address.port is not None and not 1 <= address.port <= 65535:
            raise ValueError("ollama.host 的端口必须在 1～65535 之间。")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("ollama.model 必须是非空的模型名称。")
        if self.model != self.model.strip():
            raise ValueError("ollama.model 的首尾不能包含空白。")
        if (
            isinstance(self.timeout, bool)
            or not isinstance(self.timeout, (int, float))
            or not math.isfinite(self.timeout)
            or self.timeout <= 0
        ):
            raise ValueError("ollama.timeout 必须是大于 0 的有限秒数。")


def load_ollama_config(path: str | Path = CONFIG_PATH) -> OllamaConfig:
    """读取 [ollama] 配置；缺失或错误时明确报错，不退回其他地址。"""
    with Path(path).open("rb") as file:
        document = tomllib.load(file)
    section = document.get("ollama")
    if not isinstance(section, dict):
        raise ValueError(f"{path} 缺少 [ollama] 配置。")
    missing = {"host", "model", "timeout"} - section.keys()
    if missing:
        raise ValueError(f"{path} 的 [ollama] 缺少字段：{', '.join(sorted(missing))}。")
    return OllamaConfig(
        host=section["host"],
        model=section["model"],
        timeout=section["timeout"],
    )
