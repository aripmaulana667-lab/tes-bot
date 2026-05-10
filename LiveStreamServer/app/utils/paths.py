"""Filesystem helpers with path-traversal protection."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Iterable


_INVALID_RE = re.compile(r"[^A-Za-z0-9._\- ]+")


def safe_filename(name: str, allowed_ext: Iterable[str] = ("mp4", "mkv", "mov", "avi")) -> str:
    """Sanitise a user supplied filename. Raises ValueError if not safe."""

    if not name or name in (".", ".."):
        raise ValueError("nama file tidak valid")

    # Strip directories: only the basename is allowed.
    name = os.path.basename(name.replace("\\", "/"))
    name = unicodedata.normalize("NFKD", name)

    if "\x00" in name:
        raise ValueError("nama file mengandung karakter ilegal")

    base, ext = os.path.splitext(name)
    ext = ext.lstrip(".").lower()
    if ext not in {e.lower() for e in allowed_ext}:
        raise ValueError(f"ekstensi .{ext} tidak diizinkan")

    base = _INVALID_RE.sub("_", base).strip().strip(".") or "video"
    return f"{base}.{ext}"


def resolve_in_dir(base_dir: str, name: str) -> str:
    """Join ``name`` to ``base_dir`` and ensure the result stays inside it."""

    base_abs = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base_abs, name))
    if os.path.commonpath([base_abs, target]) != base_abs:
        raise ValueError("path traversal terdeteksi")
    return target
