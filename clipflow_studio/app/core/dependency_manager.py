"""Detect, install, and repair external dependencies.

This module deliberately avoids hard imports of optional packages so that the
GUI can still start when nothing is installed -- it only reports the status.
"""
from __future__ import annotations

import importlib
import importlib.metadata as importlib_metadata
import io
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from ..utils import config as cfg
from ..utils.logger import get_logger

_LOG = get_logger("deps")

ProgressFn = Callable[[str, float], None]
"""Callback signature: ``(message, progress_0_to_1)``."""


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------
@dataclass
class DependencyStatus:
    name: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None
    can_install: bool = False
    install_hint: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def _has_internet(host: str = "1.1.1.1", port: int = 53, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _run_subprocess(args: List[str], timeout: float = 30.0) -> Tuple[int, str, str]:
    """Run ``args`` and return ``(returncode, stdout, stderr)``."""
    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"Command timed out after {exc.timeout}s"
    return proc.returncode, proc.stdout.decode(errors="ignore"), proc.stderr.decode(
        errors="ignore"
    )


def _which(name: str) -> Optional[str]:
    return shutil.which(name)


def _is_windows() -> bool:
    return os.name == "nt"


# ---------------------------------------------------------------------------
# Python / pip
# ---------------------------------------------------------------------------
def check_python() -> DependencyStatus:
    return DependencyStatus(
        name="Python",
        installed=True,
        version=platform.python_version(),
        path=sys.executable,
    )


def check_pip() -> DependencyStatus:
    code, stdout, stderr = _run_subprocess([sys.executable, "-m", "pip", "--version"])
    if code != 0:
        return DependencyStatus(
            name="pip",
            installed=False,
            error=stderr or stdout or "pip not available",
            can_install=False,
        )
    version = stdout.strip().split()[1] if stdout.strip() else None
    return DependencyStatus(name="pip", installed=True, version=version)


def check_python_package(package: str) -> DependencyStatus:
    """Return whether the given importable package is available."""
    importable = package.replace("-", "_")
    try:
        version = importlib_metadata.version(package)
        return DependencyStatus(name=package, installed=True, version=version)
    except importlib_metadata.PackageNotFoundError:
        pass
    # Some libs (e.g. faster_whisper) report differently in import vs metadata
    try:
        importlib.import_module(importable)
        return DependencyStatus(
            name=package,
            installed=True,
            version="unknown",
        )
    except ImportError as exc:
        return DependencyStatus(
            name=package,
            installed=False,
            error=str(exc),
            can_install=True,
            install_hint=f"pip install {package}",
        )


def install_python_package(package: str, upgrade: bool = False) -> Tuple[bool, str]:
    args = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        args.append("-U")
    args.append(package)
    _LOG.info("pip install %s", package)
    code, stdout, stderr = _run_subprocess(args, timeout=600)
    output = stdout + "\n" + stderr
    return code == 0, output


def update_package(package: str) -> Tuple[bool, str]:
    return install_python_package(package, upgrade=True)


def install_python_requirements(requirements_path: Optional[str] = None) -> Tuple[bool, str]:
    if requirements_path is None:
        requirements_path = os.path.join(cfg.get_project_root(), "requirements.txt")
    if not os.path.exists(requirements_path):
        return False, f"requirements.txt not found at {requirements_path}"
    args = [sys.executable, "-m", "pip", "install", "-r", requirements_path]
    _LOG.info("pip install -r %s", requirements_path)
    code, stdout, stderr = _run_subprocess(args, timeout=900)
    output = stdout + "\n" + stderr
    return code == 0, output


# ---------------------------------------------------------------------------
# FFmpeg
# ---------------------------------------------------------------------------
def get_ffmpeg_path() -> Optional[str]:
    """Resolve a usable FFmpeg path (config -> tools/ -> PATH)."""
    saved = cfg.get("ffmpeg_path")
    if saved and os.path.exists(saved):
        return saved
    local = _local_ffmpeg_path()
    if local and os.path.exists(local):
        return local
    return _which("ffmpeg")


def _local_ffmpeg_path() -> Optional[str]:
    base = os.path.join(cfg.get_tools_dir(), "ffmpeg")
    candidates = []
    if _is_windows():
        candidates.append(os.path.join(base, "bin", "ffmpeg.exe"))
        candidates.append(os.path.join(base, "ffmpeg.exe"))
    else:
        candidates.append(os.path.join(base, "bin", "ffmpeg"))
        candidates.append(os.path.join(base, "ffmpeg"))
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def save_ffmpeg_path(path: str) -> None:
    cfg.set_value("ffmpeg_path", path)
    ffprobe = path.replace("ffmpeg.exe", "ffprobe.exe").replace("ffmpeg", "ffprobe")
    if os.path.exists(ffprobe):
        cfg.set_value("ffprobe_path", ffprobe)


def check_ffmpeg() -> DependencyStatus:
    path = get_ffmpeg_path()
    if not path:
        return DependencyStatus(
            name="FFmpeg",
            installed=False,
            error="ffmpeg not found",
            can_install=_is_windows(),
            install_hint="Install FFmpeg Online (Windows) atau apt install ffmpeg / brew install ffmpeg.",
        )
    code, stdout, stderr = _run_subprocess([path, "-version"], timeout=10)
    if code != 0:
        return DependencyStatus(
            name="FFmpeg",
            installed=False,
            error=stderr or stdout or "ffmpeg failed to run",
            path=path,
        )
    version = stdout.splitlines()[0] if stdout else None
    return DependencyStatus(name="FFmpeg", installed=True, version=version, path=path)


_FFMPEG_WIN_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)


