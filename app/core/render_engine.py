"""Render engine.

Strategy (chosen for speed + flexibility on low-end PCs):

1. Decode mono PCM via ffmpeg -> compute spectrum bands per frame.
2. For each video frame:
     * Resolve background frame (image, video, gradient, or color).
     * Render visualizer onto an RGBA overlay (NumPy + Pillow).
     * Draw lyrics text onto the overlay (with optional karaoke highlight).
     * Composite the overlay onto the background frame.
3. Pipe RGB frames to ``ffmpeg -i pipe:0`` together with the original audio
   stream and encode to MP4 using the user-selected encoder (libx264 or
   hardware NVENC/QSV/AMF when available).

This keeps Python's per-frame workload light (one numpy + one Pillow paint
pass) while leaving the heavy work — encoding, scaling, audio mux — to
FFmpeg.
"""
from __future__ import annotations

import io
import math
import os
import platform
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import audio_reader, background_manager, logo_processor, lyrics_extractor, spectrum_engine
from .ffmpeg_manager import FFmpegStatus, _no_window_kwargs, detect_encoder, probe_ffmpeg


# Resolution presets (width, height)
RESOLUTIONS: dict[str, tuple[int, int]] = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4K": (3840, 2160),
}

QUALITY_CRF = {
    "Low": 28,
    "Medium": 23,
    "High": 20,
    "Best": 17,
}

QUALITY_HW_BITRATE = {
    "Low": "2500k",
    "Medium": "4500k",
    "High": "8000k",
    "Best": "14000k",
}

PRESETS = {
    "Fast 720p": {"resolution": "720p", "fps": 30, "quality": "Low", "fast": True},
    "Balanced 1080p": {"resolution": "1080p", "fps": 30, "quality": "Medium", "fast": False},
    "High Quality 1080p": {"resolution": "1080p", "fps": 60, "quality": "High", "fast": False},
    "Best Quality": {"resolution": "1080p", "fps": 60, "quality": "Best", "fast": False},
}


@dataclass
class RenderSettings:
    resolution: str = "1080p"
    custom_size: Optional[tuple[int, int]] = None
    fps: int = 30
    quality: str = "Medium"
    encoder: str = "auto"  # auto | libx264 | h264_nvenc | h264_qsv | h264_amf
    fast: bool = False

    @property
    def size(self) -> tuple[int, int]:
        if self.resolution == "Custom" and self.custom_size:
            return self.custom_size
        return RESOLUTIONS.get(self.resolution, RESOLUTIONS["1080p"])


@dataclass
class LyricsConfig:
    enabled: bool = True
    font_family: str = "Inter"
    font_path: str = ""
    font_size: int = 56
    color: str = "#FFFFFF"
    outline: bool = True
    outline_color: str = "#000000"
    outline_width: int = 3
    shadow: bool = True
    bold: bool = True
    italic: bool = False
    position: str = "center"  # top | center | bottom
    align: str = "center"  # left | center | right
    animation: str = "fade"  # none | fade | slide
    karaoke: bool = True
    highlight_color: str = "#FACC15"
    static_text: str = ""  # used if no synced lyrics and the user chose "static"


@dataclass
class RenderJob:
    audio_path: str
    output_path: str
    background: background_manager.BackgroundConfig
    spectrum: spectrum_engine.SpectrumConfig
    lyrics: LyricsConfig
    logo: logo_processor.LogoConfig
    render: RenderSettings
    lyrics_data: Optional[lyrics_extractor.LyricsData] = None
    background_override: Optional[str] = None  # used by batch mode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    return (*_hex_to_rgb(hex_color), alpha)


def _solid_image(size: tuple[int, int], color: str) -> Image.Image:
    return Image.new("RGB", size, _hex_to_rgb(color))


def _gradient_image(size: tuple[int, int], c1: str, c2: str) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (w, h))
    pix = img.load()
    a = np.array(_hex_to_rgb(c1), dtype=np.float32)
    b = np.array(_hex_to_rgb(c2), dtype=np.float32)
    for y in range(h):
        t = y / max(1, h - 1)
        row = (a + (b - a) * t).astype(np.uint8)
        for x in range(w):
            pix[x, y] = tuple(row.tolist())
    return img


