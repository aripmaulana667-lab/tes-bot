"""SQLAlchemy session and engine."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import get_settings


Base = declarative_base()


def _engine_url() -> str:
    settings = get_settings()
    url = settings.database_url
    if url.startswith("sqlite"):
        # Make sure the parent dir exists for the sqlite file.
        path = url.replace("sqlite:///", "")
        if path:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    return url


_engine = create_engine(
    _engine_url(),
    future=True,
    connect_args={"check_same_thread": False} if _engine_url().startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    # Import so that all models are registered on Base.metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=_engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
