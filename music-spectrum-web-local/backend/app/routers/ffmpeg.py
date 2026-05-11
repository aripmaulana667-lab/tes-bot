"""FFmpeg status and portable installation endpoints."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from ..services import ffmpeg as ffsvc
from ..services.jobs import store

router = APIRouter(prefix="/ffmpeg", tags=["ffmpeg"])

_install_lock = asyncio.Lock()


@router.get("/status")
async def status() -> dict:
    return ffsvc.ffmpeg_status()


@router.post("/install")
async def install() -> dict:
    if _install_lock.locked():
        raise HTTPException(status_code=409, detail="Instalasi FFmpeg sedang berjalan.")

    async with _install_lock:
        job = store.create("preview")  # repurpose kind for progress channel
        await store.update(job, status="rendering", message="Memulai instalasi FFmpeg portable ...")

        async def progress(pct: float, msg: str) -> None:
            await store.update(job, progress=pct, message=msg)

        try:
            result = await ffsvc.install_portable(progress=progress)
            await store.update(job, status="done", progress=1.0, message="FFmpeg siap.")
            return {"job_id": job.id, "status": result}
        except Exception as exc:
            await store.update(job, status="failed", error=str(exc), message="Instalasi gagal.")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