def _fit_image(src: Image.Image, size: tuple[int, int], fit: str = "cover") -> Image.Image:
    tw, th = size
    sw, sh = src.size
    if fit == "stretch":
        return src.resize(size, Image.LANCZOS)
    src_ratio = sw / sh
    target_ratio = tw / th
    if (fit == "cover" and src_ratio > target_ratio) or (fit == "contain" and src_ratio < target_ratio):
        new_h = th
        new_w = int(new_h * src_ratio)
    else:
        new_w = tw
        new_h = int(new_w / src_ratio)
    resized = src.resize((max(1, new_w), max(1, new_h)), Image.LANCZOS)
    if fit == "contain":
        canvas = Image.new("RGB", size, (0, 0, 0))
        canvas.paste(resized, ((tw - new_w) // 2, (th - new_h) // 2))
        return canvas
    # cover -> center crop
    x = (resized.width - tw) // 2
    y = (resized.height - th) // 2
    return resized.crop((x, y, x + tw, y + th))


def _ken_burns(img: Image.Image, size: tuple[int, int], t: float, duration: float) -> Image.Image:
    """Subtle slow zoom + pan to make stills feel alive."""
    if duration <= 0:
        return _fit_image(img, size, "cover")
    progress = min(1.0, t / duration)
    zoom = 1.05 + 0.08 * progress  # zoom from 1.05x to 1.13x
    pan_x = (progress - 0.5) * 0.04  # subtle horizontal pan
    pan_y = (0.5 - progress) * 0.03  # gentle vertical drift

    tw, th = size
    src = _fit_image(img, (int(tw * zoom), int(th * zoom)), "cover")
    max_dx = (src.width - tw)
    max_dy = (src.height - th)
    cx = int(max_dx * (0.5 + pan_x))
    cy = int(max_dy * (0.5 + pan_y))
    cx = max(0, min(max_dx, cx))
    cy = max(0, min(max_dy, cy))
    return src.crop((cx, cy, cx + tw, cy + th))


# ---------------------------------------------------------------------------
# Lyrics drawing
# ---------------------------------------------------------------------------


_FALLBACK_SYSTEM_FONTS = (
    # Windows
    "segoeui.ttf",
    "arial.ttf",
    "tahoma.ttf",
    # macOS
    "Helvetica.ttc",
    "Arial Unicode.ttf",
    # Linux
    "DejaVuSans.ttf",
    "DejaVuSans-Bold.ttf",
    "LiberationSans-Regular.ttf",
    "NotoSans-Regular.ttf",
)


def _load_font(cfg: LyricsConfig) -> ImageFont.FreeTypeFont:
    """Pick the best available font.

    Order:
      1. Explicit user-supplied font file path.
      2. Bundled font matching the family name.
      3. System font matching the family name (Pillow searches platform paths).
      4. Common system fallback fonts (DejaVu / Segoe UI / Arial / Helvetica).
      5. ``ImageFont.load_default(size=…)`` so we never hard-fail.
    """
    size = cfg.font_size

    if cfg.font_path and Path(cfg.font_path).exists():
        try:
            return ImageFont.truetype(cfg.font_path, size)
        except OSError:
            pass

    fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    if fonts_dir.exists():
        for p in fonts_dir.glob("*.[ot]tf"):
            if cfg.font_family.lower() in p.stem.lower():
                try:
                    return ImageFont.truetype(str(p), size)
                except OSError:
                    continue

    if cfg.font_family:
        try:
            return ImageFont.truetype(cfg.font_family, size)
        except OSError:
            pass

    for name in _FALLBACK_SYSTEM_FONTS:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue

    # Pillow 10+ supports a size argument on load_default; older Pillow returns
    # a tiny bitmap font but at least never crashes.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _measure(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_text_with_effects(
    overlay: Image.Image,
    cfg: LyricsConfig,
    text: str,
    progress: float,
    fade: float,
) -> None:
    if not text or fade <= 0.01:
        return
    draw = ImageDraw.Draw(overlay)
    font = _load_font(cfg)
    tw, th = _measure(draw, text, font)
    W, H = overlay.size
    if cfg.align == "left":
        x = int(W * 0.08)
    elif cfg.align == "right":
        x = W - int(W * 0.08) - tw
    else:
        x = (W - tw) // 2
    if cfg.position == "top":
        y = int(H * 0.10)
    elif cfg.position == "bottom":
        y = H - int(H * 0.18) - th
    else:
        y = (H - th) // 2

    alpha = int(255 * max(0.0, min(1.0, fade)))
    color = _hex_to_rgba(cfg.color, alpha)
    outline_color = _hex_to_rgba(cfg.outline_color, alpha)
    shadow_color = (0, 0, 0, int(alpha * 0.55))

    if cfg.shadow:
        shadow_offset = max(2, cfg.outline_width)
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)

    if cfg.outline and cfg.outline_width > 0:
        try:
            draw.text(
                (x, y),
                text,
                font=font,
                fill=color,
                stroke_width=cfg.outline_width,
                stroke_fill=outline_color,
            )
        except TypeError:
            # Older Pillow without stroke
            draw.text((x, y), text, font=font, fill=color)
    else:
        draw.text((x, y), text, font=font, fill=color)

    # Karaoke highlight: paint progress chars in a different color.
    if cfg.karaoke and progress > 0 and progress < 1:
        char_count = max(1, len(text))
        highlighted_len = max(0, min(char_count, int(round(char_count * progress))))
        if highlighted_len > 0:
            highlighted = text[:highlighted_len]
            highlight_color = _hex_to_rgba(cfg.highlight_color, alpha)
            try:
                draw.text(
                    (x, y),
                    highlighted,
                    font=font,
                    fill=highlight_color,
                    stroke_width=cfg.outline_width,
                    stroke_fill=outline_color,
                )
            except TypeError:
                draw.text((x, y), highlighted, font=font, fill=highlight_color)


