"""Core FFmpeg render orchestration for preview, full, and batch jobs."""
from __future__ import annotations

import asyncio
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple

from ..config import (
    BACKGROUNDS_DIR,
    LOGOS_DIR,
    LYRICS_DIR,
    MUSIC_DIR,
    OUTPUTS_DIR,
    TEMP_DIR,
)
from ..models.render import (
    BackgroundConfig,
    LogoConfig,
    RenderRequest,
    SpectrumConfig,
)
from . import ffmpeg as ffsvc
from .jobs import Job, store
from .lrc import ass_escape_path, load_lrc_file, lyrics_to_ass
from .spectrum import build_spectrum_chain


_OUT_TIME_RE = re.compile(r"out_time_ms=(\d+)")
_PROGRESS_RE = re.compile(r"out_time=(\d+):(\d+):([0-9.]+)")


def _parse_resolution(res: str) -> Tuple[int, int]:
    w, h = res.split("x")
    return int(w), int(h)


def _ensure_path(base: Path, name: str) -> Path:
    p = base / name
    if not p.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {p}")
    return p


def _safe_output_name(base_name: str, suffix: str) -> Path:
    stem = Path(base_name).stem or f"render-{int(time.time())}"
    cleaned = re.sub(r"[^A-Za-z0-9_\-]+", "_", stem)
    return OUTPUTS_DIR / f"{cleaned}{suffix}.mp4"


def _logo_position(width: int, height: int, cfg: LogoConfig) -> Tuple[str, str]:
    m = cfg.margin
    s = cfg.size
    mapping = {
        "top_left": (f"{m}", f"{m}"),
        "top_right": (f"main_w-{s}-{m}", f"{m}"),
        "bottom_left": (f"{m}", f"main_h-{s}-{m}"),
        "bottom_right": (f"main_w-{s}-{m}", f"main_h-{s}-{m}"),
        "top_center": (f"(main_w-{s})/2", f"{m}"),
    }
    return mapping.get(cfg.position, mapping["top_right"])


def _build_background_input(
    background: BackgroundConfig,
    width: int,
    height: int,
    duration: float,
    fps: int,
) -> Tuple[List[str], str]:
    """Return ffmpeg input args and the label of the prepared background stream."""
    files: List[Path] = []
    for name in background.files:
        p = BACKGROUNDS_DIR / name
        if p.exists():
            files.append(p)
    args: List[str] = []
    if not files:
        # Solid black background
        args = ["-f", "lavfi", "-t", f"{duration:.3f}", "-i", f"color=c=black:s={width}x{height}:r={fps}"]
        return args, "[1:v]"

    if background.mode == "single" or len(files) == 1:
        f = files[0]
        is_image = f.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        if is_image:
            args = [
                "-loop",
                "1",
                "-t",
                f"{duration:.3f}",
                "-framerate",
                str(fps),
                "-i",
                str(f),
            ]
        else:
            args = ["-stream_loop", "-1", "-t", f"{duration:.3f}", "-i", str(f)]
        return args, "[1:v]"

    # Slideshow: chain multiple images. For simplicity we cycle by image loop with duration.
    if background.randomize:
        import random

        files = files.copy()
        random.shuffle(files)
    args = []
    for f in files:
        is_image = f.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        per = max(0.5, background.slideshow_duration)
        if is_image:
            args += ["-loop", "1", "-t", f"{per:.3f}", "-framerate", str(fps), "-i", str(f)]
        else:
            args += ["-stream_loop", "-1", "-t", f"{per:.3f}", "-i", str(f)]
    return args, "__SLIDESHOW__"


