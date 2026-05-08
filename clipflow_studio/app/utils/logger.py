"""Application-wide logging configuration."""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import get_logs_dir

_LOGGER_NAME = "clipflow"
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialized = False


def _resolve_log_path() -> str:
    logs_dir = get_logs_dir()
    os.makedirs(logs_dir, exist_ok=True)
    return os.path.join(logs_dir, "clipflow.log")


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure root + clipflow loggers exactly once."""
    global _initialized
    logger = logging.getLogger(_LOGGER_NAME)
    if _initialized:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    try:
        file_handler = RotatingFileHandler(
            _resolve_log_path(),
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # We must not crash if the log directory is not writable.
        logger.warning("Log file could not be opened; falling back to console only")

    _initialized = True
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a child logger that inherits the configured handlers."""
    setup_logging()
    if name and name != _LOGGER_NAME:
        return logging.getLogger(f"{_LOGGER_NAME}.{name}")
    return logging.getLogger(_LOGGER_NAME)
