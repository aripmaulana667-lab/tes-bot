"""Subtitle generation for the "clipper" look.

The renderer builds an Advanced SubStation Alpha (ASS) file because ASS is the
only widely-supported subtitle format that lets us:

- Use thick outlines + drop shadow.
- Highlight individual words inline (\\c color tag).
- Animate appearance with a simple ``\\fad`` effect.

The rest of the pipeline (FFmpeg burn-in) only needs to read the resulting
``.ass`` file.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence

from ..utils import config as cfg
from ..utils.logger import get_logger
from .clip_generator import Clip
from .transcriber import WordToken

_LOG = get_logger("subtitle")


# ---------------------------------------------------------------------------
# Style configuration
# ---------------------------------------------------------------------------
@dataclass
class SubtitleStyle:
    font_name: str = "Arial"
    font_size: int = 64
    primary_color: str = "white"
    outline_color: str = "black"
    highlight_color: str = "yellow"
    outline_width: int = 4
    shadow: int = 1
    bold: bool = True
    italic: bool = False
    position: str = "bottom-center"  # 'bottom-center', 'center', 'top-center'
    max_chars_per_line: int = 26
    max_lines: int = 2
    animate: bool = True
    fade_in_ms: int = 120
    fade_out_ms: int = 120
    margin_v: int = 90  # vertical margin in pixels


# Important keywords that should be highlighted inside subtitles.
_KEYWORD_HIGHLIGHTS = {
    "important", "secret", "rahasia", "amazing", "incredible", "shocking",
    "luar biasa", "ternyata", "hasilnya", "the truth", "kunci", "kuncinya",
    "kesimpulan", "akhirnya", "perhatian", "penting", "wow", "gila",
}


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
_COLOR_NAMES = {
    "white": "FFFFFF",
    "black": "000000",
    "yellow": "FFFF00",
    "red": "FF3333",
    "green": "33FF66",
    "blue": "3399FF",
    "orange": "FF9900",
    "pink": "FF66CC",
}


def _color_to_ass(color: str) -> str:
    """Convert a CSS color name or hex string to an ASS BGR color."""
    color = (color or "white").strip()
    if color.startswith("#"):
        color = color[1:]
    color = _COLOR_NAMES.get(color.lower(), color)
    if len(color) == 6 and re.match(r"^[0-9A-Fa-f]{6}$", color):
        rr, gg, bb = color[0:2], color[2:4], color[4:6]
        return f"&H00{bb}{gg}{rr}".upper()
    return "&H00FFFFFF"


def _alignment(position: str) -> int:
    """Return the ASS alignment integer for a position label."""
    mapping = {
        "bottom-center": 2,
        "center": 5,
        "top-center": 8,
        "bottom-left": 1,
        "bottom-right": 3,
    }
    return mapping.get(position, 2)


def _format_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds - hours * 3600 - minutes * 60
    return f"{hours:01d}:{minutes:02d}:{secs:05.2f}"


# ---------------------------------------------------------------------------
# Line wrapping
# ---------------------------------------------------------------------------
def _wrap_words(words: Sequence[WordToken], max_chars: int, max_lines: int) -> List[List[WordToken]]:
    lines: List[List[WordToken]] = []
    current: List[WordToken] = []
    current_len = 0
    for word in words:
        token = word.text.strip()
        added_len = len(token) + (1 if current else 0)
        if current and current_len + added_len > max_chars:
            lines.append(current)
            if len(lines) >= max_lines:
                # carry the rest into a fresh group, will become a new caption
                current = [word]
                current_len = len(token)
                continue
            current = [word]
            current_len = len(token)
        else:
            current.append(word)
            current_len += added_len
    if current:
        lines.append(current)
    return lines


@dataclass
class SubtitleEvent:
    start: float
    end: float
    lines: List[List[WordToken]] = field(default_factory=list)


def _group_into_events(
    words: Sequence[WordToken],
    style: SubtitleStyle,
) -> List[SubtitleEvent]:
    """Group words into multi-line events that fit the style's wrapping rules."""
    if not words:
        return []
    lines = _wrap_words(words, style.max_chars_per_line, style.max_lines)
    events: List[SubtitleEvent] = []
    buffered: List[List[WordToken]] = []
    for line in lines:
        buffered.append(line)
        if len(buffered) >= style.max_lines:
            events.append(_event_from_lines(buffered))
            buffered = []
    if buffered:
        events.append(_event_from_lines(buffered))
    return events


def _event_from_lines(lines: Sequence[Sequence[WordToken]]) -> SubtitleEvent:
    flat = [w for line in lines for w in line]
    start = flat[0].start
    end = flat[-1].end
    return SubtitleEvent(start=start, end=end, lines=[list(line) for line in lines])