# ---------------------------------------------------------------------------
# Background frame sourcing
# ---------------------------------------------------------------------------


class _ImageCache:
    """Memoize loaded/resized backgrounds to keep low-end PCs responsive."""

    def __init__(self, max_items: int = 32):
        self._max = max_items
        self._cache: dict[tuple[str, int, int, str], Image.Image] = {}

    def get(self, path: str, size: tuple[int, int], fit: str = "cover") -> Image.Image:
        key = (path, size[0], size[1], fit)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        img = Image.open(path).convert("RGB")
        prepared = _fit_image(img, size, fit)
        if len(self._cache) >= self._max:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = prepared
        return prepared


class _VideoBackgroundReader:
    """Stream RGB24 frames from a video via FFmpeg, with looping."""

    def __init__(self, ffmpeg: str, path: str, size: tuple[int, int], fps: int):
        self.ffmpeg = ffmpeg
        self.path = path
        self.size = size
        self.fps = fps
        self.proc: Optional[subprocess.Popen] = None
        self.bytes_per_frame = size[0] * size[1] * 3
        self._open()

    def _open(self) -> None:
        self.close()
        cmd = [
            self.ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-stream_loop",
            "-1",
            "-i",
            self.path,
            "-an",
            "-vf",
            f"fps={self.fps},scale={self.size[0]}:{self.size[1]}:force_original_aspect_ratio=increase,"
            f"crop={self.size[0]}:{self.size[1]}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ]
        self.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            **_no_window_kwargs(),
        )

    def read(self) -> Image.Image:
        assert self.proc is not None and self.proc.stdout is not None
        data = self.proc.stdout.read(self.bytes_per_frame)
        if len(data) < self.bytes_per_frame:
            # Loop fallback: restart.
            self._open()
            assert self.proc.stdout is not None
            data = self.proc.stdout.read(self.bytes_per_frame)
        arr = np.frombuffer(data, dtype=np.uint8)
        if arr.size < self.bytes_per_frame:
            # Decoding failed silently — return black.
            return Image.new("RGB", self.size, (0, 0, 0))
        return Image.fromarray(arr.reshape(self.size[1], self.size[0], 3), "RGB")

    def close(self) -> None:
        if self.proc is not None:
            try:
                self.proc.kill()
            except OSError:
                pass
            self.proc = None


