"""Lyric text cleaning.

Strict rules from the product spec:
- Remove substrings enclosed in ``[...]`` and ``(...)``
- DO NOT touch timestamps (``[mm:ss.xx]``)
- DO NOT reorder lines
- DO NOT modify text outside those brackets
- DO NOT advance the timestamp; lyrics may never appear earlier than written
"""
from __future__ import annotations

import re
from typing import Iterable


_TIMESTAMP_RE = re.compile(r"^(\[\d{1,2}:\d{1,2}(?:[.:]\d{1,3})?\])")
_BRACKETED_RE = re.compile(r"\[[^\[\]]*\]")
_PARENS_RE = re.compile(r"\([^()]*\)")


def _strip_brackets_preserving_timestamps(text: str) -> str:
    """Remove ``[...]`` and ``(...)`` but keep leading LRC timestamps intact."""
    timestamps: list[str] = []
    rest = text
    while True:
        m = _TIMESTAMP_RE.match(rest)
        if not m:
            break
        timestamps.append(m.group(1))
        rest = rest[m.end():]

    # Repeatedly strip brackets until stable (handles nested patterns safely).
    prev = None
    while prev != rest:
        prev = rest
        rest = _BRACKETED_RE.sub("", rest)
        rest = _PARENS_RE.sub("", rest)

    # Tidy whitespace introduced by stripped brackets.
    rest = re.sub(r"[ \t]{2,}", " ", rest).strip()

    return "".join(timestamps) + rest


def clean_line(line: str) -> str:
    """Clean a single line of lyrics."""
    return _strip_brackets_preserving_timestamps(line)


def clean_text(text: str) -> str:
    """Clean a multi-line lyric blob, preserving line order."""
    lines = text.splitlines()
    cleaned: list[str] = []
    for line in lines:
        cleaned_line = clean_line(line)
        # Drop empty lines that arose purely from bracket stripping, but keep
        # genuinely blank separators in unsynced lyrics.
        if line.strip() and not cleaned_line.strip():
            continue
        cleaned.append(cleaned_line)
    # Trim trailing blank padding only.
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return "\n".join(cleaned)


def clean_lines(lines: Iterable[str]) -> list[str]:
    return [clean_line(l) for l in lines]


__all__ = ["clean_line", "clean_text", "clean_lines"]
