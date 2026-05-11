"""Parse .lrc files and generate ASS subtitles with timestamps + fade."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from ..models.render import LyricsConfig


_TIME_RE = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]")


@dataclass
class LyricLine:
    start: float
    text: str


def parse_lrc(text: str, offset_ms: int = 0) -> List[LyricLine]:
    """Parse LRC content into time-ordered lyric lines (seconds)."""
    lines: List[LyricLine] = []
    for raw in text.splitlines():
        timestamps: List[float] = []
        for match in _TIME_RE.finditer(raw):
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            millis_raw = match.group(3) or "0"
            millis = int(millis_raw.ljust(3, "0")[:3])
            t = minutes * 60 + seconds + millis / 1000.0
            timestamps.append(t)
        content = _TIME_RE.sub("", raw).strip()
        if not content:
            continue
        for ts in timestamps:
            lines.append(LyricLine(start=ts + offset_ms / 1000.0, text=content))
    lines.sort(key=lambda x: x.start)
    return lines


def _hex_to_ass(color: str, opacity: float = 1.0) -> str:
    """Convert #RRGGBB to ASS &HAABBGGRR& format."""
    color = color.strip().lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    if len(color) != 6:
        color = "FFFFFF"
    r = color[0:2]
    g = color[2:4]
    b = color[4:6]
    alpha = max(0, min(255, int(round((1.0 - opacity) * 255))))
    return f"&H{alpha:02X}{b}{g}{r}&"


def _format_ass_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - (h * 3600 + m * 60)
    return f"{h}:{m:02d}:{s:05.2f}"


def lyrics_to_ass(
    lyrics: List[LyricLine],
    cfg: LyricsConfig,
    resolution: Tuple[int, int],
    audio_duration: float,
) -> str:
    """Generate an ASS subtitle script from parsed LRC lines."""
    width, height = resolution
    primary = _hex_to_ass(cfg.color, cfg.opacity)
    outline = _hex_to_ass(cfg.outline_color, cfg.opacity)
    shadow = _hex_to_ass(cfg.shadow_color, cfg.opacity)
    font = cfg.font or "Arial"

    style_line = (
        "Style: Default,"
        f"{font},{cfg.font_size},"
        f"{primary},{primary},{outline},{shadow},"
        "0,0,0,0,100,100,0,0,"
        f"1,{cfg.outline_size},{cfg.shadow_size},"
        f"2,40,40,{cfg.bottom_margin},1"
    )

    events: List[str] = []
    fade_ms = max(0, cfg.fade_ms)
    fade_tag = f"{{\\fad({fade_ms},{fade_ms})}}" if fade_ms else ""
    for idx, line in enumerate(lyrics):
        start = max(0.0, line.start)
        if idx + 1 < len(lyrics):
            end = max(start + 0.4, lyrics[idx + 1].start - 0.05)
        else:
            end = max(start + 2.0, audio_duration or (start + 3.0))
        text = (
            line.text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")
        )
        events.append(
            "Dialogue: 0,"
            f"{_format_ass_time(start)},{_format_ass_time(end)},Default,,0,0,0,,"
            f"{fade_tag}{text}"
        )

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\n"
        "ScaledBorderAndShadow: yes\n"
        "WrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"{style_line}\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    return header + "\n".join(events) + "\n"


def load_lrc_file(path: Path, offset_ms: int = 0) -> List[LyricLine]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return parse_lrc(text, offset_ms=offset_ms)


def ass_escape_path(path: str) -> str:
    """Escape path for use inside an ffmpeg subtitles=filter argument."""
    p = path.replace("\\", "/").replace(":", "\\:")
    return p.replace("'", "\\'")
