"""SQLite-backed project history.

The schema is intentionally simple: one ``projects`` row per analyzed video,
plus one ``clips`` row per generated clip.  The DB lives in
``config/clipflow.db`` so that it survives across runs.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from ..utils.config import get_database_path
from ..utils.logger import get_logger

_LOG = get_logger("database")
_DB_LOCK = threading.RLock()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    url TEXT NOT NULL,
    video_path TEXT,
    audio_path TEXT,
    transcript_path TEXT,
    duration REAL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS clips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    score REAL,
    transcript TEXT,
    duration_preset INTEGER,
    output_path TEXT,
    exported INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    metadata_json TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_clips_project ON clips(project_id);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at);
"""


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Yield a thread-safe SQLite connection."""
    with _DB_LOCK:
        conn = sqlite3.connect(get_database_path())
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db() -> None:
    """Create the tables if they don't exist."""
    with _connect() as conn:
        conn.executescript(_SCHEMA)
    _LOG.debug("Database initialized at %s", get_database_path())


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    data = dict(row)
    metadata = data.pop("metadata_json", None)
    if metadata:
        try:
            data["metadata"] = json.loads(metadata)
        except json.JSONDecodeError:
            data["metadata"] = {}
    else:
        data["metadata"] = {}
    return data


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
def add_project(
    *,
    url: str,
    title: Optional[str] = None,
    video_path: Optional[str] = None,
    audio_path: Optional[str] = None,
    transcript_path: Optional[str] = None,
    duration: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    init_db()
    now = time.time()
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO projects (
                title, url, video_path, audio_path, transcript_path,
                duration, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                url,
                video_path,
                audio_path,
                transcript_path,
                duration,
                now,
                now,
                metadata_json,
            ),
        )
        return int(cur.lastrowid)


def update_project(project_id: int, **fields: Any) -> None:
    if not fields:
        return
    init_db()
    columns = []
    values: List[Any] = []
    for key, value in fields.items():
        if key == "metadata":
            columns.append("metadata_json = ?")
            values.append(json.dumps(value or {}, ensure_ascii=False))
        elif key in {
            "title",
            "url",
            "video_path",
            "audio_path",
            "transcript_path",
            "duration",
        }:
            columns.append(f"{key} = ?")
            values.append(value)
    columns.append("updated_at = ?")
    values.append(time.time())
    values.append(project_id)
    sql = f"UPDATE projects SET {', '.join(columns)} WHERE id = ?"
    with _connect() as conn:
        conn.execute(sql, values)


def get_project(project_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        return _row_to_dict(row) if row else None


def list_projects(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def delete_project(project_id: int) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))


# ---------------------------------------------------------------------------
# Clips
# ---------------------------------------------------------------------------
def add_clip(
    *,
    project_id: int,
    start_time: float,
    end_time: float,
    score: float,
    transcript: str,
    duration_preset: Optional[int] = None,
    output_path: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    init_db()
    now = time.time()
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO clips (
                project_id, start_time, end_time, score, transcript,
                duration_preset, output_path, exported, created_at,
                metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                project_id,
                start_time,
                end_time,
                score,
                transcript,
                duration_preset,
                output_path,
                now,
                metadata_json,
            ),
        )
        return int(cur.lastrowid)


def mark_clip_exported(clip_id: int, output_path: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE clips SET exported = 1, output_path = ? WHERE id = ?",
            (output_path, clip_id),
        )


def list_clips(project_id: int) -> List[Dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM clips WHERE project_id = ? ORDER BY start_time ASC",
            (project_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
