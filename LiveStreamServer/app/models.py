"""SQLAlchemy ORM models."""

from __future__ import annotations

import datetime as _dt

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> _dt.datetime:
    return _dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    api_token = Column(String(128), unique=True, nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), unique=True, nullable=False)
    original_name = Column(String(255), nullable=False)
    path = Column(String(1024), nullable=False)
    size = Column(Integer, nullable=False, default=0)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    platform = Column(String(64), nullable=False, default="custom")
    rtmp_url = Column(String(512), nullable=False)
    stream_key = Column(String(512), nullable=False)
    default_bitrate = Column(String(16), default="2500k")
    default_resolution = Column(String(16), default="1280x720")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)


class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    status = Column(String(32), default="stopped", nullable=False)
    pid = Column(Integer, nullable=True)
    bitrate = Column(String(16), default="2500k")
    resolution = Column(String(16), default="1280x720")
    fps = Column(Integer, default=30)
    audio_bitrate = Column(String(16), default="128k")
    preset = Column(String(32), default="veryfast")
    loop = Column(Boolean, default=True, nullable=False)
    auto_restart = Column(Boolean, default=False, nullable=False)
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    log_path = Column(String(1024), nullable=True)

    account = relationship("Account", lazy="joined")
    video = relationship("Video", lazy="joined")


class StreamLog(Base):
    __tablename__ = "stream_logs"

    id = Column(Integer, primary_key=True)
    stream_id = Column(Integer, ForeignKey("streams.id"), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(16), default="info")
    created_at = Column(DateTime, default=_now, nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=False, default="")
