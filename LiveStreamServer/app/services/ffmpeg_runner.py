"""FFmpeg command builder for outgoing RTMP streams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FfmpegOptions:
    video_path: str
    rtmp_target: str
    bitrate: str = "2500k"
    resolution: Optional[str] = "1280x720"  # ``None`` = keep source size
    fps: Optional[int] = 30
    audio_bitrate: str = "128k"
    preset: str = "veryfast"
    loop: bool = True


def build_command(ffmpeg_exe: str, options: FfmpegOptions) -> List[str]:
    """Return the FFmpeg argv list for streaming to RTMP.

    Mirrors the spec from the user's brief:

        ffmpeg -re [-stream_loop -1] -i VIDEO -c:v libx264 -preset veryfast
               -b:v BITRATE -maxrate BITRATE -bufsize 2*BITRATE
               -c:a aac -b:a 128k -ar 44100 -f flv RTMP_URL/STREAM_KEY
    """

    cmd: List[str] = [ffmpeg_exe, "-hide_banner", "-loglevel", "info", "-re"]

    if options.loop:
        cmd += ["-stream_loop", "-1"]

    cmd += ["-i", options.video_path]

    cmd += [
        "-c:v",
        "libx264",
        "-preset",
        options.preset,
        "-b:v",
        options.bitrate,
        "-maxrate",
        options.bitrate,
        "-bufsize",
        _double_bitrate(options.bitrate),
    ]

    if options.resolution:
        cmd += ["-s", options.resolution]
    if options.fps:
        cmd += ["-r", str(options.fps)]

    cmd += [
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        options.audio_bitrate,
        "-ar",
        "44100",
        "-f",
        "flv",
        options.rtmp_target,
    ]
    return cmd


def _double_bitrate(value: str) -> str:
    """``2500k`` -> ``5000k``. Falls back to the original string on failure."""

    try:
        if value.endswith("k") or value.endswith("K"):
            return f"{int(value[:-1]) * 2}k"
        if value.endswith("m") or value.endswith("M"):
            return f"{int(value[:-1]) * 2}M"
        return f"{int(value) * 2}"
    except (TypeError, ValueError):
        return value


def join_rtmp(rtmp_url: str, stream_key: str) -> str:
    """Combine ``rtmp_url`` and ``stream_key``.

    Accepts both forms:
      - rtmp://host/app  + key  -> rtmp://host/app/key
      - rtmp://host/app/  + key -> rtmp://host/app/key
      - rtmp://host/app/key (already complete) + ""
    """

    rtmp_url = rtmp_url.rstrip("/")
    if not stream_key:
        return rtmp_url
    return f"{rtmp_url}/{stream_key}"
