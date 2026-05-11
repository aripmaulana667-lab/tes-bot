"""FFmpeg discovery, status, and portable installation."""
from __future__ import annotations

import asyncio
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import httpx

from ..config import FFMPEG_DIR, FFMPEG_PATH, FFPROBE_PATH, IS_WINDOWS, TEMP_DIR


WINDOWS_BUILDS = [
    "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-gpl.zip",
]

LINUX_BUILDS = [
    "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-linux64-gpl.tar.xz",
]


def _binary_name(name: str) -> str:
    return f"{name}.exe" if IS_WINDOWS else name


def portable_ffmpeg_path() -> Path:
    return FFMPEG_DIR / "bin" / _binary_name("ffmpeg")


def portable_ffprobe_path() -> Path:
    return FFMPEG_DIR / "bin" / _binary_name("ffprobe")


def find_ffmpeg() -> Tuple[Optional[str], str]:
    """Return (path, source) for ffmpeg binary."""
    if FFMPEG_PATH and Path(FFMPEG_PATH).exists():
        return FFMPEG_PATH, "env"
    portable = portable_ffmpeg_path()
    if portable.exists():
        return str(portable), "portable"
    sys_path = shutil.which("ffmpeg")
    if sys_path:
        return sys_path, "system"
    return None, "missing"


def find_ffprobe() -> Optional[str]:
    if FFPROBE_PATH and Path(FFPROBE_PATH).exists():
        return FFPROBE_PATH
    portable = portable_ffprobe_path()
    if portable.exists():
        return str(portable)
    return shutil.which("ffprobe")


def get_version(binary: str) -> str:
    try:
        result = subprocess.run(
            [binary, "-version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        line = (result.stdout or result.stderr or "").splitlines()
        return line[0] if line else ""
    except Exception as exc:  # pragma: no cover
        return f"error: {exc}"


def ffmpeg_status() -> dict:
    path, source = find_ffmpeg()
    if not path:
        return {
            "available": False,
            "source": source,
            "path": "",
            "version": "",
            "error": "FFmpeg tidak ditemukan. Gunakan tombol Install FFmpeg portable atau pasang manual.",
        }
    return {
        "available": True,
        "source": source,
        "path": path,
        "version": get_version(path),
        "error": "",
    }


async def probe_duration(path: str) -> float:
    ffprobe = find_ffprobe()
    if not ffprobe:
        ffmpeg, _ = find_ffmpeg()
        if not ffmpeg:
            return 0.0
        proc = await asyncio.create_subprocess_exec(
            ffmpeg,
            "-i",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        text = stderr.decode("utf-8", errors="ignore")
        for line in text.splitlines():
            if "Duration:" in line:
                try:
                    dur = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = dur.split(":")
                    return int(h) * 3600 + int(m) * 60 + float(s)
                except Exception:
                    return 0.0
        return 0.0

    proc = await asyncio.create_subprocess_exec(
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    try:
        return float(stdout.decode().strip())
    except Exception:
        return 0.0


async def install_portable(progress=None) -> dict:
    """Download FFmpeg portable build into tools/ffmpeg/."""
    urls = WINDOWS_BUILDS if IS_WINDOWS else LINUX_BUILDS
    last_err = ""
    for url in urls:
        try:
            if progress:
                await progress(0.0, f"Mengunduh {url} ...")
            async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
                async with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    total = int(resp.headers.get("Content-Length") or 0)
                    archive_path = TEMP_DIR / Path(url).name
                    downloaded = 0
                    with open(archive_path, "wb") as f:
                        async for chunk in resp.aiter_bytes(1024 * 256):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress and total:
                                pct = min(0.85, downloaded / total * 0.85)
                                await progress(pct, f"Mengunduh: {downloaded // 1024} KB")
            if progress:
                await progress(0.9, "Mengekstrak FFmpeg ...")
            _extract_archive(archive_path, FFMPEG_DIR)
            try:
                archive_path.unlink()
            except Exception:
                pass
            if not portable_ffmpeg_path().exists():
                raise RuntimeError("Binary FFmpeg tidak ditemukan setelah ekstrak.")
            if progress:
                await progress(1.0, "FFmpeg portable siap digunakan.")
            return ffmpeg_status()
        except Exception as exc:
            last_err = str(exc)
            continue
    raise RuntimeError(f"Gagal memasang FFmpeg portable: {last_err}")


def _extract_archive(archive_path: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    name = archive_path.name.lower()
    if name.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(dest)
    elif name.endswith(".tar.xz") or name.endswith(".tar.gz") or name.endswith(".tar"):
        import tarfile

        with tarfile.open(archive_path) as tf:
            tf.extractall(dest)
    else:
        raise RuntimeError(f"Format arsip tidak didukung: {archive_path.name}")
    _flatten_ffmpeg_dir(dest)


def _flatten_ffmpeg_dir(dest: Path) -> None:
    """Move extracted ffmpeg-*/bin into tools/ffmpeg/bin."""
    bin_target = dest / "bin"
    if bin_target.exists() and any(bin_target.iterdir()):
        return
    for child in dest.iterdir():
        if child.is_dir() and child.name.lower().startswith("ffmpeg"):
            inner_bin = child / "bin"
            if inner_bin.exists():
                bin_target.mkdir(parents=True, exist_ok=True)
                for f in inner_bin.iterdir():
                    target = bin_target / f.name
                    if target.exists():
                        try:
                            target.unlink()
                        except Exception:
                            pass
                    shutil.move(str(f), target)
            for extra in ("doc", "presets"):
                extra_dir = child / extra
                if extra_dir.exists():
                    target_dir = dest / extra
                    if target_dir.exists():
                        shutil.rmtree(target_dir, ignore_errors=True)
                    shutil.move(str(extra_dir), target_dir)
            try:
                shutil.rmtree(child)
            except Exception:
                pass
            break