# ---------------------------------------------------------------------------
# Encoder selection
# ---------------------------------------------------------------------------


def _resolve_encoder(settings: RenderSettings, status: FFmpegStatus) -> str:
    if settings.encoder and settings.encoder != "auto":
        return settings.encoder
    return detect_encoder(status, "h264")


def _ffmpeg_encoder_args(encoder: str, settings: RenderSettings) -> list[str]:
    quality = settings.quality
    if encoder == "libx264":
        crf = QUALITY_CRF.get(quality, 23)
        preset = "veryfast" if settings.fast else "medium"
        return [
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
        ]
    bitrate = QUALITY_HW_BITRATE.get(quality, "4500k")
    if encoder in ("h264_nvenc", "hevc_nvenc"):
        return [
            "-c:v",
            encoder,
            "-preset",
            "p4",
            "-rc",
            "vbr",
            "-cq",
            "23",
            "-b:v",
            bitrate,
            "-pix_fmt",
            "yuv420p",
        ]
    if encoder in ("h264_qsv", "hevc_qsv"):
        return [
            "-c:v",
            encoder,
            "-global_quality",
            "23",
            "-b:v",
            bitrate,
            "-pix_fmt",
            "nv12",
        ]
    if encoder in ("h264_amf", "hevc_amf"):
        return [
            "-c:v",
            encoder,
            "-quality",
            "balanced",
            "-rc",
            "vbr_peak",
            "-b:v",
            bitrate,
            "-pix_fmt",
            "yuv420p",
        ]
    # Fallback
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass
class RenderProgress:
    frame: int
    total: int
    elapsed: float
    eta: float
    fps: float
    message: str = ""

    @property
    def fraction(self) -> float:
        return self.frame / max(1, self.total)


ProgressCallback = Callable[[RenderProgress], None]
LogCallback = Callable[[str], None]


def estimate_duration(job: RenderJob, status: Optional[FFmpegStatus] = None) -> float:
    """Rough render-time estimate in seconds for the user UI."""
    status = status or probe_ffmpeg()
    info = audio_reader.probe(job.audio_path, status.ffprobe_path)
    if info.duration <= 0:
        return 0.0
    w, h = job.render.size
    pixels = w * h
    # Heuristic factor — pretty conservative for potato laptops.
    base = info.duration * (pixels / (1920 * 1080)) * 0.6
    if job.background.type == "video" or job.background.multi_enabled:
        base *= 1.25
    if job.spectrum.style in ("Particle Spectrum", "Radial Pulse"):
        base *= 1.1
    if status.has_nvenc or status.has_qsv or status.has_amf:
        base *= 0.55
    return float(base)


