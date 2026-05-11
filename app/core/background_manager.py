"""Background selection, preparation and multi-clip scheduling.

Provides two flavours of background:
- ``StaticBackground`` resolves a single image/video/color/gradient and is
  rendered by the render engine via an FFmpeg input.
- ``Schedule`` describes when multiple backgrounds (images and/or videos) are
  active during a song. The render engine consumes that schedule to drive a
  Python compositor when the multi-background option is enabled (ken-burns,
  fade transitions, etc.).
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi"}
ALL_BG_EXTS = IMAGE_EXTS | VIDEO_EXTS


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def is_video(path: str | Path) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTS


def is_bg_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in ALL_BG_EXTS


def list_backgrounds(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted(
        [p for p in folder.iterdir() if p.is_file() and is_bg_supported(p)]
    )


@dataclass
class BackgroundConfig:
    type: str = "color"  # "color" | "gradient" | "image" | "video"
    color: str = "#0F172A"
    color2: str = "#1E293B"
    gradient: bool = True
    path: str = ""
    fit: str = "cover"  # cover | contain | stretch
    multi_enabled: bool = False
    multi_mode: str = "manual"  # manual | folder_order | folder_random
    multi_files: list[str] = field(default_factory=list)
    multi_folder: str = ""
    interval: float = 6.0  # seconds per background in multi-mode
    transition: str = "fade"  # fade | cut
    ken_burns: bool = True


@dataclass
class BackgroundClip:
    """A single scheduled background segment."""

    start: float
    end: float
    path: Optional[str]  # None for solid/gradient
    is_video: bool = False


@dataclass
class Schedule:
    clips: list[BackgroundClip]

    def at(self, t: float) -> Optional[BackgroundClip]:
        for c in self.clips:
            if c.start <= t < c.end:
                return c
        if self.clips:
            return self.clips[-1]
        return None


def schedule_for(
    cfg: BackgroundConfig,
    duration: float,
    seed: Optional[int] = None,
) -> Schedule:
    """Build the schedule for a song.

    - Single image/video/color/gradient -> one clip spanning the song.
    - Multi-mode -> repeating list per ``cfg.interval``.
    """
    if not cfg.multi_enabled or cfg.type in ("color", "gradient") and not cfg.multi_files and not cfg.multi_folder:
        return Schedule(
            clips=[
                BackgroundClip(
                    start=0.0,
                    end=duration,
                    path=cfg.path or None,
                    is_video=cfg.type == "video" and bool(cfg.path),
                )
            ]
        )

    pool: list[Path] = []
    if cfg.multi_mode == "manual":
        pool = [Path(p) for p in cfg.multi_files if Path(p).exists()]
    elif cfg.multi_mode == "folder_order":
        pool = list_backgrounds(cfg.multi_folder)
    elif cfg.multi_mode == "folder_random":
        pool = list_backgrounds(cfg.multi_folder)

    if not pool:
        # Fallback to the single background (or color).
        return Schedule(
            clips=[
                BackgroundClip(
                    start=0.0,
                    end=duration,
                    path=cfg.path or None,
                    is_video=cfg.type == "video" and bool(cfg.path),
                )
            ]
        )

    interval = max(2.0, cfg.interval)
    clips: list[BackgroundClip] = []
    t = 0.0
    rng = random.Random(seed)
    i = 0
    while t < duration:
        if cfg.multi_mode == "folder_random":
            choice = pool[rng.randrange(0, len(pool))]
        else:
            choice = pool[i % len(pool)]
            i += 1
        end = min(duration, t + interval)
        clips.append(
            BackgroundClip(
                start=t,
                end=end,
                path=str(choice),
                is_video=is_video(choice),
            )
        )
        t = end
    return Schedule(clips=clips)


# ---------------------------------------------------------------------------
# Background <-> music matching for batch render.
# ---------------------------------------------------------------------------


def match_for_batch(
    audio_files: list[Path],
    folder: str | Path,
    mode: str = "order",
    seed: Optional[int] = None,
) -> dict[str, Optional[str]]:
    """Return a mapping ``audio_path -> background_path`` for batch mode.

    Modes:
      - "order"  : sort backgrounds by name, walk in lockstep with audio files.
      - "match"  : pair by stem name (``song.mp3`` -> ``song.jpg``/``.mp4`` etc).
      - "random" : random choice per file.
    """
    bgs = list_backgrounds(folder)
    out: dict[str, Optional[str]] = {}
    rng = random.Random(seed)
    if not bgs:
        return {str(a): None for a in audio_files}

    if mode == "match":
        bg_by_stem = {b.stem.lower(): b for b in bgs}
        for a in audio_files:
            out[str(a)] = str(bg_by_stem.get(a.stem.lower())) if a.stem.lower() in bg_by_stem else None
        return out

    if mode == "random":
        for a in audio_files:
            out[str(a)] = str(bgs[rng.randrange(0, len(bgs))])
        return out

    # order
    for i, a in enumerate(audio_files):
        out[str(a)] = str(bgs[i % len(bgs)])
    return out


__all__ = [
    "BackgroundConfig",
    "BackgroundClip",
    "Schedule",
    "IMAGE_EXTS",
    "VIDEO_EXTS",
    "ALL_BG_EXTS",
    "is_image",
    "is_video",
    "is_bg_supported",
    "list_backgrounds",
    "schedule_for",
    "match_for_batch",
]
