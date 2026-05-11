"""Render endpoints: preview, full, batch, status, log, download, cancel."""
from __future__ import annotations

import asyncio
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import OUTPUTS_DIR
from ..models.render import (
    BatchRenderRequest,
    JobInfo,
    RenderRequest,
)
from ..services.batch import run_batch
from ..services.jobs import store
from ..services.render import render_job

router = APIRouter(prefix="/render", tags=["render"])


async def _run_single(job, request: RenderRequest, preview: bool) -> None:
    try:
        await render_job(job, request, preview=preview)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        await store.update(job, status="failed", error=str(exc), message="Gagal.")


@router.post("/preview")
async def render_preview(request: RenderRequest) -> JobInfo:
    job = store.create("preview")
    asyncio.create_task(_run_single(job, request, True))
    return job.to_info()


@router.post("/full")
async def render_full(request: RenderRequest) -> JobInfo:
    job = store.create("full")
    asyncio.create_task(_run_single(job, request, False))
    return job.to_info()


@router.post("/batch")
async def render_batch(request: BatchRenderRequest) -> JobInfo:
    job = store.create("batch")

    async def runner():
        try:
            await run_batch(job, request)
        except Exception as exc:
            await store.update(job, status="failed", error=str(exc))

    asyncio.create_task(runner())
    return job.to_info()


@router.get("/jobs")
async def list_jobs() -> List[JobInfo]:
    return [j.to_info() for j in store.list()]


@router.get("/{job_id}/status")
async def job_status(job_id: str) -> JobInfo:
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    return job.to_info()


@router.get("/{job_id}/log")
async def job_log(job_id: str) -> dict:
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    return {"id": job.id, "log": job.log_lines}


@router.get("/{job_id}/download")
async def job_download(job_id: str):
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    if not job.output_file:
        raise HTTPException(status_code=404, detail="Output belum tersedia.")
    path = OUTPUTS_DIR / job.output_file
    if not path.exists():
        raise HTTPException(status_code=404, detail="File output tidak ditemukan.")
    return FileResponse(str(path), filename=path.name, media_type="video/mp4")


@router.post("/{job_id}/cancel")
async def job_cancel(job_id: str) -> JobInfo:
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    store.request_cancel(job)
    await store.update(job, message="Membatalkan ...")
    return job.to_info()
