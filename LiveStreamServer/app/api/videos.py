"""Video management endpoints."""

from __future__ import annotations

import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import require_token
from app.config import get_settings
from app.database import get_db
from app.models import Video
from app.schemas import VideoOut, VideoRename
from app.services.ffmpeg_installer import detect_ffmpeg
from app.services.video_service import probe_duration
from app.utils.paths import resolve_in_dir, safe_filename


router = APIRouter(prefix="/videos", tags=["videos"], dependencies=[Depends(require_token)])


def _to_out(video: Video) -> VideoOut:
    return VideoOut.model_validate(video)


@router.get("", response_model=List[VideoOut])
def list_videos(db: Session = Depends(get_db)) -> List[VideoOut]:
    items = db.query(Video).order_by(Video.created_at.desc()).all()
    return [_to_out(v) for v in items]


@router.post("/upload", response_model=VideoOut)
def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)) -> VideoOut:
    settings = get_settings()
    os.makedirs(settings.videos_dir, exist_ok=True)

    original = file.filename or "video.mp4"
    try:
        clean = safe_filename(original)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Always store with a unique prefix to prevent collisions.
    unique_name = f"{uuid.uuid4().hex[:8]}_{clean}"
    target = resolve_in_dir(settings.videos_dir, unique_name)

    max_bytes = settings.max_upload_mb * 1024 * 1024
    written = 0
    try:
        with open(target, "wb") as out:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"file melebihi batas {settings.max_upload_mb} MB",
                    )
                out.write(chunk)
    except HTTPException:
        if os.path.exists(target):
            os.remove(target)
        raise
    except OSError as exc:
        if os.path.exists(target):
            os.remove(target)
        raise HTTPException(status_code=500, detail=f"gagal menyimpan file: {exc}") from exc
    finally:
        file.file.close()

    duration = None
    _, ffmpeg_path, _ = detect_ffmpeg(settings)
    if ffmpeg_path:
        duration = probe_duration(target, ffmpeg_path)

    video = Video(
        filename=unique_name,
        original_name=original,
        path=target,
        size=written,
        duration=duration,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return _to_out(video)


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(video_id: int, db: Session = Depends(get_db)) -> None:
    video = db.query(Video).get(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="video tidak ditemukan")
    try:
        if os.path.isfile(video.path):
            os.remove(video.path)
    except OSError:
        pass
    db.delete(video)
    db.commit()


@router.patch("/{video_id}/rename", response_model=VideoOut)
def rename_video(video_id: int, payload: VideoRename, db: Session = Depends(get_db)) -> VideoOut:
    video = db.query(Video).get(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="video tidak ditemukan")

    settings = get_settings()
    try:
        clean = safe_filename(payload.new_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    new_path = resolve_in_dir(settings.videos_dir, clean)
    if os.path.exists(new_path) and new_path != video.path:
        raise HTTPException(status_code=409, detail="nama file sudah dipakai")

    try:
        shutil.move(video.path, new_path)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"gagal rename: {exc}") from exc

    video.filename = clean
    video.path = new_path
    video.original_name = payload.new_name
    db.commit()
    db.refresh(video)
    return _to_out(video)
