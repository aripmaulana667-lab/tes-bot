"""Helpers for video file metadata."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Optional


def probe_duration(video_path: str, ffmpeg_path: Optional[str] = None) -> Optional[float]:
    """Return the duration in seconds, or ``None`` if it cannot be determined."""

    candidates = []
    if ffmpeg_path:
        ffprobe = os.path.join(os.path.dirname(ffmpeg_path), "ffprobe.exe" if os.name == "nt" else "ffprobe")
        if os.path.isfile(ffprobe):
            candidates.append(ffprobe)
    on_path = shutil.which("ffprobe")
    if on_path:
        candidates.append(on_path)

    for cand in candidates:
        try:
            result = subprocess.run(
                [
                    cand,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    video_path,
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                duration = data.get("format", {}).get("duration")
                if duration is not None:
                    return float(duration)
        except (OSError, ValueError, subprocess.SubprocessError):
            continue
    return None
