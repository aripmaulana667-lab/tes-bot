"""FFmpeg-based clip exporter (cut + crop + scale + burn subtitles)."""
from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

from ..utils import config as cfg
from ..utils.logger import get_logger
from . import dependency_manager as deps
from . import export_presets as presets
from .clip_generator import Clip
from .subtitle_renderer import (
    SubtitleStyle,
    render_clip_subtitles,
)

_LOG = get_logger("exporter")

ProgressFn = Callable[[str, float], None]


@dataclass
class ExportSettings:
    platform: str = "tiktok"
    aspect_ratio: str = "9:16"
    resolution: str = "1080x1920"  # 'WIDTHxHEIGHT'
    fps: str = "original"
    crop_mode: str = "center"  # see export_presets.CROP_MODES
    quality: str = "high"
    codec: str = "h264"
    burn_subtitles: bool = True
    manual_crop_x: float = 0.5  # fraction (0..1) for manual crop center
    manual_crop_y: float = 0.5
    custom_video_bitrate: Optional[int] = None  # kbps override


@dataclass
class ExportResult:
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None
    command: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------
def _filter_chain(
    *,
    target_w: int,
    target_h: int,
    crop_mode: str,
    manual_x: float,
    manual_y: float,
    subtitle_path: Optional[str],
) -> str:
    """Build the FFmpeg ``-filter_complex`` chain for cropping + subtitles."""
    crop_mode = crop_mode.lower()
    target_ar = target_w / target_h

    if crop_mode == "blurred-background":
        # Two streams: background blurred, foreground letterboxed.
        # FFmpeg syntax: split video into [bg][fg], scale each, overlay.
        chain = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h},gblur=sigma=24[bgblur];"
            f"[fg]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease[fgscaled];"
            f"[bgblur][fgscaled]overlay=(W-w)/2:(H-h)/2[outv]"
        )
    elif crop_mode == "manual":
        manual_x = max(0.0, min(1.0, float(manual_x)))
        manual_y = max(0.0, min(1.0, float(manual_y)))
        chain = (
            f"[0:v]scale=if(gt(a\\,{target_ar:.6f})\\,-2\\,{target_w}):"
            f"if(gt(a\\,{target_ar:.6f})\\,{target_h}\\,-2),"
            f"crop={target_w}:{target_h}:"
            f"x=max(0\\,min(iw-{target_w}\\,iw*{manual_x:.4f}-{target_w}/2)):"
            f"y=max(0\\,min(ih-{target_h}\\,ih*{manual_y:.4f}-{target_h}/2))[outv]"
        )
    else:
        # 'center' and 'auto-face' currently both fall back to a center crop.
        # If face detection fails or is unavailable, we honor the spec by
        # gracefully degrading to center.  ``auto-face`` is wired to the same
        # filter so the export still works.
        chain = (
            f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2[outv]"
        )

    if subtitle_path:
        ass_arg = subtitle_path.replace("\\", "/").replace(":", "\\:")
        chain += f";[outv]ass='{ass_arg}'[outv]"
    return chain


