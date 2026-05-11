"""Extract lyrics (synced or unsynced) from audio metadata or sidecar files.

We never advance timestamps. If only unsynced lyrics are available, the caller
gets ``LyricsData(synced=False, lines=[LyricLine(time=None, text=...)])`` and
can choose between static display, importing an ``.lrc`` file, or disabling
lyrics — that decision lives in the GUI, not here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from .lyrics_cleaner import clean_line


_LRC_LINE_RE = re.compile(r"\[(\d{1,2}):(\d{1,2})(?:[.:](\d{1,3}))?\]")
_WORD_TIME_RE = re.compile(r"<(\d{1,2}):(\d{1,2})(?:[.:](\d{1,3}))?>")


@dataclass
class WordTiming:
    time: float
    text: str


@dataclass
class LyricLine:
    time: Optional[float]  # seconds; None means unsynced
    text: str
    words: list[WordTiming] = field(default_factory=list)


@dataclass
class LyricsData:
    synced: bool
    lines: list[LyricLine]
    source: str = ""  # "metadata", "lrc-file", "manual", ""

    @property
    def empty(self) -> bool:
        return not self.lines


def _parse_time(mm: str, ss: str, frac: Optional[str]) -> float:
    minutes = int(mm)
    seconds = int(ss)
    fraction = 0.0
    if frac:
        # The fractional part of an LRC timestamp can be tenths, hundredths or
        # milliseconds. Normalize on its digit-count.
        digits = len(frac)
        fraction = int(frac) / (10 ** digits)
    return minutes * 60 + seconds + fraction


def parse_lrc(text: str) -> LyricsData:
    """Parse LRC formatted text. Supports enhanced LRC with ``<mm:ss.xx>`` word timings."""
    raw_lines = text.replace("\r\n", "\n").split("\n")
    parsed: list[LyricLine] = []
    any_synced = False

    for raw in raw_lines:
        if not raw.strip():
            continue
        timestamps: list[float] = []
        idx = 0
        while True:
            m = _LRC_LINE_RE.match(raw, idx)
            if not m:
                break
            timestamps.append(_parse_time(m.group(1), m.group(2), m.group(3)))
            idx = m.end()
        body = raw[idx:]

        # Word-level timings within body.
        words: list[WordTiming] = []
        if "<" in body and timestamps:
            base_time = timestamps[0]
            cleaned_body_parts: list[str] = []
            cursor = 0
            current_time = base_time
            buf: list[str] = []
            while cursor < len(body):
                m = _WORD_TIME_RE.match(body, cursor)
                if m:
                    if buf:
                        words.append(WordTiming(current_time, "".join(buf)))
                        cleaned_body_parts.append("".join(buf))
                        buf = []
                    current_time = _parse_time(m.group(1), m.group(2), m.group(3))
                    cursor = m.end()
                else:
                    buf.append(body[cursor])
                    cursor += 1
            if buf:
                words.append(WordTiming(current_time, "".join(buf)))
                cleaned_body_parts.append("".join(buf))
            body = "".join(cleaned_body_parts)

        cleaned = clean_line(body).strip()
        if not cleaned and not timestamps:
            continue

        if timestamps:
            any_synced = True
            for t in timestamps:
                parsed.append(LyricLine(time=t, text=cleaned, words=words.copy()))
        else:
            parsed.append(LyricLine(time=None, text=cleaned))

    if any_synced:
        parsed.sort(key=lambda l: (l.time if l.time is not None else 0.0))

    return LyricsData(synced=any_synced, lines=parsed)


def _from_mutagen_tags(tags) -> Optional[str]:
    """Inspect a Mutagen tags object for synced or unsynced lyrics text."""
    if tags is None:
        return None
    # ID3 USLT / SYLT.
    try:
        from mutagen.id3 import USLT, SYLT  # type: ignore
        for key in tags.keys():
            if key.startswith("USLT"):
                frame = tags[key]
                return getattr(frame, "text", "") or ""
            if key.startswith("SYLT"):
                frame = tags[key]
                # SYLT stores [(text, time_ms), ...]
                parts: list[str] = []
                for text, time_ms in getattr(frame, "text", []):
                    mm = int(time_ms // 60000)
                    ss = (time_ms % 60000) / 1000.0
                    parts.append(f"[{mm:02d}:{ss:05.2f}]{text}")
                return "\n".join(parts)
    except Exception:
        pass

    # Vorbis / FLAC.
    for key in ("LYRICS", "lyrics", "UNSYNCED LYRICS", "UNSYNCEDLYRICS"):
        if key in tags:
            val = tags[key]
            if isinstance(val, list) and val:
                return str(val[0])
            return str(val)

    # MP4 / M4A.
    for key in ("©lyr", "\xa9lyr", "lyr"):
        if key in tags:
            val = tags[key]
            if isinstance(val, list) and val:
                return str(val[0])
            return str(val)

    return None


def from_audio_metadata(path: str | Path) -> LyricsData:
    """Try to pull lyrics from the file's tags via Mutagen."""
    try:
        from mutagen import File as MutagenFile  # type: ignore
    except Exception:
        return LyricsData(synced=False, lines=[])

    try:
        mf = MutagenFile(str(path))
    except Exception:
        return LyricsData(synced=False, lines=[])

    if mf is None:
        return LyricsData(synced=False, lines=[])

    raw = _from_mutagen_tags(mf.tags)
    if not raw:
        return LyricsData(synced=False, lines=[])

    # If the lyrics text contains LRC timestamps, parse as LRC.
    if "[" in raw and _LRC_LINE_RE.search(raw):
        data = parse_lrc(raw)
        data.source = "metadata"
        return data

    # Pure unsynced text.
    lines: list[LyricLine] = []
    for raw_line in raw.replace("\r\n", "\n").split("\n"):
        cleaned = clean_line(raw_line).strip()
        if cleaned:
            lines.append(LyricLine(time=None, text=cleaned))
    return LyricsData(synced=False, lines=lines, source="metadata")


