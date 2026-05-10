"""Auto-installer for FFmpeg on Windows VPS/RDP.

The installer downloads a static Windows build from a well-known mirror,
extracts it into ``<base_dir>/bin/ffmpeg`` and remembers the resolved path
in ``config.json``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from typing import Optional, Tuple

import requests

from app.config import Settings, get_settings, update_settings


# Use a known stable URL. ``BtbN`` provides up-to-date Windows static builds.
FFMPEG_WIN_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)


def _exe_name() -> str:
    return "ffmpeg.exe" if os.name == "nt" else "ffmpeg"


def detect_ffmpeg(settings: Optional[Settings] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """Return ``(installed, path, version)`` for FFmpeg."""

    settings = settings or get_settings()
    candidates = []
    if settings.ffmpeg_path:
        candidates.append(settings.ffmpeg_path)
    candidates.append(os.path.join(settings.bin_dir, "ffmpeg", "bin", _exe_name()))
    candidates.append(os.path.join(settings.bin_dir, _exe_name()))

    on_path = shutil.which("ffmpeg")
    if on_path:
        candidates.append(on_path)

    for cand in candidates:
        if cand and os.path.isfile(cand):
            version = _ffmpeg_version(cand)
            if version is not None:
                return True, cand, version
    return False, None, None


def _ffmpeg_version(path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [path, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            first = result.stdout.splitlines()[0] if result.stdout else ""
            return first.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def install_ffmpeg(force: bool = False) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """Download and extract FFmpeg on Windows.

    Returns ``(installed, message, path, version)``.
    """

    settings = get_settings()

    if not force:
        installed, path, version = detect_ffmpeg(settings)
        if installed and path:
            update_settings(ffmpeg_path=path)
            return True, "FFmpeg sudah terpasang", path, version

    if os.name != "nt":
        # Outside Windows we just rely on system ffmpeg if available.
        on_path = shutil.which("ffmpeg")
        if on_path:
            update_settings(ffmpeg_path=on_path)
            version = _ffmpeg_version(on_path)
            return True, "Menggunakan ffmpeg dari PATH", on_path, version
        return (
            False,
            "Auto-install hanya didukung di Windows. Silakan install ffmpeg manual.",
            None,
            None,
        )

    target_root = os.path.join(settings.bin_dir, "ffmpeg")
    os.makedirs(settings.bin_dir, exist_ok=True)

    tmp_dir = tempfile.mkdtemp(prefix="ffmpeg-dl-")
    archive_path = os.path.join(tmp_dir, "ffmpeg.zip")
    try:
        with requests.get(FFMPEG_WIN_URL, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(archive_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        # Cleanup any previous install.
        if os.path.isdir(target_root):
            shutil.rmtree(target_root, ignore_errors=True)
        os.makedirs(target_root, exist_ok=True)

        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(target_root)

        # Flatten the inner ``ffmpeg-*`` directory the archive uses.
        entries = os.listdir(target_root)
        if len(entries) == 1 and os.path.isdir(os.path.join(target_root, entries[0])):
            inner = os.path.join(target_root, entries[0])
            for item in os.listdir(inner):
                shutil.move(os.path.join(inner, item), os.path.join(target_root, item))
            shutil.rmtree(inner, ignore_errors=True)

        ffmpeg_exe = os.path.join(target_root, "bin", _exe_name())
        if not os.path.isfile(ffmpeg_exe):
            return False, "ffmpeg.exe tidak ditemukan setelah ekstrak", None, None

        update_settings(ffmpeg_path=ffmpeg_exe)
        return True, "FFmpeg berhasil di-install", ffmpeg_exe, _ffmpeg_version(ffmpeg_exe)
    except requests.RequestException as exc:
        return False, f"Gagal download FFmpeg: {exc}", None, None
    except (OSError, zipfile.BadZipFile) as exc:
        return False, f"Gagal ekstrak FFmpeg: {exc}", None, None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def python_dependency_check() -> Tuple[bool, str]:
    """Lightweight self-check for the dependency list."""

    required = ["fastapi", "uvicorn", "sqlalchemy", "psutil", "requests"]
    missing = []
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    if missing:
        return False, "Dependency hilang: " + ", ".join(missing)
    return True, f"Semua dependency utama tersedia (Python {sys.version.split()[0]})"
