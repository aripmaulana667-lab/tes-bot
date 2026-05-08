"""Preset registry for output platforms, aspect ratios, and quality tiers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Aspect ratio presets
# ---------------------------------------------------------------------------
ASPECT_RATIOS: Dict[str, Tuple[int, int]] = {
    "9:16": (9, 16),  # Vertical (TikTok, Reels, Shorts)
    "1:1": (1, 1),    # Square
    "16:9": (16, 9),  # Landscape
    "4:5": (4, 5),    # Instagram feed
    "3:4": (3, 4),
    "21:9": (21, 9),  # Cinematic
}

DEFAULT_ASPECT = "9:16"


@dataclass(frozen=True)
class ResolutionPreset:
    label: str
    width: int
    height: int

    @property
    def value(self) -> str:
        return f"{self.width}x{self.height}"


# Per aspect ratio resolution catalogue
RESOLUTION_PRESETS: Dict[str, List[ResolutionPreset]] = {
    "9:16": [
        ResolutionPreset("720p", 720, 1280),
        ResolutionPreset("1080p", 1080, 1920),
        ResolutionPreset("2K", 1440, 2560),
    ],
    "1:1": [
        ResolutionPreset("720p", 720, 720),
        ResolutionPreset("1080p", 1080, 1080),
        ResolutionPreset("2K", 2048, 2048),
    ],
    "16:9": [
        ResolutionPreset("720p", 1280, 720),
        ResolutionPreset("1080p", 1920, 1080),
        ResolutionPreset("2K", 2560, 1440),
    ],
    "4:5": [
        ResolutionPreset("720p", 720, 900),
        ResolutionPreset("1080p", 1080, 1350),
    ],
    "3:4": [
        ResolutionPreset("720p", 720, 960),
        ResolutionPreset("1080p", 1080, 1440),
    ],
    "21:9": [
        ResolutionPreset("720p", 1680, 720),
        ResolutionPreset("1080p", 2520, 1080),
    ],
}


# ---------------------------------------------------------------------------
# Platform presets
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PlatformPreset:
    name: str
    aspect_ratio: str
    default_resolution: ResolutionPreset
    fps_options: Tuple[str, ...]
    notes: str = ""


def _vertical(label: str, width: int, height: int) -> ResolutionPreset:
    return ResolutionPreset(label, width, height)


PLATFORMS: Dict[str, PlatformPreset] = {
    "tiktok": PlatformPreset(
        name="TikTok",
        aspect_ratio="9:16",
        default_resolution=_vertical("1080p", 1080, 1920),
        fps_options=("original", "30", "60"),
        notes="Vertikal 9:16, 1080x1920 disarankan.",
    ),
    "reels": PlatformPreset(
        name="Instagram Reels",
        aspect_ratio="9:16",
        default_resolution=_vertical("1080p", 1080, 1920),
        fps_options=("original", "30", "60"),
        notes="Vertikal 9:16, 1080x1920 disarankan.",
    ),
    "shorts": PlatformPreset(
        name="YouTube Shorts",
        aspect_ratio="9:16",
        default_resolution=_vertical("1080p", 1080, 1920),
        fps_options=("original", "30", "60"),
        notes="Vertikal 9:16, 1080x1920 disarankan.",
    ),
    "custom": PlatformPreset(
        name="Custom",
        aspect_ratio="9:16",
        default_resolution=_vertical("1080p", 1080, 1920),
        fps_options=("original", "24", "30", "48", "60"),
        notes="Manual: pilih aspect ratio, resolusi, dan FPS sesuai kebutuhan.",
    ),
}


# ---------------------------------------------------------------------------
# Quality / codec / bitrate
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class QualityPreset:
    name: str
    crf: int
    preset: str
    audio_bitrate_kbps: int


QUALITY_PRESETS: Dict[str, QualityPreset] = {
    "draft": QualityPreset(name="Draft", crf=28, preset="veryfast", audio_bitrate_kbps=96),
    "standard": QualityPreset(name="Standard", crf=22, preset="medium", audio_bitrate_kbps=128),
    "high": QualityPreset(name="High", crf=19, preset="slow", audio_bitrate_kbps=192),
    "ultra": QualityPreset(name="Ultra / 2K", crf=17, preset="slower", audio_bitrate_kbps=256),
}


CODECS: Dict[str, Dict[str, str]] = {
    "h264": {
        "video_codec": "libx264",
        "container": "mp4",
        "pix_fmt": "yuv420p",
    },
    "h265": {
        "video_codec": "libx265",
        "container": "mp4",
        "pix_fmt": "yuv420p",
    },
}


CROP_MODES: Tuple[str, ...] = (
    "center",
    "blurred-background",
    "manual",
    "auto-face",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def list_platforms() -> List[str]:
    return list(PLATFORMS.keys())


def list_aspect_ratios() -> List[str]:
    return list(ASPECT_RATIOS.keys())


def list_resolutions(aspect_ratio: str) -> List[ResolutionPreset]:
    return RESOLUTION_PRESETS.get(aspect_ratio, RESOLUTION_PRESETS[DEFAULT_ASPECT])


def list_quality_presets() -> List[str]:
    return list(QUALITY_PRESETS.keys())


def list_codecs() -> List[str]:
    return list(CODECS.keys())


def list_crop_modes() -> Tuple[str, ...]:
    return CROP_MODES


def get_platform(name: str) -> PlatformPreset:
    return PLATFORMS.get(name.lower(), PLATFORMS["tiktok"])


def get_quality(name: str) -> QualityPreset:
    return QUALITY_PRESETS.get(name.lower(), QUALITY_PRESETS["high"])


def get_codec(name: str) -> Dict[str, str]:
    return CODECS.get(name.lower(), CODECS["h264"])


def parse_resolution(resolution: str) -> Tuple[int, int]:
    """Parse a string like '1080x1920' into ``(width, height)``."""
    if not resolution or "x" not in resolution.lower():
        return (1080, 1920)
    raw = resolution.lower().replace(" ", "")
    parts = raw.split("x")
    try:
        return (int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return (1080, 1920)


def auto_video_bitrate(width: int, height: int) -> int:
    """Return a sensible target video bitrate (kbps) for a resolution."""
    pixels = max(1, width * height)
    if pixels <= 720 * 1280:
        return 4500
    if pixels <= 1080 * 1920:
        return 8000
    if pixels <= 1440 * 2560:
        return 14000
    return 20000


def filename_for_clip(
    *,
    project_id: int,
    clip_index: int,
    platform: str,
    resolution: str,
) -> str:
    safe_platform = platform.lower().replace(" ", "-")
    return f"clipflow_p{project_id:04d}_clip{clip_index:02d}_{safe_platform}_{resolution}.mp4"