def from_lrc_file(path: str | Path) -> LyricsData:
    data = parse_lrc(Path(path).read_text(encoding="utf-8", errors="replace"))
    data.source = "lrc-file"
    return data


def from_sidecar(audio_path: str | Path) -> Optional[LyricsData]:
    """Look for ``<song>.lrc`` next to the audio file."""
    audio_path = Path(audio_path)
    candidates = [
        audio_path.with_suffix(".lrc"),
        audio_path.with_suffix(".LRC"),
    ]
    for c in candidates:
        if c.exists():
            return from_lrc_file(c)
    return None


def extract(audio_path: str | Path) -> LyricsData:
    """High level: try metadata, then sidecar LRC."""
    data = from_audio_metadata(audio_path)
    if not data.empty:
        return data
    sidecar = from_sidecar(audio_path)
    if sidecar is not None and not sidecar.empty:
        return sidecar
    return LyricsData(synced=False, lines=[], source="")


def line_active(line: LyricLine, t: float, lookahead: float = 0.0) -> bool:
    """Return True if ``line`` should be visible at audio time ``t``.

    A line is never active before its timestamp, ensuring lyrics never appear
    "earlier than the timestamp" as the spec mandates.
    """
    if line.time is None:
        return True  # unsynced — caller decides display strategy
    return t + lookahead >= line.time


def active_line_at(data: LyricsData, t: float) -> Optional[LyricLine]:
    """Return the latest line whose timestamp is <= t (synced lyrics only)."""
    if not data.synced or not data.lines:
        return None
    last: Optional[LyricLine] = None
    for line in data.lines:
        if line.time is None:
            continue
        if line.time <= t:
            last = line
        else:
            break
    return last


def progress_through_words(line: LyricLine, t: float, line_end: float) -> float:
    """Return karaoke progress 0..1 across ``line``.

    Falls back to a linear ramp if no word timings are present.
    """
    if line.time is None:
        return 0.0
    if t < line.time:
        return 0.0
    if line.words:
        # Position based on word timings.
        last_word_end = max(w.time for w in line.words)
        return max(0.0, min(1.0, (t - line.time) / max(0.01, last_word_end - line.time)))
    total = max(0.05, line_end - line.time)
    return max(0.0, min(1.0, (t - line.time) / total))


__all__ = [
    "LyricLine",
    "LyricsData",
    "WordTiming",
    "parse_lrc",
    "from_audio_metadata",
    "from_lrc_file",
    "from_sidecar",
    "extract",
    "line_active",
    "active_line_at",
    "progress_through_words",
]