def render_preview_frame(job: RenderJob, t: float = 5.0, max_size: int = 480) -> Image.Image:
    """Render a single still preview frame at a lower resolution."""
    status = probe_ffmpeg()
    w, h = job.render.size
    scale = min(1.0, max_size / max(w, h))
    size = (max(160, int(w * scale)), max(90, int(h * scale)))
    preview_render = RenderSettings(
        resolution="Custom",
        custom_size=size,
        fps=job.render.fps,
        quality=job.render.quality,
        encoder=job.render.encoder,
        fast=True,
    )

    # Compute a tiny slice of spectrum around t.
    samples = audio_reader.decode_pcm(
        job.audio_path, sample_rate=22050, channels=1, ffmpeg_path=status.ffmpeg_path
    )
    spectrum = spectrum_engine.compute_frames(
        samples,
        sample_rate=22050,
        fps=preview_render.fps,
        bars=job.spectrum.bars,
        bass_boost=job.spectrum.bass_boost,
        sensitivity=job.spectrum.sensitivity,
        smoothness=job.spectrum.smoothness,
    )
    frame_index = max(0, min(len(spectrum) - 1, int(t * preview_render.fps)))

    duration = audio_reader.probe(job.audio_path, status.ffprobe_path).duration
    schedule = background_manager.schedule_for(job.background, duration or 60.0, seed=42)
    bg_img = _compose_background_frame(
        job.background,
        schedule,
        t=t,
        size=size,
        ffmpeg=status.ffmpeg_path,
        cache=_ImageCache(),
        video_readers={},
    )

    overlay = spectrum_engine.render(
        job.spectrum, spectrum, frame_index, size
    )
    bg_img = bg_img.convert("RGBA")
    bg_img.alpha_composite(overlay)

    if job.lyrics.enabled:
        line = None
        progress = 0.0
        if job.lyrics_data and job.lyrics_data.synced:
            line = lyrics_extractor.active_line_at(job.lyrics_data, t)
            if line is not None:
                # Estimate the next line's start time for word progress.
                next_t = duration
                for l in job.lyrics_data.lines:
                    if l.time is not None and l.time > line.time:
                        next_t = l.time
                        break
                progress = lyrics_extractor.progress_through_words(line, t, next_t)
        elif job.lyrics_data and job.lyrics_data.lines:
            line = job.lyrics_data.lines[0]
        if line is not None and (line.time is None or t >= line.time):
            _draw_text_with_effects(bg_img, job.lyrics, line.text, progress, 1.0)
        elif job.lyrics.static_text:
            _draw_text_with_effects(bg_img, job.lyrics, job.lyrics.static_text, 0.0, 1.0)

    prepared_logo = logo_processor.prepare(job.logo, size)
    logo_processor.paste(bg_img, job.logo, prepared_logo)

    return bg_img.convert("RGB")


def _compose_background_frame(
    cfg: background_manager.BackgroundConfig,
    schedule: background_manager.Schedule,
    t: float,
    size: tuple[int, int],
    ffmpeg: str,
    cache: _ImageCache,
    video_readers: dict[str, _VideoBackgroundReader],
    fps: int = 30,
) -> Image.Image:
    """Return a fully-composed (with ken-burns + fade) RGB background frame."""
    clip = schedule.at(t)
    if clip is None or clip.path is None:
        # Solid or gradient.
        if cfg.type == "gradient":
            return _gradient_image(size, cfg.color, cfg.color2)
        return _solid_image(size, cfg.color)

    if clip.is_video:
        reader = video_readers.get(clip.path)
        if reader is None:
            reader = _VideoBackgroundReader(ffmpeg, clip.path, size, fps)
            video_readers[clip.path] = reader
        frame = reader.read()
    else:
        try:
            base = cache.get(clip.path, size, cfg.fit)
        except Exception:
            return _gradient_image(size, cfg.color, cfg.color2)
        if cfg.ken_burns:
            duration = max(1.0, clip.end - clip.start)
            frame = _ken_burns(base, size, t - clip.start, duration)
        else:
            frame = base

    # Fade in/out for transition between clips.
    if cfg.transition == "fade" and clip.end - clip.start > 0.6:
        local_t = t - clip.start
        seg_dur = clip.end - clip.start
        fade_dur = min(0.6, seg_dur / 4.0)
        if local_t < fade_dur:
            alpha = local_t / fade_dur
            frame = Image.blend(_solid_image(size, "#000000"), frame, alpha)
        elif local_t > seg_dur - fade_dur:
            alpha = max(0.0, (seg_dur - local_t) / fade_dur)
            frame = Image.blend(_solid_image(size, "#000000"), frame, alpha)
    return frame


def _next_line_start(data: lyrics_extractor.LyricsData, current: lyrics_extractor.LyricLine, duration: float) -> float:
    for line in data.lines:
        if line.time is not None and current.time is not None and line.time > current.time:
            return line.time
    return duration