def _quality_options(
    quality: presets.QualityPreset,
    width: int,
    height: int,
    codec_info: Dict[str, str],
    custom_video_bitrate: Optional[int],
) -> List[str]:
    bitrate = custom_video_bitrate or presets.auto_video_bitrate(width, height)
    audio_bitrate = quality.audio_bitrate_kbps
    args: List[str] = [
        "-c:v",
        codec_info["video_codec"],
        "-preset",
        quality.preset,
        "-crf",
        str(quality.crf),
        "-pix_fmt",
        codec_info["pix_fmt"],
        "-b:v",
        f"{bitrate}k",
        "-maxrate",
        f"{int(bitrate * 1.4)}k",
        "-bufsize",
        f"{bitrate * 2}k",
        "-c:a",
        "aac",
        "-b:a",
        f"{audio_bitrate}k",
        "-movflags",
        "+faststart",
    ]
    return args


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def export_clip(
    *,
    source_video: str,
    clip: Clip,
    settings: ExportSettings,
    project_id: int = 0,
    output_dir: Optional[str] = None,
    subtitle_style: Optional[SubtitleStyle] = None,
    progress: Optional[ProgressFn] = None,
) -> ExportResult:
    ffmpeg = deps.get_ffmpeg_path()
    if not ffmpeg:
        return ExportResult(success=False, error="FFmpeg tidak ditemukan. Install dulu via Dependency Status.")
    if not os.path.exists(source_video):
        return ExportResult(success=False, error=f"Source video missing: {source_video}")

    width, height = presets.parse_resolution(settings.resolution)
    codec_info = presets.get_codec(settings.codec)
    quality_preset = presets.get_quality(settings.quality)
    out_dir = output_dir or cfg.get_outputs_dir()
    os.makedirs(out_dir, exist_ok=True)
    filename = presets.filename_for_clip(
        project_id=project_id,
        clip_index=clip.index,
        platform=settings.platform,
        resolution=settings.resolution,
    )
    output_path = os.path.join(out_dir, filename)

    subtitle_path: Optional[str] = None
    if settings.burn_subtitles:
        subtitle_path = render_clip_subtitles(
            clip,
            style=subtitle_style,
            video_width=width,
            video_height=height,
        )

    fchain = _filter_chain(
        target_w=width,
        target_h=height,
        crop_mode=settings.crop_mode,
        manual_x=settings.manual_crop_x,
        manual_y=settings.manual_crop_y,
        subtitle_path=subtitle_path,
    )

    duration = max(0.1, clip.end - clip.start)

    cmd: List[str] = [
        ffmpeg,
        "-y",
        "-ss",
        f"{clip.start:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        source_video,
        "-filter_complex",
        fchain,
        "-map",
        "[outv]",
        "-map",
        "0:a?",
    ]
    if settings.fps not in (None, "original", "auto"):
        cmd.extend(["-r", str(settings.fps)])
    cmd.extend(
        _quality_options(
            quality_preset,
            width=width,
            height=height,
            codec_info=codec_info,
            custom_video_bitrate=settings.custom_video_bitrate,
        )
    )
    cmd.append(output_path)

    if progress:
        progress(f"Exporting clip {clip.index + 1} ...", 0.05)
    _LOG.info("FFmpeg export: %s", " ".join(shlex.quote(p) for p in cmd))

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        return ExportResult(success=False, error=f"FFmpeg not found: {exc}", command=cmd)
    except OSError as exc:
        return ExportResult(success=False, error=f"OS error: {exc}", command=cmd)

    if proc.returncode != 0:
        err = proc.stderr.decode(errors="ignore")[-1200:]
        _LOG.error("FFmpeg export failed: %s", err)
        return ExportResult(success=False, error=err, command=cmd)

    if progress:
        progress(f"Saved clip {clip.index + 1}: {os.path.basename(output_path)}", 1.0)
    return ExportResult(success=True, output_path=output_path, command=cmd)


def export_clips(
    *,
    source_video: str,
    clips: Sequence[Clip],
    settings: ExportSettings,
    project_id: int = 0,
    output_dir: Optional[str] = None,
    subtitle_style: Optional[SubtitleStyle] = None,
    progress: Optional[ProgressFn] = None,
) -> List[ExportResult]:
    results: List[ExportResult] = []
    total = max(1, len(clips))
    for idx, clip in enumerate(clips):
        if progress:
            progress(f"Exporting clip {idx + 1}/{total} ...", idx / total)
        result = export_clip(
            source_video=source_video,
            clip=clip,
            settings=settings,
            project_id=project_id,
            output_dir=output_dir,
            subtitle_style=subtitle_style,
            progress=progress,
        )
        results.append(result)
    if progress:
        progress("All clips exported." if all(r.success for r in results) else "Done with errors.", 1.0)
    return results
