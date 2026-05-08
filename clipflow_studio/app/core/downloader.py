"""YouTube downloader powered by yt-dlp.

The module exposes a single :class:`Downloader` whose :meth:`download` method
runs synchronously and accepts a progress callback.  GUI code is expected to
run :meth:`download` from a background thread.

The downloader will:

1. Validate the URL with a lightweight Python regex.
2. If validation fails, optionally call the Deno helper as a fallback.
3. Try to download the video.
4. If the download fails, optionally update yt-dlp and retry.
5. If still failing, ask the Deno helper for metadata so the error log is rich.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..utils import config as cfg
from ..utils.logger import get_logger
from . import deno_helper, dependency_manager as deps

_LOG = get_logger("downloader")

ProgressFn = Callable[[str, float], None]


_YOUTUBE_REGEX = re.compile(
    r"^(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be)/.+",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def is_valid_youtube_url(url: str) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    return bool(_YOUTUBE_REGEX.match(url.strip()))


def validate_url(url: str, allow_deno_fallback: bool = True) -> Dict[str, Any]:
    """Try Python first, fall back to Deno when available."""
    url = (url or "").strip()
    if is_valid_youtube_url(url):
        return {"valid": True, "platform": "youtube", "url": url, "error": None, "source": "python"}
    if allow_deno_fallback and deno_helper.get_deno_path():
        result = deno_helper.validate_youtube_url_with_deno(url)
        result.setdefault("source", "deno")
        return result
    return {"valid": False, "platform": None, "url": url, "error": "invalid_url", "source": "python"}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class DownloadResult:
    success: bool
    video_path: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------
class Downloader:
    """Wrapper around yt-dlp with optional Deno fallback for diagnostics."""

    def __init__(
        self,
        *,
        outputs_dir: Optional[str] = None,
        ffmpeg_path: Optional[str] = None,
        max_height: int = 1080,
    ) -> None:
        self.outputs_dir = outputs_dir or cfg.get_temp_dir()
        os.makedirs(self.outputs_dir, exist_ok=True)
        self.ffmpeg_path = ffmpeg_path or deps.get_ffmpeg_path()
        self.max_height = max_height

    # -- Public API ----------------------------------------------------------
    def download(
        self,
        url: str,
        progress: Optional[ProgressFn] = None,
        *,
        allow_update: bool = True,
        on_update_question: Optional[Callable[[], bool]] = None,
    ) -> DownloadResult:
        """Run the full download workflow.

        ``on_update_question`` is invoked when the first attempt fails and the
        caller wants to confirm before yt-dlp is updated.  If it returns
        ``True`` the update goes ahead.  If ``allow_update`` is ``False``, no
        update happens regardless.
        """
        validation = validate_url(url)
        if not validation.get("valid"):
            return DownloadResult(success=False, error=validation.get("error") or "invalid_url")

        url = validation["url"]
        if progress:
            progress("Starting download ...", 0.0)

        first_error: Optional[str] = None
        result = self._try_download(url, progress=progress)
        if result.success:
            return result
        first_error = result.error or "unknown"
        _LOG.warning("First yt-dlp attempt failed: %s", first_error)

        proceed_with_update = allow_update
        if proceed_with_update and on_update_question is not None:
            try:
                proceed_with_update = bool(on_update_question())
            except Exception:  # noqa: BLE001
                proceed_with_update = False

        if proceed_with_update:
            if progress:
                progress("Updating yt-dlp ...", 0.0)
            ok, log = deps.update_package("yt-dlp")
            _LOG.info("yt-dlp update result: %s", "OK" if ok else log[-300:])
            if ok:
                retry = self._try_download(url, progress=progress)
                if retry.success:
                    return retry
                first_error = retry.error or first_error

        # Last-ditch: ask Deno for metadata so the user has *something*.
        meta = deno_helper.fetch_video_metadata_with_deno(url)
        return DownloadResult(
            success=False,
            error=first_error or "yt-dlp_failed",
            metadata=meta,
            title=meta.get("title"),
        )

    # -- Internals -----------------------------------------------------------
    def _try_download(
        self, url: str, progress: Optional[ProgressFn] = None
    ) -> DownloadResult:
        try:
            from yt_dlp import YoutubeDL  # type: ignore[import-not-found]
        except ImportError as exc:
            return DownloadResult(success=False, error=f"yt-dlp not installed: {exc}")

        outtmpl = os.path.join(self.outputs_dir, "%(id)s.%(ext)s")

        def _hook(info: Dict[str, Any]) -> None:
            status = info.get("status")
            if status == "downloading":
                downloaded = info.get("downloaded_bytes", 0) or 0
                total = info.get("total_bytes") or info.get("total_bytes_estimate") or 0
                frac = float(downloaded) / total if total else 0.0
                if progress:
                    progress(
                        f"Downloading: {downloaded // 1024} / "
                        f"{(total or 0) // 1024} KB",
                        max(0.0, min(1.0, frac)),
                    )
            elif status == "finished" and progress:
                progress("Post-processing ...", 1.0)

        opts: Dict[str, Any] = {
            "format": (
                f"bv*[height<={self.max_height}]+ba/b[height<={self.max_height}]"
                "/best[height<={h}]/best".format(h=self.max_height)
            ),
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "noprogress": True,
            "quiet": True,
            "noplaylist": True,
            "progress_hooks": [_hook],
            "concurrent_fragment_downloads": 4,
            "retries": 3,
            "fragment_retries": 3,
            "overwrites": True,
        }
        if self.ffmpeg_path:
            ffmpeg_dir = os.path.dirname(self.ffmpeg_path)
            opts["ffmpeg_location"] = ffmpeg_dir or self.ffmpeg_path

        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    return DownloadResult(success=False, error="yt-dlp returned no info")
                requested = info.get("requested_downloads") or []
                if requested:
                    final_path = requested[0].get("filepath") or requested[0].get(
                        "filename"
                    )
                else:
                    final_path = ydl.prepare_filename(info)
                    if final_path and not os.path.exists(final_path):
                        # When ffmpeg merge happened, the extension changes.
                        candidate = os.path.splitext(final_path)[0] + ".mp4"
                        if os.path.exists(candidate):
                            final_path = candidate
                if not final_path or not os.path.exists(final_path):
                    return DownloadResult(success=False, error="downloaded file missing")
                return DownloadResult(
                    success=True,
                    video_path=final_path,
                    title=info.get("title"),
                    duration=float(info.get("duration") or 0.0) or None,
                    metadata={
                        k: v
                        for k, v in info.items()
                        if k
                        in {"id", "title", "duration", "uploader", "channel", "webpage_url"}
                    },
                )
        except Exception as exc:  # noqa: BLE001 (yt-dlp raises many subclasses)
            return DownloadResult(success=False, error=str(exc))


def get_video_duration(path: str) -> Optional[float]:
    """Use ffprobe (if available) to get a video's duration in seconds."""
    ffprobe = cfg.get("ffprobe_path") or _which("ffprobe")
    ffmpeg = deps.get_ffmpeg_path()
    if ffprobe is None and ffmpeg:
        # Try ffprobe sibling next to ffmpeg
        sibling = os.path.join(os.path.dirname(ffmpeg), "ffprobe")
        if os.name == "nt":
            sibling += ".exe"
        if os.path.exists(sibling):
            ffprobe = sibling
    if not ffprobe:
        return None
    try:
        proc = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    out = proc.stdout.decode(errors="ignore").strip()
    try:
        return float(out)
    except ValueError:
        return None


def _which(name: str) -> Optional[str]:
    import shutil

    return shutil.which(name)
