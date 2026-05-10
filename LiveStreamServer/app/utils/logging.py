"""Logging helpers."""

from __future__ import annotations

import logging
import os
from typing import Optional

from app.config import get_settings


def get_logger(name: str = "livestream") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    return logger


def stream_log_path(stream_id: int, logs_dir: Optional[str] = None) -> str:
    settings = get_settings()
    base = logs_dir or settings.logs_dir
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"stream-{stream_id}.log")
