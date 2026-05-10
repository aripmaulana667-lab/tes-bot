"""Server status & FFmpeg installer endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import require_token
from app.config import get_settings
from app.schemas import FfmpegStatus, InstallFfmpegResponse, ServerStatus
from app.services.ffmpeg_installer import detect_ffmpeg, install_ffmpeg, python_dependency_check
from app.services.stream_manager import get_stream_manager
from app.services.system_service import server_uptime_seconds


router = APIRouter(prefix="/server", tags=["server"])


@router.get("/status", response_model=ServerStatus, dependencies=[Depends(require_token)])
def server_status() -> ServerStatus:
    settings = get_settings()
    installed, path, version = detect_ffmpeg(settings)
    return ServerStatus(
        app=settings.app_name,
        uptime_seconds=server_uptime_seconds(),
        ffmpeg_installed=installed,
        ffmpeg_path=path,
        ffmpeg_version=version,
        base_dir=settings.base_dir,
        videos_dir=settings.videos_dir,
        active_streams=get_stream_manager().active_count(),
    )


@router.get("/check-ffmpeg", response_model=FfmpegStatus, dependencies=[Depends(require_token)])
def check_ffmpeg() -> FfmpegStatus:
    installed, path, version = detect_ffmpeg()
    return FfmpegStatus(installed=installed, path=path, version=version)


@router.post(
    "/install-ffmpeg",
    response_model=InstallFfmpegResponse,
    dependencies=[Depends(require_token)],
)
def install_ffmpeg_endpoint(force: bool = False) -> InstallFfmpegResponse:
    installed, message, path, version = install_ffmpeg(force=force)
    return InstallFfmpegResponse(installed=installed, path=path, version=version, message=message)


@router.get("/check-deps", dependencies=[Depends(require_token)])
def check_deps() -> dict:
    ok, message = python_dependency_check()
    return {"ok": ok, "message": message}