def download_ffmpeg_windows(progress: Optional[ProgressFn] = None) -> Tuple[bool, str]:
    """Download a Windows FFmpeg build to ``tools/ffmpeg/`` and update config."""
    if not _is_windows():
        return False, "Auto-install FFmpeg currently supports Windows only."
    if not _has_internet():
        return False, "Tidak ada koneksi internet."

    target_root = os.path.join(cfg.get_tools_dir(), "ffmpeg")
    os.makedirs(target_root, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "ffmpeg.zip")
            try:
                _download_with_progress(
                    _FFMPEG_WIN_URL,
                    zip_path,
                    progress=progress,
                    label="Downloading FFmpeg",
                )
            except Exception as exc:  # noqa: BLE001
                return False, f"Download FFmpeg gagal: {exc}"

            try:
                _safe_extract_zip(zip_path, target_root)
            except (zipfile.BadZipFile, OSError) as exc:
                return False, f"Extract FFmpeg gagal: {exc}"

        ffmpeg_exe = _find_executable_in_tree(target_root, "ffmpeg.exe")
        if not ffmpeg_exe:
            return False, "Binari ffmpeg.exe tidak ditemukan setelah extract."
        save_ffmpeg_path(ffmpeg_exe)
        return True, ffmpeg_exe
    except PermissionError as exc:
        return False, f"Permission error: {exc}"
    except OSError as exc:
        return False, f"OS error saat install FFmpeg: {exc}"


# ---------------------------------------------------------------------------
# Deno
# ---------------------------------------------------------------------------
def get_deno_path() -> Optional[str]:
    saved = cfg.get("deno_path")
    if saved and os.path.exists(saved):
        return saved
    local = _local_deno_path()
    if local and os.path.exists(local):
        return local
    return _which("deno")


