"""Configuration loader for the LiveStream Server.

Settings are loaded from ``config.json`` next to ``server_app.py`` if it
exists, otherwise sensible defaults are used. The first time the server
runs it will create a ``config.json`` with a generated API token.
"""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass, field, asdict
from threading import Lock
from typing import Any, Dict, Optional


_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(_HERE, "config.json")
EXAMPLE_PATH = os.path.join(_HERE, "config.example.json")


def _platform_default_base_dir() -> str:
    if os.name == "nt":
        return r"C:\LiveStreamServer"
    return os.path.join(_HERE)


@dataclass
class Settings:
    app_name: str = "LiveStreamServer"
    host: str = "0.0.0.0"
    port: int = 8765
    base_dir: str = field(default_factory=_platform_default_base_dir)
    videos_dir: str = ""
    logs_dir: str = ""
    bin_dir: str = ""
    ffmpeg_path: str = ""
    database_url: str = ""
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    api_token: str = ""
    auto_restart_default: bool = False
    stream_loop_default: bool = True
    max_upload_mb: int = 4096

    def fill_paths(self) -> None:
        if not self.videos_dir:
            self.videos_dir = os.path.join(self.base_dir, "videos")
        if not self.logs_dir:
            self.logs_dir = os.path.join(self.base_dir, "logs")
        if not self.bin_dir:
            self.bin_dir = os.path.join(self.base_dir, "bin")
        if not self.database_url:
            db_path = os.path.join(self.base_dir, "database.db")
            self.database_url = f"sqlite:///{db_path}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_lock = Lock()
_cached: Optional[Settings] = None


def _load_from_file(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except (OSError, json.JSONDecodeError):
        return {}


def _persist(settings: Settings) -> None:
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH) or ".", exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(settings.to_dict(), f, indent=4)
    except OSError:
        # On packaged/read-only environments we just keep the defaults in memory.
        pass


def get_settings(force_reload: bool = False) -> Settings:
    global _cached
    with _lock:
        if _cached is not None and not force_reload:
            return _cached

        data = _load_from_file(CONFIG_PATH) or _load_from_file(EXAMPLE_PATH)
        settings = Settings(**{k: v for k, v in data.items() if k in Settings.__dataclass_fields__})
        settings.fill_paths()

        if not settings.api_token:
            settings.api_token = secrets.token_urlsafe(32)
            _persist(settings)

        _cached = settings
        return settings


def update_settings(**values: Any) -> Settings:
    settings = get_settings()
    with _lock:
        for key, value in values.items():
            if key in Settings.__dataclass_fields__:
                setattr(settings, key, value)
        settings.fill_paths()
        _persist(settings)
    return settings
