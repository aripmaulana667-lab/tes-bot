"""Application configuration and storage paths."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

STORAGE_DIR = PROJECT_ROOT / "storage"
MUSIC_DIR = STORAGE_DIR / "music"
LYRICS_DIR = STORAGE_DIR / "lyrics"
BACKGROUNDS_DIR = STORAGE_DIR / "backgrounds"
LOGOS_DIR = STORAGE_DIR / "logos"
OUTPUTS_DIR = STORAGE_DIR / "outputs"
TEMP_DIR = STORAGE_DIR / "temp"

TOOLS_DIR = PROJECT_ROOT / "tools"
FFMPEG_DIR = TOOLS_DIR / "ffmpeg"

for d in (
    STORAGE_DIR,
    MUSIC_DIR,
    LYRICS_DIR,
    BACKGROUNDS_DIR,
    LOGOS_DIR,
    OUTPUTS_DIR,
    TEMP_DIR,
    FFMPEG_DIR,
):
    d.mkdir(parents=True, exist_ok=True)


HOST: str = os.environ.get("HOST", "127.0.0.1")
PORT: int = int(os.environ.get("PORT", "8000"))

_default_origins = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS: List[str] = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",")
    if o.strip()
]

FFMPEG_PATH: str = os.environ.get("FFMPEG_PATH", "").strip()
FFPROBE_PATH: str = os.environ.get("FFPROBE_PATH", "").strip()


IS_WINDOWS: bool = sys.platform.startswith("win")

ALLOWED_MUSIC_EXT = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"}
ALLOWED_LYRIC_EXT = {".lrc", ".txt"}
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
ALLOWED_BG_EXT = ALLOWED_IMAGE_EXT | ALLOWED_VIDEO_EXT
ALLOWED_LOGO_EXT = ALLOWED_IMAGE_EXT
