"""System resource snapshot via psutil."""

from __future__ import annotations

import os
import time
from typing import Optional

import psutil

from app.config import get_settings
from app.schemas import SystemResources
from app.services.ffmpeg_installer import detect_ffmpeg
from app.services.stream_manager import get_stream_manager


_START_TS = time.time()


def _dir_size(path: str) -> int:
    total = 0
    if not os.path.isdir(path):
        return 0
    for root, _, files in os.walk(path):
        for name in files:
            fp = os.path.join(root, name)
            try:
                total += os.path.getsize(fp)
            except OSError:
                continue
    return total


def collect_resources() -> SystemResources:
    settings = get_settings()
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(settings.base_dir if os.path.isdir(settings.base_dir) else ".")
    videos_used = _dir_size(settings.videos_dir)
    installed, _, _ = detect_ffmpeg(settings)

    return SystemResources(
        cpu_percent=float(cpu),
        ram_percent=float(mem.percent),
        ram_used_mb=mem.used / (1024 * 1024),
        ram_total_mb=mem.total / (1024 * 1024),
        disk_used_mb=disk.used / (1024 * 1024),
        disk_total_mb=disk.total / (1024 * 1024),
        videos_dir_used_mb=videos_used / (1024 * 1024),
        active_streams=get_stream_manager().active_count(),
        ffmpeg_installed=installed,
        uptime_seconds=time.time() - _START_TS,
    )


def server_uptime_seconds() -> float:
    return time.time() - _START_TS
