"""Stream lifecycle endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_token
from app.database import get_db
from app.models import Stream
from app.schemas import StreamLogResponse, StreamOut, StreamStartRequest
from app.services.stream_manager import get_stream_manager


router = APIRouter(prefix="/streams", tags=["streams"], dependencies=[Depends(require_token)])


def _to_out(stream: Stream) -> StreamOut:
    return StreamOut(
        id=stream.id,
        account_id=stream.account_id,
        account_name=stream.account.name if stream.account else "",
        platform=stream.account.platform if stream.account else "",
        video_id=stream.video_id,
        video_name=stream.video.original_name if stream.video else "",
        status=stream.status,
        pid=stream.pid,
        bitrate=stream.bitrate,
        resolution=stream.resolution,
        fps=stream.fps,
        loop=stream.loop,
        auto_restart=stream.auto_restart,
        started_at=stream.started_at,
        stopped_at=stream.stopped_at,
        last_error=stream.last_error,
    )


@router.get("", response_model=List[StreamOut])
def list_streams(db: Session = Depends(get_db)) -> List[StreamOut]:
    items = db.query(Stream).order_by(Stream.id.desc()).all()
    return [_to_out(s) for s in items]


@router.get("/{stream_id}", response_model=StreamOut)
def get_stream(stream_id: int, db: Session = Depends(get_db)) -> StreamOut:
    stream = db.query(Stream).get(stream_id)
    if stream is None:
        raise HTTPException(status_code=404, detail="stream tidak ditemukan")
    return _to_out(stream)


@router.post("/start", response_model=StreamOut)
def start_stream(payload: StreamStartRequest, db: Session = Depends(get_db)) -> StreamOut:
    manager = get_stream_manager()
    try:
        stream = manager.start(
            db,
            account_id=payload.account_id,
            video_id=payload.video_id,
            bitrate=payload.bitrate,
            resolution=payload.resolution,
            fps=payload.fps,
            audio_bitrate=payload.audio_bitrate,
            preset=payload.preset,
            loop=payload.loop,
            auto_restart=payload.auto_restart,
        )
        db.commit()
        db.refresh(stream)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _to_out(stream)


@router.post("/stop/{stream_id}", response_model=StreamOut)
def stop_stream(stream_id: int, db: Session = Depends(get_db)) -> StreamOut:
    manager = get_stream_manager()
    try:
        stream = manager.stop(db, stream_id)
        db.commit()
        db.refresh(stream)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_out(stream)


@router.post("/restart/{stream_id}", response_model=StreamOut)
def restart_stream(stream_id: int, db: Session = Depends(get_db)) -> StreamOut:
    manager = get_stream_manager()
    try:
        stream = manager.restart(db, stream_id)
        db.commit()
        db.refresh(stream)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _to_out(stream)


@router.get("/logs/{stream_id}", response_model=StreamLogResponse)
def stream_logs(stream_id: int, limit: int = 200) -> StreamLogResponse:
    manager = get_stream_manager()
    return StreamLogResponse(stream_id=stream_id, lines=manager.tail_logs(stream_id, limit=limit))
