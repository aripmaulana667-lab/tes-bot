"""Persistent application configuration (JSON file).

The config stores user preferences and the discovered paths to external
binaries (FFmpeg, Deno) so the user does not have to add them to PATH.
"""
from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, Optional

_CONFIG_LOCK = threading.RLock()
_DEFAULTS: Dict[str, Any] = {
    # External binaries
    "ffmpeg_path": None,
    "ffprobe_path": None,
    "deno_path": None,
    # AI defaults
    "whisper_model": "base",
    "whisper_compute_type": "int8",
    "highlight_top_k": 5,
    # Output defaults
    "default_platform": "tiktok",
    "default_resolution": "1080x1920",
    "default_aspect_ratio": "9:16",
    "default_fps": "original",
    "default_crop_mode": "center",
    "default_quality": "high",
    "default_codec": "h264",
    # Subtitle defaults
    "subtitle_font": "Arial",
    "subtitle_font_size": 64,
    "subtitle_color": "white",
    "subtitle_outline_color": "black",
    "subtitle_outline_width": 4,
    "subtitle_position": "bottom-center",
    "subtitle_highlight_color": "yellow",
    "subtitle_animate": True,
    # UI
    "theme": "dark",
    "accent_color": "blue",
}


def get_project_root() -> str:
    """Return the path to the ClipFlow Studio project root.

    The project root is the parent of the ``app`` package, i.e. the folder
    that contains ``run.py`` / ``setup.bat`` / ``tools/``.
    """
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )


def get_config_dir() -> str:
    path = os.path.join(get_project_root(), "config")
    os.makedirs(path, exist_ok=True)
    return path


def get_config_path() -> str:
    return os.path.join(get_config_dir(), "config.json")


def get_tools_dir() -> str:
    path = os.path.join(get_project_root(), "tools")
    os.makedirs(path, exist_ok=True)
    return path


def get_outputs_dir() -> str:
    path = os.path.join(get_project_root(), "outputs")
    os.makedirs(path, exist_ok=True)
    return path


def get_temp_dir() -> str:
    path = os.path.join(get_project_root(), "temp")
    os.makedirs(path, exist_ok=True)
    return path


def get_assets_dir() -> str:
    path = os.path.join(get_project_root(), "assets")
    os.makedirs(path, exist_ok=True)
    return path


def get_logs_dir() -> str:
    path = os.path.join(get_project_root(), "logs")
    os.makedirs(path, exist_ok=True)
    return path


def get_database_path() -> str:
    path = os.path.join(get_config_dir(), "clipflow.db")
    return path


def _load_raw() -> Dict[str, Any]:
    path = get_config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        return data
    except (OSError, json.JSONDecodeError):
        return {}


def _save_raw(data: Dict[str, Any]) -> None:
    path = get_config_path()
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def load_config() -> Dict[str, Any]:
    """Load the merged configuration (defaults + user overrides)."""
    with _CONFIG_LOCK:
        merged = dict(_DEFAULTS)
        merged.update(_load_raw())
        return merged


def save_config(config: Dict[str, Any]) -> None:
    """Persist the *full* configuration dict."""
    with _CONFIG_LOCK:
        _save_raw(config)


def get(key: str, default: Optional[Any] = None) -> Any:
    return load_config().get(key, default if default is not None else _DEFAULTS.get(key))


def set_value(key: str, value: Any) -> None:
    with _CONFIG_LOCK:
        data = _load_raw()
        data[key] = value
        _save_raw(data)


def update(values: Dict[str, Any]) -> None:
    with _CONFIG_LOCK:
        data = _load_raw()
        data.update(values)
        _save_raw(data)


def reset() -> None:
    with _CONFIG_LOCK:
        _save_raw({})
