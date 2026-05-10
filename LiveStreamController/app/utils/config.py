"""Persisted controller configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict


_HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(_HERE, "config.json")


@dataclass
class ControllerConfig:
    server_host: str = ""
    server_port: int = 8765
    use_https: bool = False
    api_token: str = ""
    username: str = "admin"
    remember_token: bool = True

    @property
    def base_url(self) -> str:
        host = self.server_host or "127.0.0.1"
        scheme = "https" if self.use_https else "http"
        port = int(self.server_port)
        # Drop the port suffix when it's the default for the scheme so URLs
        # for things like Cloudflare quick tunnels look clean
        # (https://x.trycloudflare.com instead of :443).
        if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
            return f"{scheme}://{host}"
        return f"{scheme}://{host}:{port}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_config() -> ControllerConfig:
    if not os.path.isfile(CONFIG_PATH):
        return ControllerConfig()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return ControllerConfig()
    return ControllerConfig(**{k: v for k, v in data.items() if k in ControllerConfig.__dataclass_fields__})


def save_config(config: ControllerConfig) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=4)
    except OSError:
        pass
