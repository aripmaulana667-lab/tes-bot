"""FFmpeg discovery, installation and capability probing.

The user shouldn't need to fiddle with PATH. We:
  1. Honor an explicit user-configured path.
  2. Look for a bundled ``ffmpeg``/``ffprobe`` under ``app/assets/ffmpeg``.
  3. Fall back to ``shutil.which``.
  4. Offer a one-click "Install FFmpeg Online" that downloads a static build
     from BtbN's GitHub release (Windows) / johnvansickle.com (Linux) and
     installs it under the application data dir.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLED_DIR = REPO_ROOT / "app" / "assets" / "ffmpeg"
CONFIG_PATH = REPO_ROOT / "config.json"


WINDOWS_FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/"
    "ffmpeg-master-latest-win64-gpl.zip"
)
LINUX_FFMPEG_URL = (
    "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
)


@dataclass
class FFmpegStatus:
    found: bool
    ffmpeg_path: str = ""
    ffprobe_path: str = ""
    version: str = ""
    encoders: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def has_nvenc(self) -> bool:
        return any("nvenc" in e for e in self.encoders)

    @property
    def has_qsv(self) -> bool:
        return any("qsv" in e for e in self.encoders)

    @property
    def has_amf(self) -> bool:
        return any("amf" in e for e in self.encoders)


def _load_configured_path() -> str:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data.get("ffmpeg_path", "") or ""
    except (OSError, json.JSONDecodeError):
        return ""


def save_configured_path(path: str) -> None:
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        else:
            data = {}
    except (OSError, json.JSONDecodeError):
        data = {}
    data["ffmpeg_path"] = path
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _which(name: str) -> str:
    return shutil.which(name) or ""


def _bundled() -> tuple[str, str]:
    suffix = ".exe" if platform.system() == "Windows" else ""
    ff = BUNDLED_DIR / f"ffmpeg{suffix}"
    fp = BUNDLED_DIR / f"ffprobe{suffix}"
    if ff.exists():
        return str(ff), str(fp) if fp.exists() else ""
    return "", ""


def _no_window_kwargs() -> dict:
    """Hide the flashing CMD window on Windows when running ffmpeg."""
    if platform.system() != "Windows":
        return {}
    creationflags = 0x08000000  # CREATE_NO_WINDOW
    return {"creationflags": creationflags}


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **_no_window_kwargs(),
    )


def probe_ffmpeg(path: str = "") -> FFmpegStatus:
    """Probe a given path (or detect automatically) and return status."""
    candidates: list[str] = []
    if path:
        candidates.append(path)
    cfg = _load_configured_path()
    if cfg and cfg not in candidates:
        candidates.append(cfg)
    b_ff, _ = _bundled()
    if b_ff and b_ff not in candidates:
        candidates.append(b_ff)
    sys_ff = _which("ffmpeg")
    if sys_ff and sys_ff not in candidates:
        candidates.append(sys_ff)

    for cand in candidates:
        if not cand or not Path(cand).exists():
            continue
        try:
            res = _run([cand, "-hide_banner", "-version"])
        except OSError as exc:
            continue
        if res.returncode != 0:
            continue
        first = res.stdout.splitlines()[0] if res.stdout else ""
        version_match = re.search(r"ffmpeg version ([^\s]+)", first)
        version = version_match.group(1) if version_match else first

        # Probe encoders for hardware acceleration detection.
        encoders: list[str] = []
        try:
            enc = _run([cand, "-hide_banner", "-encoders"])
            for line in enc.stdout.splitlines():
                line = line.strip()
                m = re.match(r"\s*[VAS\.][\.A-Z]*\s+(\S+)", line)
                if m:
                    encoders.append(m.group(1))
        except OSError:
            pass

        # Look up an ffprobe alongside.
        ffprobe = ""
        cand_dir = Path(cand).parent
        for name in ("ffprobe.exe", "ffprobe"):
            p = cand_dir / name
            if p.exists():
                ffprobe = str(p)
                break
        if not ffprobe:
            ffprobe = _which("ffprobe")

        return FFmpegStatus(
            found=True,
            ffmpeg_path=str(Path(cand)),
            ffprobe_path=ffprobe,
            version=version,
            encoders=encoders,
        )

    return FFmpegStatus(found=False, error="ffmpeg executable not found")


_encoder_verify_cache: dict[tuple[str, str], bool] = {}


def _verify_encoder(ffmpeg_path: str, encoder: str) -> bool:
    """Try a 1-frame dummy encode to confirm the encoder is actually usable.

    On many machines FFmpeg advertises ``h264_nvenc`` even when CUDA is not
    installed at runtime; this guard rejects those phantoms.
    """
    key = (ffmpeg_path, encoder)
    if key in _encoder_verify_cache:
        return _encoder_verify_cache[key]
    try:
        cmd = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=64x64:r=1",
            "-frames:v",
            "1",
            "-c:v",
            encoder,
            "-f",
            "null",
            "-",
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            **_no_window_kwargs(),
        )
        ok = res.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        ok = False
    _encoder_verify_cache[key] = ok
    return ok


def detect_encoder(status: FFmpegStatus, codec: str = "h264") -> str:
    """Return the preferred encoder name for the given codec.

    Falls back to ``libx264`` if the preferred hardware encoder is listed
    but cannot actually initialise (e.g. NVENC listed but no CUDA).
    """
    prefer_order = []
    if codec.lower() in ("h264", "x264"):
        prefer_order = ["h264_nvenc", "h264_qsv", "h264_amf", "libx264"]
    elif codec.lower() in ("hevc", "h265"):
        prefer_order = ["hevc_nvenc", "hevc_qsv", "hevc_amf", "libx265"]
    else:
        prefer_order = [codec]
    for enc in prefer_order:
        if enc not in status.encoders:
            continue
        if enc.startswith(("libx", "libx264", "libx265")):
            return enc
        if status.ffmpeg_path and _verify_encoder(status.ffmpeg_path, enc):
            return enc
    return "libx264"


# ---------------------------------------------------------------------------
# Auto-installation
# ---------------------------------------------------------------------------


def install_online(
    on_progress: Optional[Callable[[float, str], None]] = None,
) -> FFmpegStatus:
    """Download a static FFmpeg build and place it under ``app/assets/ffmpeg``.

    on_progress(0..1, "message") is called periodically.
    """
    on_progress = on_progress or (lambda *_: None)

    system = platform.system()
    if system == "Windows":
        url = WINDOWS_FFMPEG_URL
        archive_name = "ffmpeg.zip"
    elif system == "Linux":
        url = LINUX_FFMPEG_URL
        archive_name = "ffmpeg.tar.xz"
    else:
        return FFmpegStatus(
            found=False,
            error=f"Auto-install is not supported on {system}. Install FFmpeg manually.",
        )

    BUNDLED_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / archive_name
        on_progress(0.02, f"Downloading FFmpeg from {url}…")
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length") or 0)
                with archive.open("wb") as out:
                    read = 0
                    while True:
                        chunk = resp.read(64 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
                        read += len(chunk)
                        if total:
                            on_progress(
                                min(0.85, 0.05 + 0.8 * read / total),
                                f"Downloading FFmpeg… {read // (1024 * 1024)} MB",
                            )
        except Exception as exc:  # noqa: BLE001
            return FFmpegStatus(found=False, error=f"Download failed: {exc}")

        on_progress(0.9, "Extracting FFmpeg…")
        ff_path = ""
        fp_path = ""
        try:
            if system == "Windows":
                with zipfile.ZipFile(archive) as zf:
                    members = zf.namelist()
                    for m in members:
                        lower = m.lower()
                        if lower.endswith("/bin/ffmpeg.exe"):
                            target = BUNDLED_DIR / "ffmpeg.exe"
                            with zf.open(m) as src, target.open("wb") as dst:
                                shutil.copyfileobj(src, dst)
                            ff_path = str(target)
                        elif lower.endswith("/bin/ffprobe.exe"):
                            target = BUNDLED_DIR / "ffprobe.exe"
                            with zf.open(m) as src, target.open("wb") as dst:
                                shutil.copyfileobj(src, dst)
                            fp_path = str(target)
            else:
                with tarfile.open(archive, "r:xz") as tf:
                    for member in tf.getmembers():
                        name = member.name
                        if name.endswith("/ffmpeg"):
                            extracted = tf.extractfile(member)
                            if extracted is None:
                                continue
                            target = BUNDLED_DIR / "ffmpeg"
                            with target.open("wb") as dst:
                                shutil.copyfileobj(extracted, dst)
                            target.chmod(0o755)
                            ff_path = str(target)
                        elif name.endswith("/ffprobe"):
                            extracted = tf.extractfile(member)
                            if extracted is None:
                                continue
                            target = BUNDLED_DIR / "ffprobe"
                            with target.open("wb") as dst:
                                shutil.copyfileobj(extracted, dst)
                            target.chmod(0o755)
                            fp_path = str(target)
        except Exception as exc:  # noqa: BLE001
            return FFmpegStatus(found=False, error=f"Extraction failed: {exc}")

        if not ff_path:
            return FFmpegStatus(
                found=False, error="FFmpeg binary not found in downloaded archive"
            )

    save_configured_path(ff_path)
    on_progress(1.0, "FFmpeg installed.")
    return probe_ffmpeg(ff_path)


__all__ = [
    "FFmpegStatus",
    "probe_ffmpeg",
    "detect_encoder",
    "install_online",
    "save_configured_path",
]