# ---------------------------------------------------------------------------
# ASS rendering
# ---------------------------------------------------------------------------
def _is_keyword(word: str) -> bool:
    bare = word.strip(",.!?:;\"'()[]").lower()
    if bare in _KEYWORD_HIGHLIGHTS:
        return True
    if len(bare) >= 6 and bare.isupper():
        return True
    return False


def _render_event_text(event: SubtitleEvent, style: SubtitleStyle) -> str:
    parts: List[str] = []
    if style.animate:
        parts.append(f"{{\\fad({style.fade_in_ms},{style.fade_out_ms})}}")
    highlight_color = _color_to_ass(style.highlight_color)
    primary_color = _color_to_ass(style.primary_color)
    for line_idx, line in enumerate(event.lines):
        line_tokens: List[str] = []
        for word in line:
            text = word.text.strip()
            if not text:
                continue
            if _is_keyword(text):
                line_tokens.append(f"{{\\c{highlight_color}\\b1}}{text}{{\\c{primary_color}\\b1}}")
            else:
                line_tokens.append(text)
        parts.append(" ".join(line_tokens))
        if line_idx != len(event.lines) - 1:
            parts.append("\\N")
    return "".join(parts)


def _ass_header(style: SubtitleStyle, *, video_width: int, video_height: int) -> str:
    primary = _color_to_ass(style.primary_color)
    outline = _color_to_ass(style.outline_color)
    bold = -1 if style.bold else 0
    italic = -1 if style.italic else 0
    align = _alignment(style.position)
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {video_width}\n"
        f"PlayResY: {video_height}\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{style.font_name},{style.font_size},{primary},{primary},{outline},&H80000000,"
        f"{bold},{italic},0,0,100,100,0,0,1,{style.outline_width},{style.shadow},{align},40,40,"
        f"{style.margin_v},1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def render_clip_subtitles(
    clip: Clip,
    *,
    style: Optional[SubtitleStyle] = None,
    video_width: int = 1080,
    video_height: int = 1920,
    output_path: Optional[str] = None,
) -> Optional[str]:
    """Render an ASS subtitle file for a single clip.

    Returns the file path or ``None`` if the clip has no word-level timing.
    """
    style = style or _style_from_config()
    words: List[WordToken] = []
    for seg in clip.segments:
        for word in seg.words:
            if word.end < clip.start or word.start > clip.end:
                continue
            shifted = WordToken(
                text=word.text,
                start=max(0.0, word.start - clip.start),
                end=max(0.0, word.end - clip.start),
                probability=word.probability,
            )
            words.append(shifted)
    if not words:
        _LOG.info("Clip %d has no word timing; subtitles will fall back to segments", clip.index)
        words = _approximate_words_from_segments(clip)
    if not words:
        return None

    events = _group_into_events(words, style)
    if not events:
        return None

    if output_path is None:
        output_path = os.path.join(
            cfg.get_temp_dir(), f"subtitle_clip{clip.index:02d}.ass"
        )

    header = _ass_header(style, video_width=video_width, video_height=video_height)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(header)
        for event in events:
            text = _render_event_text(event, style).replace("\n", " ")
            fh.write(
                f"Dialogue: 0,{_format_time(event.start)},{_format_time(event.end)},"
                f"Default,,0,0,0,,{text}\n"
            )
    return output_path


def _approximate_words_from_segments(clip: Clip) -> List[WordToken]:
    out: List[WordToken] = []
    for seg in clip.segments:
        if seg.end <= clip.start or seg.start >= clip.end:
            continue
        tokens = seg.text.split()
        if not tokens:
            continue
        rel_start = max(0.0, seg.start - clip.start)
        rel_end = max(rel_start, seg.end - clip.start)
        if rel_end <= rel_start:
            continue
        per_token = (rel_end - rel_start) / max(1, len(tokens))
        for i, tok in enumerate(tokens):
            out.append(
                WordToken(
                    text=tok,
                    start=rel_start + per_token * i,
                    end=rel_start + per_token * (i + 1),
                    probability=1.0,
                )
            )
    return out


def _style_from_config() -> SubtitleStyle:
    return SubtitleStyle(
        font_name=cfg.get("subtitle_font", "Arial"),
        font_size=int(cfg.get("subtitle_font_size", 64)),
        primary_color=cfg.get("subtitle_color", "white"),
        outline_color=cfg.get("subtitle_outline_color", "black"),
        outline_width=int(cfg.get("subtitle_outline_width", 4)),
        position=cfg.get("subtitle_position", "bottom-center"),
        highlight_color=cfg.get("subtitle_highlight_color", "yellow"),
        animate=bool(cfg.get("subtitle_animate", True)),
    )


def style_from_dict(data: dict) -> SubtitleStyle:
    base = _style_from_config()
    for key, value in data.items():
        if hasattr(base, key):
            setattr(base, key, value)
    return base
