"""Read audio metadata and decode PCM samples via FFmpeg.

We intentionally avoid heavy decoders (librosa, soundfile) and rely on ffmpeg
piping raw float32 PCM. This keeps cold-start fast on low-end PCs.
"""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

import numpy as np

from .ffmpeg_manager import _no_window_kwargs, probe_ffmpeg


SUPPORTED_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".aac"}


@dataclass
class AudioInfo:
    path: str
    duration: float = 0.0
    sample_rate: int = 44100
    channels: int = 2
    bitrate: int = 0
    title: str = ""
    artist: str = ""
    album: str = ""

    @property
    def filename(self) -> str:
        return Path(self.path).name


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTS


def list_supported_in_folder(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    if not folder.exists():
        return []
    out: list[Path] = []
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            out.append(p)
    return out


def probe(path: str | Path, ffprobe_path: str = "") -> AudioInfo:
    """Best-effort metadata probe.

    Uses ffprobe (preferred) and falls back to mutagen.
    """
    path = str(path)
    info = AudioInfo(path=path)

    if not ffprobe_path:
        status = probe_ffmpeg()
        ffprobe_path = status.ffprobe_path

    if ffprobe_path:
        try:
            cmd = [
                ffprobe_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                path,
            ]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                **_no_window_kwargs(),
            )
            data = json.loads(res.stdout or "{}")
            fmt = data.get("format", {})
            if "duration" in fmt:
                info.duration = float(fmt["duration"])
            if "bit_rate" in fmt:
                info.bitrate = int(fmt["bit_rate"])
            tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
            info.title = tags.get("title", info.title)
            info.artist = tags.get("artist", info.artist)
            info.album = tags.get("album", info.album)
            for s in data.get("streams", []):
                if s.get("codec_type") == "audio":
                    info.sample_rate = int(s.get("sample_rate") or info.sample_rate)
                    info.channels = int(s.get("channels") or info.channels)
                    break
        except Exception:
            pass

    # Mutagen fallback for missing duration/title.
    if info.duration <= 0 or not info.title:
        try:
            from mutagen import File as MutagenFile  # type: ignore

            mf = MutagenFile(path)
            if mf is not None:
                if mf.info and getattr(mf.info, "length", 0):
                    info.duration = info.duration or float(mf.info.length)
                tags = getattr(mf, "tags", None) or {}
                def first(key: str) -> str:
                    val = tags.get(key)
                    if val is None:
                        return ""
                    if isinstance(val, list) and val:
                        val = val[0]
                    return str(val)

                info.title = info.title or first("TIT2") or first("title") or first("\xa9nam")
                info.artist = (
                    info.artist or first("TPE1") or first("artist") or first("\xa9ART")
                )
                info.album = info.album or first("TALB") or first("album") or first("\xa9alb")
        except Exception:
            pass

    if not info.title:
        info.title = Path(path).stem
    return info


def decode_pcm(
    path: str | Path,
    sample_rate: int = 44100,
    channels: int = 1,
    ffmpeg_path: str = "",
) -> np.ndarray:
    """Return decoded PCM as float32 array in [-1, 1].

    For visualizer use we usually want mono (channels=1) to feed FFT directly.
    """
    if not ffmpeg_path:
        status = probe_ffmpeg()
        ffmpeg_path = status.ffmpeg_path
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg is required to decode audio.")

    cmd = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-",
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        check=False,
        **_no_window_kwargs(),
    )
    if proc.returncode != 0:
        msg = proc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg decode failed: {msg.strip()}")
    arr = np.frombuffer(proc.stdout, dtype=np.float32)
    if channels > 1:
        arr = arr.reshape(-1, channels)
    return arr


__all__ = [
    "AudioInfo",
    "SUPPORTED_EXTS",
    "is_supported",
    "list_supported_in_folder",
    "probe",
    "decode_pcm",
]