def _build_filtergraph(
    *,
    width: int,
    height: int,
    duration: float,
    fps: int,
    background: BackgroundConfig,
    spectrum: SpectrumConfig,
    lyrics_ass_path: Optional[Path],
    logo: LogoConfig,
    logo_input_index: Optional[int],
    bg_indices: List[int],
    bg_label_token: str,
) -> str:
    """Compose the full filter_complex pipeline."""
    parts: List[str] = []

    if bg_label_token == "[1:v]":
        bg_chain = (
            f"[{bg_indices[0]}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1,fps={fps}"
        )
        if background.blur > 0:
            bg_chain += f",boxblur={background.blur}:1"
        if background.dark_overlay > 0:
            opacity = max(0.0, min(1.0, background.dark_overlay))
            bg_chain += (
                f",drawbox=x=0:y=0:w={width}:h={height}:color=black@{opacity:.3f}:t=fill"
            )
        bg_chain += "[bg]"
        parts.append(bg_chain)
    else:
        concat_inputs = []
        for i, idx in enumerate(bg_indices):
            concat_inputs.append(
                f"[{idx}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},setsar=1,fps={fps}[bgp{i}]"
            )
        parts.extend(concat_inputs)
        concat_chain = "".join(f"[bgp{i}]" for i in range(len(bg_indices)))
        concat_chain += f"concat=n={len(bg_indices)}:v=1:a=0,loop=loop=-1:size=1:start=0,trim=duration={duration:.3f}"
        if background.blur > 0:
            concat_chain += f",boxblur={background.blur}:1"
        if background.dark_overlay > 0:
            opacity = max(0.0, min(1.0, background.dark_overlay))
            concat_chain += (
                f",drawbox=x=0:y=0:w={width}:h={height}:color=black@{opacity:.3f}:t=fill"
            )
        concat_chain += "[bg]"
        parts.append(concat_chain)

    spec_chain = build_spectrum_chain((width, max(60, min(spectrum.height, height // 2))), spectrum)
    parts.append(spec_chain)

    spectrum_h = max(60, min(spectrum.height, height // 2))
    parts.append(f"[bg][spec]overlay=0:{height - spectrum_h}:format=auto[bgs]")

    last_label = "[bgs]"

    if lyrics_ass_path is not None:
        escaped = ass_escape_path(str(lyrics_ass_path))
        parts.append(f"{last_label}subtitles='{escaped}'[bsl]")
        last_label = "[bsl]"

    if logo.file and logo_input_index is not None:
        x_expr, y_expr = _logo_position(width, height, logo)
        logo_chain = (
            f"[{logo_input_index}:v]scale={logo.size}:{logo.size}:force_original_aspect_ratio=decrease,"
            f"pad={logo.size}:{logo.size}:(ow-iw)/2:(oh-ih)/2:color=0x00000000"
        )
        if logo.circle:
            radius = logo.size // 2
            logo_chain += (
                f",format=rgba,geq=lum='p(X,Y)':a='if(lte(hypot(X-{radius},Y-{radius}),{radius}),alpha(X,Y),0)'"
            )
        logo_chain += f",format=rgba,colorchannelmixer=aa={logo.opacity:.3f}[lg]"
        parts.append(logo_chain)
        parts.append(f"{last_label}[lg]overlay={x_expr}:{y_expr}:format=auto[final]")
        last_label = "[final]"

    parts.append(f"{last_label}format=yuv420p[v]")
    return ";".join(parts)


async def _read_progress(job: Job, proc: asyncio.subprocess.Process, total_duration: float) -> None:
    if proc.stdout is None:
        return
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        decoded = line.decode("utf-8", errors="ignore").strip()
        if not decoded:
            continue
        if decoded.startswith("out_time_ms="):
            try:
                out_ms = int(decoded.split("=", 1)[1])
                if total_duration > 0:
                    pct = out_ms / 1_000_000 / total_duration
                    await store.update(job, progress=pct, message=f"Render {pct*100:.1f}%")
            except Exception:
                pass
        elif decoded == "progress=end":
            await store.update(job, progress=1.0, message="Finalisasi ...")


async def _read_stderr(job: Job, proc: asyncio.subprocess.Process) -> None:
    if proc.stderr is None:
        return
    while True:
        line = await proc.stderr.readline()
        if not line:
            break
        decoded = line.decode("utf-8", errors="ignore").rstrip()
        if not decoded:
            continue
        await store.update(job, log_line=decoded)


async def render_job(
    job: Job,
    request: RenderRequest,
    *,
    preview: bool = False,
) -> Path:
    ffmpeg_path, _ = ffsvc.find_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg tidak ditemukan. Install FFmpeg portable terlebih dulu.")

    music_path = _ensure_path(MUSIC_DIR, request.music_file)
    await store.update(job, status="rendering", message="Menyiapkan render ...", music_file=str(music_path.name))

    duration = await ffsvc.probe_duration(str(music_path))
    if duration <= 0:
        duration = 60.0
    target_duration = float(request.preview_seconds) if preview else duration
    target_duration = max(1.0, target_duration)
    await store.update(job, duration=target_duration)

    width, height = _parse_resolution(request.render.resolution)
    fps = int(request.render.fps)

    bg_args, bg_label_token = _build_background_input(
        request.background, width, height, target_duration, fps
    )

    lyrics_ass: Optional[Path] = None
    if request.lyrics.file:
        try:
            lrc_path = _ensure_path(LYRICS_DIR, request.lyrics.file)
            lines = load_lrc_file(lrc_path, offset_ms=request.lyrics.offset_ms)
            if lines:
                ass_text = lyrics_to_ass(lines, request.lyrics, (width, height), target_duration)
                lyrics_ass = TEMP_DIR / f"lyrics-{job.id}.ass"
                lyrics_ass.write_text(ass_text, encoding="utf-8")
        except FileNotFoundError as exc:
            await store.update(job, log_line=f"Peringatan: {exc}")

    logo_path: Optional[Path] = None
    if request.logo.file:
        try:
            logo_path = _ensure_path(LOGOS_DIR, request.logo.file)
        except FileNotFoundError as exc:
            await store.update(job, log_line=f"Peringatan logo: {exc}")

    args: List[str] = [ffmpeg_path, "-hide_banner", "-y"]
    args += ["-i", str(music_path)]

    bg_start_index = 1
    bg_indices: List[int] = []
    if bg_args:
        # Each bg input adds one stream — count by scanning args:
        i = 0
        idx = bg_start_index
        while i < len(bg_args):
            if bg_args[i] == "-i":
                bg_indices.append(idx)
                idx += 1
                i += 2
            else:
                i += 1
        args += bg_args

    logo_input_index: Optional[int] = None
    if logo_path is not None:
        logo_input_index = (bg_indices[-1] + 1) if bg_indices else bg_start_index
        args += ["-loop", "1", "-t", f"{target_duration:.3f}", "-i", str(logo_path)]

    filtergraph = _build_filtergraph(
        width=width,
        height=height,
        duration=target_duration,
        fps=fps,
        background=request.background,
        spectrum=request.spectrum,
        lyrics_ass_path=lyrics_ass,
        logo=request.logo,
        logo_input_index=logo_input_index,
        bg_indices=bg_indices,
        bg_label_token=bg_label_token if bg_label_token == "[1:v]" else "__SLIDESHOW__",
    )

    if preview:
        args += ["-t", f"{target_duration:.3f}"]

    out_suffix = "-preview" if preview else ""
    output_name = request.output_name or music_path.stem
    out_path = _safe_output_name(output_name, out_suffix)

    args += [
        "-filter_complex",
        filtergraph,
        "-map",
        "[v]",
        "-map",
        "0:a",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        request.render.preset,
        "-crf",
        str(request.render.crf),
        "-r",
        str(fps),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-progress",
        "pipe:1",
        "-nostats",
        str(out_path),
    ]

    await store.update(job, log_line="$ " + " ".join(args))

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    job.process = proc

    progress_task = asyncio.create_task(_read_progress(job, proc, target_duration))
    stderr_task = asyncio.create_task(_read_stderr(job, proc))

    try:
        rc = await proc.wait()
    finally:
        await progress_task
        await stderr_task

    if job.cancel_event.is_set():
        await store.update(job, status="cancelled", message="Dibatalkan oleh pengguna.")
        try:
            if out_path.exists():
                out_path.unlink()
        except Exception:
            pass
        raise asyncio.CancelledError()

    if rc != 0:
        raise RuntimeError(f"FFmpeg keluar dengan kode {rc}. Cek log untuk detail.")

    if lyrics_ass is not None:
        try:
            lyrics_ass.unlink()
        except Exception:
            pass

    await store.update(
        job,
        status="done",
        progress=1.0,
        message="Selesai.",
        output_file=out_path.name,
    )
    return out_path
