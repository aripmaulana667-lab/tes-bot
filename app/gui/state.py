"""Shared GUI state container.

The tabs talk to each other through a single ``AppState``: when the input tab
chooses files, the preview/render tabs immediately see those values. The state
also persists to ``config.json`` so the next launch picks up where the user
left off.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal

from app.core.background_manager import BackgroundConfig
from app.core.logo_processor import LogoConfig
from app.core.render_engine import LyricsConfig, RenderSettings
from app.core.spectrum_engine import SpectrumConfig


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config.json"


@dataclass
class BatchPlan:
    background_mode: str = "order"
    background_folder: str = ""


@dataclass
class AppState:
    input_mode: str = "single"  # "single" | "batch"
    audio_path: str = ""
    audio_folder: str = ""
    output_dir: str = str(REPO_ROOT / "output")
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    logo: LogoConfig = field(default_factory=LogoConfig)
    lyrics: LyricsConfig = field(default_factory=LyricsConfig)
    spectrum: SpectrumConfig = field(default_factory=SpectrumConfig)
    render: RenderSettings = field(default_factory=RenderSettings)
    batch: BatchPlan = field(default_factory=BatchPlan)
    ffmpeg_path: str = ""

    def to_dict(self) -> dict:
        return {
            "input_mode": self.input_mode,
            "audio_path": self.audio_path,
            "audio_folder": self.audio_folder,
            "output_dir": self.output_dir,
            "background": asdict(self.background),
            "logo": asdict(self.logo),
            "lyrics": asdict(self.lyrics),
            "spectrum": asdict(self.spectrum),
            "render": asdict(self.render),
            "batch": asdict(self.batch),
            "ffmpeg_path": self.ffmpeg_path,
        }


class StateBus(QObject):
    """Signal hub for cross-tab notifications."""

    state_changed = Signal()
    audio_chosen = Signal(str)  # path or folder
    log_emitted = Signal(str)
    ffmpeg_status_changed = Signal(object)  # FFmpegStatus
    preview_requested = Signal()


def load_state() -> AppState:
    """Initialize from defaults + persisted ``config.json`` if available."""
    state = AppState()
    if not CONFIG_PATH.exists():
        return state
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return state

    def _apply(target, source: dict) -> None:
        for k, v in source.items():
            if hasattr(target, k):
                setattr(target, k, v)

    if "input_mode" in data:
        state.input_mode = data["input_mode"]
    if "audio_path" in data:
        state.audio_path = data["audio_path"]
    if "audio_folder" in data:
        state.audio_folder = data["audio_folder"]
    if "output_dir" in data:
        state.output_dir = data["output_dir"]
    if "ffmpeg_path" in data:
        state.ffmpeg_path = data["ffmpeg_path"]
    if "background" in data and isinstance(data["background"], dict):
        _apply(state.background, data["background"])
    if "logo" in data and isinstance(data["logo"], dict):
        _apply(state.logo, data["logo"])
    if "lyrics" in data and isinstance(data["lyrics"], dict):
        _apply(state.lyrics, data["lyrics"])
    if "spectrum" in data and isinstance(data["spectrum"], dict):
        _apply(state.spectrum, data["spectrum"])
    if "render" in data and isinstance(data["render"], dict):
        for k, v in data["render"].items():
            if hasattr(state.render, k):
                setattr(state.render, k, v)
    if "batch" in data and isinstance(data["batch"], dict):
        _apply(state.batch, data["batch"])

    # Defaults that exist in the JSON file but not on the dataclass:
    if "default_resolution" in data:
        state.render.resolution = data["default_resolution"]
    if "default_fps" in data:
        state.render.fps = int(data["default_fps"])
    if "default_quality" in data:
        state.render.quality = data["default_quality"]
    if "default_encoder" in data:
        state.render.encoder = data["default_encoder"]

    return state


def save_state(state: AppState) -> None:
    try:
        # Preserve any unknown keys already in the file.
        if CONFIG_PATH.exists():
            try:
                existing = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
        else:
            existing = {}
        existing.update(state.to_dict())
        CONFIG_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    except OSError:
        pass


__all__ = ["AppState", "BatchPlan", "StateBus", "load_state", "save_state"]
