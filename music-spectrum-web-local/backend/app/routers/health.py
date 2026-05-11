"""Health check router."""
from __future__ import annotations

import platform
import time

from fastapi import APIRouter

from ..services.spectrum import list_styles

router = APIRouter(tags=["health"])

_started_at = time.time()


@router.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "service": "music-spectrum-lyrics-studio",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "uptime_seconds": round(time.time() - _started_at, 1),
        "spectrum_styles": list_styles(),
    }
