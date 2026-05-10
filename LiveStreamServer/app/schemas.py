"""Pydantic schemas (request/response models)."""

from __future__ import annotations

import datetime as _dt
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Auth ----------


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    api_token: str
    username: str


# ---------- Server ----------


class ServerStatus(BaseModel):
    app: str
    version: str = "1.0.0"
    uptime_seconds: float
    ffmpeg_installed: bool
    ffmpeg_path: Optional[str] = None
    ffmpeg_version: Optional[str] = None
    base_dir: str
    videos_dir: str
    active_streams: int


class FfmpegStatus(BaseModel):
    installed: bool
    path: Optional[str] = None
    version: Optional[str] = None


class InstallFfmpegResponse(BaseModel):
    installed: bool
    path: Optional[str] = None
    version: Optional[str] = None
    message: str


# ---------- Videos ----------


class VideoOut(BaseModel):
    id: int
    filename: str
    original_name: str
    size: int
    duration: Optional[float] = None
    created_at: _dt.datetime

    class Config:
        from_attributes = True


class VideoRename(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=255)


# ---------- Accounts ----------


class AccountIn(BaseModel):
    name: str
    platform: str = "custom"
    rtmp_url: str
    stream_key: str
    default_bitrate: str = "2500k"
    default_resolution: str = "1280x720"
    is_active: bool = True


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[str] = None
    rtmp_url: Optional[str] = None
    stream_key: Optional[str] = None
    default_bitrate: Optional[str] = None
    default_resolution: Optional[str] = None
    is_active: Optional[bool] = None


class AccountOut(BaseModel):
    id: int
    name: str
    platform: str
    rtmp_url: str
    stream_key_masked: str
    default_bitrate: str
    default_resolution: str
    is_active: bool
    created_at: _dt.datetime


# ---------- Streams ----------


class StreamStartRequest(BaseModel):
    account_id: int
    video_id: int
    bitrate: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    audio_bitrate: Optional[str] = None
    preset: Optional[str] = None
    loop: Optional[bool] = None
    auto_restart: Optional[bool] = None


class StreamOut(BaseModel):
    id: int
    account_id: int
    account_name: str
    platform: str
    video_id: int
    video_name: str
    status: str
    pid: Optional[int] = None
    bitrate: str
    resolution: str
    fps: int
    loop: bool
    auto_restart: bool
    started_at: Optional[_dt.datetime] = None
    stopped_at: Optional[_dt.datetime] = None
    last_error: Optional[str] = None


class StreamLogLine(BaseModel):
    line: str


class StreamLogResponse(BaseModel):
    stream_id: int
    lines: List[str]


# ---------- System ----------


class SystemResources(BaseModel):
    cpu_percent: float
    ram_percent: float
    ram_used_mb: float
    ram_total_mb: float
    disk_used_mb: float
    disk_total_mb: float
    videos_dir_used_mb: float
    active_streams: int
    ffmpeg_installed: bool
    uptime_seconds: float
