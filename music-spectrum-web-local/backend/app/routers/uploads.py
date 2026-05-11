"""Upload and listing of local assets (music, lyrics, backgrounds, logos)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..config import (
    ALLOWED_BG_EXT,
    ALLOWED_LOGO_EXT,
    ALLOWED_LYRIC_EXT,
    ALLOWED_MUSIC_EXT,
    BACKGROUNDS_DIR,
    LOGOS_DIR,
    LYRICS_DIR,
    MUSIC_DIR,
)

router = APIRouter(prefix="/assets", tags=["assets"])


_CATEGORIES = {
    "music": (MUSIC_DIR, ALLOWED_MUSIC_EXT),
    "lyrics": (LYRICS_DIR, ALLOWED_LYRIC_EXT),
    "backgrounds": (BACKGROUNDS_DIR, ALLOWED_BG_EXT),
    "logos": (LOGOS_DIR, ALLOWED_LOGO_EXT),
}


def _safe_name(name: str) -> str:
    name = Path(name).name
    return re.sub(r"[^A-Za-z0-9._\- ]+", "_", name).strip() or "file"


@router.get("/{category}")
async def list_assets(category: str) -> List[dict]:
    if category not in _CATEGORIES:
        raise HTTPException(status_code=404, detail="Kategori tidak dikenal.")
    folder, ext = _CATEGORIES[category]
    items = []
    for p in sorted(folder.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in ext:
            continue
        items.append({"name": p.name, "size": p.stat().st_size})
    return items


@router.post("/{category}")
async def upload_asset(category: str, file: UploadFile = File(...)) -> dict:
    if category not in _CATEGORIES:
        raise HTTPException(status_code=404, detail="Kategori tidak dikenal.")
    folder, ext = _CATEGORIES[category]
    filename = _safe_name(file.filename or "file")
    if Path(filename).suffix.lower() not in ext:
        raise HTTPException(status_code=400, detail=f"Ekstensi tidak diperbolehkan untuk {category}.")
    target = folder / filename
    counter = 1
    while target.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        target = folder / f"{stem}-{counter}{suffix}"
        counter += 1
    with open(target, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    return {"name": target.name, "size": target.stat().st_size}


@router.delete("/{category}/{name}")
async def delete_asset(category: str, name: str) -> dict:
    if category not in _CATEGORIES:
        raise HTTPException(status_code=404, detail="Kategori tidak dikenal.")
    folder, _ = _CATEGORIES[category]
    target = folder / _safe_name(name)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan.")
    target.unlink()
    return {"ok": True}
