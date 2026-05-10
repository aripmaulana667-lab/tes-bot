"""Bootstrap helpers: create folders and the default admin user."""

from __future__ import annotations

import os

from app.config import Settings
from app.database import init_db, session_scope
from app.models import User
from app.utils.security import hash_password


def ensure_directories(settings: Settings) -> None:
    for path in (settings.base_dir, settings.videos_dir, settings.logs_dir, settings.bin_dir):
        os.makedirs(path, exist_ok=True)


def ensure_default_admin(settings: Settings) -> None:
    with session_scope() as db:
        existing = db.query(User).filter(User.username == settings.default_admin_username).one_or_none()
        if existing is None:
            user = User(
                username=settings.default_admin_username,
                password_hash=hash_password(settings.default_admin_password),
                api_token=settings.api_token,
            )
            db.add(user)
        else:
            # Keep the API token in sync between config and DB.
            existing.api_token = settings.api_token


def bootstrap_environment(settings: Settings) -> None:
    ensure_directories(settings)
    init_db()
    ensure_default_admin(settings)