def render_video(
    job: RenderJob,
    on_progress: Optional[ProgressCallback] = None,
    on_log: Optional[LogCallback] = None,
    cancel_event: Optional[threading.Event] = None,
) -> str:
    """Render a single song to ``job.output_path`` and return the path."""
    on_progress = on_progress or (lambda *_: None)
    on_log = on_log or (lambda *_: None)
    cancel_event = cancel_event or threading.Event()

    status = probe_ffmpeg()
    if not status.found:
        raise RuntimeError("FFmpeg is not configured. Install or set the path first.")

    info = audio_reader.probe(job.audio_path, status.ffprobe_path)
    if info.duration <= 0:
        raise RuntimeError(f"Could not read duration of {job.audio_path}")

    on_log(f"[render] {info.filename} | {info.duration:.2f}s | {info.sample_rate}Hz")

    fps = max(12, min(60, job.render.fps))
    size = job.render.size
    total_frames = int(math.ceil(info.duration * fps))

    on_log(f"[render] target {size[0]}x{size[1]} @ {fps}fps -> {total_frames} frames")

    # Decode mono PCM for spectrum (lower sample rate to keep it light).
    on_log("[render] decoding audio for spectrum analysis…")
    samples = audio_reader.decode_pcm(
        job.audio_path,
        sample_rate=22050,
        channels=1,
        ffmpeg_path=status.ffmpeg_path,
    )

    on_log("[render] computing spectrum frames…")
    spectrum = spectrum_engine.compute_frames(
        samples,
        sample_rate=22050,
        fps=fps,
        bars=job.spectrum.bars,
        bass_boost=job.spectrum.bass_boost,
        sensitivity=job.spectrum.sensitivity,
        smoothness=job.spectrum.smoothness,
    )

    # Background scheduling (apply override if batch chose a specific file).
    bg_cfg = job.background
    if job.background_override:
        bg_cfg = background_manager.BackgroundConfig(**{**bg_cfg.__dict__})
        bg_cfg.path = job.background_override
        if background_manager.is_video(job.background_override):
            bg_cfg.type = "video"
        else:
            bg_cfg.type = "image"
        bg_cfg.multi_enabled = False

    schedule = background_manager.schedule_for(bg_cfg, info.duration, seed=hash(job.audio_path) & 0xFFFFFFFF)
    on_log(f"[render] background schedule -> {len(schedule.clips)} clip(s)")

    encoder = _resolve_encoder(job.render, status)
    on_log(f"[render] encoder: {encoder}")

    Path(job.output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        status.ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        # Raw video pipe.
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{size[0]}x{size[1]}",
        "-r",
        str(fps),
        "-i",
        "-",
        # Audio input from original file.
        "-i",
        job.audio_path,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        *_ffmpeg_encoder_args(encoder, job.render),
        "-movflags",
        "+faststart",
        job.output_path,
    ]
    on_log(f"[render] ffmpeg: {' '.join(shlex.quote(c) for c in cmd)}")
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        **_no_window_kwargs(),
    )

    # Read stderr in a worker so we surface errors as they happen.
    stderr_lines: list[str] = []

    def _drain_stderr() -> None:
        assert proc.stderr is not None
        for line in proc.stderr:
            try:
                text = line.decode("utf-8", errors="replace").rstrip()
            except Exception:
                text = "(undecodable stderr)"
            if text:
                stderr_lines.append(text)
                on_log(f"[ffmpeg] {text}")

    drainer = threading.Thread(target=_drain_stderr, daemon=True)
    drainer.start()

    cache = _ImageCache()
    video_readers: dict[str, _VideoBackgroundReader] = {}
    prepared_logo = logo_processor.prepare(job.logo, size)
    start_time = time.monotonic()

    lyrics_data = job.lyrics_data
    if lyrics_data is None and job.lyrics.enabled:
        lyrics_data = lyrics_extractor.extract(job.audio_path)
        job.lyrics_data = lyrics_data

    try:
        for frame_index in range(total_frames):
            if cancel_event.is_set():
                on_log("[render] cancelled by user")
                break

            t = frame_index / fps
            # ---- Background ------------------------------------------------
            frame = _compose_background_frame(
                bg_cfg,
                schedule,
                t,
                size,
                status.ffmpeg_path,
                cache,
                video_readers,
                fps=fps,
            ).convert("RGBA")

            # ---- Visualizer ------------------------------------------------
            overlay = spectrum_engine.render(job.spectrum, spectrum, frame_index, size)
            frame.alpha_composite(overlay)

            # ---- Lyrics ----------------------------------------------------
            if job.lyrics.enabled and lyrics_data is not None and lyrics_data.lines:
                if lyrics_data.synced:
                    line = lyrics_extractor.active_line_at(lyrics_data, t)
                    if line is not None and line.time is not None:
                        line_end = _next_line_start(lyrics_data, line, info.duration)
                        progress = lyrics_extractor.progress_through_words(line, t, line_end)
                        # Fade: 0.25s in, 0.4s out before the next line.
                        fade_in = 0.25
                        fade_out = 0.4
                        local = t - line.time
                        if local < fade_in:
                            fade = local / fade_in
                        elif t > line_end - fade_out:
                            fade = max(0.0, (line_end - t) / fade_out)
                        else:
                            fade = 1.0
                        if line.time <= t:
                            _draw_text_with_effects(
                                frame, job.lyrics, line.text, progress, fade
                            )
                else:
                    # Unsynced: show all lines together as a static block, OR
                    # fall back to caller-provided static_text if there are
                    # no lines (the GUI sets this when the user picks "Use
                    # static lyric text").
                    text = lyrics_data.lines[0].text if lyrics_data.lines else job.lyrics.static_text
                    if text:
                        _draw_text_with_effects(frame, job.lyrics, text, 0.0, 1.0)
            elif job.lyrics.enabled and job.lyrics.static_text:
                _draw_text_with_effects(frame, job.lyrics, job.lyrics.static_text, 0.0, 1.0)

            # ---- Logo ------------------------------------------------------
            logo_processor.paste(frame, job.logo, prepared_logo)

            # ---- Pipe to FFmpeg -------------------------------------------
            assert proc.stdin is not None
            try:
                proc.stdin.write(frame.convert("RGB").tobytes())
            except BrokenPipeError:
                break

            if frame_index % max(1, fps // 2) == 0 or frame_index == total_frames - 1:
                elapsed = time.monotonic() - start_time
                render_fps = (frame_index + 1) / max(elapsed, 1e-3)
                eta = (total_frames - frame_index - 1) / max(render_fps, 1e-3)
                on_progress(
                    RenderProgress(
                        frame=frame_index + 1,
                        total=total_frames,
                        elapsed=elapsed,
                        eta=eta,
                        fps=render_fps,
                        message=f"frame {frame_index + 1}/{total_frames}",
                    )
                )
    finally:
        if proc.stdin is not None:
            try:
                proc.stdin.close()
            except OSError:
                pass
        for reader in video_readers.values():
            reader.close()
        try:
            proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            proc.kill()
        drainer.join(timeout=1.5)

    if cancel_event.is_set():
        try:
            Path(job.output_path).unlink(missing_ok=True)
        except OSError:
            pass
        raise RuntimeError("Render cancelled")

    if proc.returncode != 0:
        message = "\n".join(stderr_lines[-15:])
        raise RuntimeError(f"FFmpeg exited with {proc.returncode}: {message}")

    elapsed = time.monotonic() - start_time
    on_log(f"[render] done in {elapsed:.1f}s -> {job.output_path}")
    return job.output_path


__all__ = [
    "RenderJob",
    "RenderSettings",
    "LyricsConfig",
    "RenderProgress",
    "RESOLUTIONS",
    "PRESETS",
    "QUALITY_CRF",
    "estimate_duration",
    "render_preview_frame",
    "render_video",
]
