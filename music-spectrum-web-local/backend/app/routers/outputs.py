"""Output file management endpoints."""
from __future__ import annotations

import platform
import subprocess
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import IS_WINDOWS, OUTPUTS_DIR

router = APIRouter(prefix="/outputs", tags=["outputs"])


@router.get("")
async def list_outputs() -> List[dict]:
    items = []
    for p in sorted(OUTPUTS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_file():
            continue
        stat = p.stat()
        items.append(
            {
                "name": p.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            }
        )
    return items


@router.delete("/{filename}")
async def delete_output(filename: str) -> dict:
    target = OUTPUTS_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File tidak ditemukan.")
    target.unlink()
    return {"ok": True}


@router.get("/{filename}/download")
async def download_output(filename: str):
    target = OUTPUTS_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File tidak ditemukan.")
    return FileResponse(str(target), filename=target.name, media_type="video/mp4")


@router.post("/open-folder")
async def open_outputs_folder() -> dict:
    try:
        if IS_WINDOWS:
            subprocess.Popen(["explorer", str(OUTPUTS_DIR)])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(OUTPUTS_DIR)])
        else:
            subprocess.Popen(["xdg-open", str(OUTPUTS_DIR)])
        return {"ok": True, "path": str(OUTPUTS_DIR)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