def _local_deno_path() -> Optional[str]:
    base = os.path.join(cfg.get_tools_dir(), "deno")
    candidates = [
        os.path.join(base, "deno.exe" if _is_windows() else "deno"),
        os.path.join(base, "bin", "deno.exe" if _is_windows() else "deno"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def save_deno_path(path: str) -> None:
    cfg.set_value("deno_path", path)


def check_deno() -> DependencyStatus:
    path = get_deno_path()
    if not path:
        return DependencyStatus(
            name="Deno",
            installed=False,
            error="deno not found",
            can_install=_is_windows(),
            install_hint="Install Deno Online (Windows) atau brew install deno.",
        )
    code, stdout, stderr = _run_subprocess([path, "--version"], timeout=10)
    if code != 0:
        return DependencyStatus(
            name="Deno",
            installed=False,
            error=stderr or stdout or "deno failed to run",
            path=path,
        )
    version = stdout.splitlines()[0] if stdout else None
    return DependencyStatus(name="Deno", installed=True, version=version, path=path)


_DENO_WIN_URL = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip"


def install_deno_windows(progress: Optional[ProgressFn] = None) -> Tuple[bool, str]:
    if not _is_windows():
        return False, "Auto-install Deno currently supports Windows only."
    if not _has_internet():
        return False, "Tidak ada koneksi internet."

    target = os.path.join(cfg.get_tools_dir(), "deno")
    os.makedirs(target, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "deno.zip")
            try:
                _download_with_progress(
                    _DENO_WIN_URL,
                    zip_path,
                    progress=progress,
                    label="Downloading Deno",
                )
            except Exception as exc:  # noqa: BLE001
                return False, f"Download Deno gagal: {exc}"

            try:
                _safe_extract_zip(zip_path, target)
            except (zipfile.BadZipFile, OSError) as exc:
                return False, f"Install Deno gagal saat extract: {exc}"

        deno_exe = _find_executable_in_tree(target, "deno.exe")
        if not deno_exe:
            return False, "Binari deno.exe tidak ditemukan setelah install."
        save_deno_path(deno_exe)
        return True, deno_exe
    except PermissionError as exc:
        return False, f"Permission error: {exc}"
    except OSError as exc:
        return False, f"OS error saat install Deno: {exc}"


# ---------------------------------------------------------------------------
# Aggregate / utilities
# ---------------------------------------------------------------------------
PYTHON_PACKAGES: Tuple[str, ...] = (
    "yt-dlp",
    "faster-whisper",
    "sentence-transformers",
    "customtkinter",
)


def check_all_dependencies() -> List[DependencyStatus]:
    statuses: List[DependencyStatus] = [
        check_python(),
        check_pip(),
        check_ffmpeg(),
        check_deno(),
    ]
    for pkg in PYTHON_PACKAGES:
        statuses.append(check_python_package(pkg))
    statuses.append(_check_sqlite())
    statuses.append(_check_git_optional())
    return statuses


def install_missing_dependencies(progress: Optional[ProgressFn] = None) -> Dict[str, str]:
    """Try to install everything that is missing.  Returns a per-item report."""
    report: Dict[str, str] = {}
    statuses = check_all_dependencies()
    total = max(1, len([s for s in statuses if not s.installed and s.can_install]))
    done = 0

    def _emit(msg: str, frac: float) -> None:
        if progress:
            progress(msg, frac)

    for status in statuses:
        if status.installed or not status.can_install:
            continue
        done += 1
        if status.name == "FFmpeg":
            _emit("Installing FFmpeg ...", done / total)
            ok, info = download_ffmpeg_windows(progress=progress)
            report["FFmpeg"] = info if ok else f"FAILED: {info}"
        elif status.name == "Deno":
            _emit("Installing Deno ...", done / total)
            ok, info = install_deno_windows(progress=progress)
            report["Deno"] = info if ok else f"FAILED: {info}"
        elif status.name in PYTHON_PACKAGES:
            _emit(f"Installing {status.name} ...", done / total)
            ok, info = install_python_package(status.name)
            report[status.name] = "OK" if ok else f"FAILED: {info[-400:]}"
    _emit("Done", 1.0)
    return report


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _check_sqlite() -> DependencyStatus:
    try:
        import sqlite3  # noqa: WPS433

        return DependencyStatus(name="SQLite", installed=True, version=sqlite3.sqlite_version)
    except ImportError as exc:
        return DependencyStatus(name="SQLite", installed=False, error=str(exc))


def _check_git_optional() -> DependencyStatus:
    path = _which("git")
    if not path:
        return DependencyStatus(
            name="Git (optional)",
            installed=False,
            install_hint="https://git-scm.com/downloads",
        )
    code, stdout, _ = _run_subprocess([path, "--version"])
    return DependencyStatus(
        name="Git (optional)",
        installed=code == 0,
        version=stdout.strip() or None,
        path=path,
    )


def _download_with_progress(
    url: str,
    dest_path: str,
    progress: Optional[ProgressFn] = None,
    label: str = "Downloading",
    chunk_size: int = 64 * 1024,
) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ClipFlow-Studio/0.1 (+https://example.local)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 (trusted URL)
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        with open(dest_path, "wb") as fh:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                fh.write(chunk)
                downloaded += len(chunk)
                if progress:
                    if total:
                        progress(f"{label}: {downloaded // 1024}/{total // 1024} KB", downloaded / total)
                    else:
                        progress(f"{label}: {downloaded // 1024} KB", 0.0)


def _safe_extract_zip(zip_path: str, target_dir: str) -> None:
    """Safely extract zip preventing path traversal."""
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            target_path = os.path.realpath(os.path.join(target_dir, member))
            if not target_path.startswith(os.path.realpath(target_dir)):
                raise OSError(f"Suspicious zip entry blocked: {member}")
        zf.extractall(target_dir)


def _find_executable_in_tree(root: str, exe_name: str) -> Optional[str]:
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.lower() == exe_name.lower():
                return os.path.join(dirpath, filename)
    return None


def open_folder(path: str) -> bool:
    """Open ``path`` in the OS file manager.  Returns True on best-effort."""
    if not os.path.isdir(path):
        return False
    try:
        if _is_windows():
            os.startfile(path)  # type: ignore[attr-defined]  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])  # noqa: S603
        else:
            subprocess.Popen(["xdg-open", path])  # noqa: S603
        return True
    except OSError as exc:
        _LOG.warning("Failed to open folder %s: %s", path, exc)
        return False


def has_internet() -> bool:
    """Public helper, also exposed for the UI."""
    return _has_internet()


# Aliases requested by the spec
check_all = check_all_dependencies
install_missing = install_missing_dependencies


# Buffered echo helper for CLI/diagnostic mode
def diagnostics_summary() -> str:
    buf = io.StringIO()
    for status in check_all_dependencies():
        buf.write(
            "{name:<28} {status:<14} {version} {path}\n".format(
                name=status.name,
                status="OK" if status.installed else "MISSING",
                version=status.version or "-",
                path=status.path or "",
            )
        )
    return buf.getvalue()


# Keep a reference so timestamps in unit tests are deterministic
_STARTED_AT = time.time()
