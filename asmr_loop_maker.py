"""ASMR Seamless Loop Maker.

Core engine for finding the best loop points in a short video and producing a
long, seamless ASMR loop with crossfaded video and audio.

Pipeline overview
-----------------
1. ``read_video_frames``        – decode every frame of the source clip.
2. ``frame_signature``          – build a compact signature (small grayscale
                                  thumbnail + colour histogram) for each frame.
3. ``compare_signatures``       – score how similar two frames are.
4. ``find_best_loop_points``    – search candidate (start, end) frame pairs to
                                  find the smoothest loop given a minimum
                                  segment length.
5. ``make_looped_video``        – stitch the chosen segment back-to-back with
                                  a visual crossfade until the requested output
                                  duration is reached.
6. ``extract_audio``            – pull the audio of the loop segment as WAV
                                  using FFmpeg.
7. ``make_looped_audio``        – loop and crossfade the audio with soundfile.
8. ``mux_video_audio``          – combine the looped silent video with the
                                  looped audio into a final H.264/AAC MP4.
9. ``process_video``            – glue function that runs the full pipeline
                                  for one file.

The module can also be run as a script for single-file or batch processing::

    python asmr_loop_maker.py input.mp4 --output output.mp4 --hours 1
    python asmr_loop_maker.py --batch-dir ./clips --output ./long --hours 3
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

import cv2
import numpy as np

try:  # pragma: no cover - soundfile import is exercised at runtime
    import soundfile as sf
except ImportError:  # pragma: no cover - keep module importable without soundfile
    sf = None  # type: ignore[assignment]


LOGGER = logging.getLogger("asmr_loop_maker")

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv"}

ProgressCallback = Callable[[float, str], None]


@dataclass
class LoopAnalysis:
    """Result of the loop point search."""

    start_frame: int
    end_frame: int
    fps: float
    score: float
    pixel_diff: float
    hist_correlation: float

    @property
    def start_seconds(self) -> float:
        return self.start_frame / self.fps

    @property
    def end_seconds(self) -> float:
        return self.end_frame / self.fps

    @property
    def duration_seconds(self) -> float:
        return (self.end_frame - self.start_frame) / self.fps


@dataclass
class ProcessResult:
    """Final result returned by ``process_video``."""

    input_path: str
    output_path: str
    analysis: LoopAnalysis
    output_seconds: float
    crossfade_seconds: float
    has_audio: bool


# ---------------------------------------------------------------------------
# FFmpeg helpers
# ---------------------------------------------------------------------------


def _require_ffmpeg() -> str:
    """Locate the ffmpeg binary or raise a helpful error."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg not found in PATH. Install FFmpeg and ensure 'ffmpeg' is callable."
        )
    return ffmpeg


def _call(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# ---------------------------------------------------------------------------
# Frame reading
# ---------------------------------------------------------------------------


def read_video_frames(
    video_path: str | os.PathLike,
    on_progress: Optional[ProgressCallback] = None,
) -> Tuple[List[np.ndarray], float, int, int]:
    """Read every frame from a video file.

    Returns ``(frames, fps, width, height)``.
    """
    path = str(video_path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Video file not found: {path}")

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video for reading: {path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    frames: List[np.ndarray] = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            frames.append(frame)
            if on_progress and total > 0 and len(frames) % 10 == 0:
                on_progress(min(len(frames) / total, 1.0), "Membaca frame video")
    finally:
        cap.release()

    if not frames:
        raise RuntimeError(f"No frames decoded from video: {path}")
    if width == 0 or height == 0:
        height, width = frames[0].shape[:2]
    return frames, float(fps), int(width), int(height)


# ---------------------------------------------------------------------------
# Frame signatures + comparison
# ---------------------------------------------------------------------------


def frame_signature(
    frame: np.ndarray, size: int = 96
) -> Tuple[np.ndarray, np.ndarray]:
    """Build a compact signature for a single frame.

    The signature is a pair ``(small_gray, color_histogram)`` where ``small_gray``
    is a downscaled grayscale thumbnail in ``[0, 1]`` and ``color_histogram`` is
    a normalised 2D HSV (hue, saturation) histogram. Both pieces are used by
    :func:`compare_signatures`.
    """
    if frame is None or frame.size == 0:
        raise ValueError("Empty frame supplied to frame_signature.")
    small = cv2.resize(frame, (size, size), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(hist, hist, alpha=0.0, beta=1.0, norm_type=cv2.NORM_MINMAX)
    return gray, hist.astype(np.float32)


def compare_signatures(
    sig_a: Tuple[np.ndarray, np.ndarray],
    sig_b: Tuple[np.ndarray, np.ndarray],
) -> Tuple[float, float, float]:
    """Compare two frame signatures.

    Returns ``(score, pixel_diff, hist_correlation)`` where ``score`` is a
    distance (lower = smoother loop) combining the grayscale pixel difference
    and the colour histogram correlation distance.
    """
    gray_a, hist_a = sig_a
    gray_b, hist_b = sig_b
    pixel_diff = float(np.mean(np.abs(gray_a - gray_b)))
    hist_corr = float(cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL))
    hist_dist = (1.0 - hist_corr) * 0.5  # map [-1, 1] -> [1, 0] distance
    score = pixel_diff * 0.6 + hist_dist * 0.4
    return score, pixel_diff, hist_corr


# ---------------------------------------------------------------------------
# Loop point search
# ---------------------------------------------------------------------------


def find_best_loop_points(
    frames: List[np.ndarray],
    fps: float,
    min_segment_seconds: float = 2.0,
    signature_size: int = 96,
    on_progress: Optional[ProgressCallback] = None,
) -> LoopAnalysis:
    """Return the (start, end) frame pair that creates the smoothest loop.

    The algorithm computes a signature for every frame, then for every
    candidate start frame it scores the distance to every candidate end frame
    that is at least ``min_segment_seconds`` later. The pair with the lowest
    combined score (60% grayscale pixel difference, 40% histogram correlation
    distance) is returned.
    """
    n = len(frames)
    if n < 4:
        raise RuntimeError("Video has too few frames to build a loop (need at least 4).")

    min_gap = max(int(round(min_segment_seconds * fps)), 2)
    if min_gap >= n:
        raise RuntimeError(
            "Source video is shorter than the requested minimum segment length."
        )

    grays = np.empty((n, signature_size, signature_size), dtype=np.float32)
    hist_len = 32 * 32
    hists = np.empty((n, hist_len), dtype=np.float32)
    for i, frame in enumerate(frames):
        gray, hist = frame_signature(frame, size=signature_size)
        grays[i] = gray
        hists[i] = hist.flatten()
        if on_progress and (i % 5 == 0 or i == n - 1):
            on_progress(0.5 * (i + 1) / n, "Menghitung signature frame")

    flat = grays.reshape(n, -1)
    hist_means = hists.mean(axis=1, keepdims=True)
    hists_centered = hists - hist_means
    hist_norms = np.sqrt((hists_centered ** 2).sum(axis=1)) + 1e-12

    best: Optional[LoopAnalysis] = None
    indices = np.arange(n)
    for s in range(n):
        # Grayscale pixel difference between frame ``s`` and every other frame.
        diffs = np.mean(np.abs(flat - flat[s : s + 1]), axis=1)
        # Histogram correlation between frame ``s`` and every other frame.
        num = (hists_centered[s] * hists_centered).sum(axis=1)
        corrs = num / (hist_norms[s] * hist_norms)
        hist_dists = (1.0 - corrs) * 0.5
        scores = diffs * 0.6 + hist_dists * 0.4

        valid = indices >= s + min_gap
        if not np.any(valid):
            continue
        masked = np.where(valid, scores, np.inf)
        e_best = int(np.argmin(masked))
        score = float(masked[e_best])
        if best is None or score < best.score:
            best = LoopAnalysis(
                start_frame=s,
                end_frame=e_best,
                fps=fps,
                score=score,
                pixel_diff=float(diffs[e_best]),
                hist_correlation=float(corrs[e_best]),
            )
        if on_progress and (s % 10 == 0 or s == n - 1):
            on_progress(0.5 + 0.5 * (s + 1) / n, "Mencari titik loop terbaik")

    if best is None:
        raise RuntimeError("Failed to find a loop point. Try a shorter min_segment_seconds.")
    return best


# ---------------------------------------------------------------------------
# Video looping
# ---------------------------------------------------------------------------


def _spawn_video_encoder(
    output_path: str, width: int, height: int, fps: float
) -> subprocess.Popen:
    ffmpeg = _require_ffmpeg()
    cmd = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pixel_format",
        "bgr24",
        "-video_size",
        f"{width}x{height}",
        "-framerate",
        f"{fps}",
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-movflags",
        "+faststart",
        output_path,
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def make_looped_video(
    frames: List[np.ndarray],
    fps: float,
    analysis: LoopAnalysis,
    output_seconds: float,
    crossfade_seconds: float,
    output_path: str,
    on_progress: Optional[ProgressCallback] = None,
) -> None:
    """Build the long looped video (no audio yet) with visual crossfades.

    The loop segment ``frames[start..end]`` is written back-to-back. Between
    consecutive iterations the last ``K`` frames are linearly blended with the
    first ``K`` frames of the next iteration, where ``K = crossfade_seconds *
    fps``.
    """
    segment = frames[analysis.start_frame : analysis.end_frame + 1]
    if len(segment) < 2:
        raise RuntimeError("Selected loop segment is too short to encode.")

    height, width = segment[0].shape[:2]
    seg_len = len(segment)
    max_crossfade = max(seg_len // 2 - 1, 0)
    crossfade_frames = max(0, min(int(round(crossfade_seconds * fps)), max_crossfade))
    if crossfade_seconds > 0 and crossfade_frames < 2:
        crossfade_frames = 0

    body_len = seg_len - crossfade_frames
    total_frames_target = max(1, int(round(output_seconds * fps)))

    proc = _spawn_video_encoder(output_path, width, height, fps)
    if proc.stdin is None:
        raise RuntimeError("Failed to open stdin for FFmpeg video encoder.")

    written = 0
    try:
        while written < total_frames_target:
            for i in range(body_len):
                if written >= total_frames_target:
                    break
                proc.stdin.write(np.ascontiguousarray(segment[i]).tobytes())
                written += 1
                if on_progress and written % 200 == 0:
                    on_progress(written / total_frames_target, "Encoding video loop")
            if written >= total_frames_target:
                break

            if crossfade_frames > 0:
                for k in range(crossfade_frames):
                    if written >= total_frames_target:
                        break
                    alpha = (k + 1) / (crossfade_frames + 1)
                    tail = segment[body_len + k].astype(np.float32)
                    head = segment[k].astype(np.float32)
                    blended = tail * (1.0 - alpha) + head * alpha
                    np.clip(blended, 0, 255, out=blended)
                    proc.stdin.write(np.ascontiguousarray(blended.astype(np.uint8)).tobytes())
                    written += 1
                    if on_progress and written % 200 == 0:
                        on_progress(written / total_frames_target, "Encoding video loop")
    finally:
        try:
            proc.stdin.close()
        except Exception:  # pragma: no cover - best effort cleanup
            pass
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"FFmpeg video encoder exited with code {rc}.")
    if on_progress:
        on_progress(1.0, "Encoding video selesai")


# ---------------------------------------------------------------------------
# Audio looping
# ---------------------------------------------------------------------------


def extract_audio(
    input_path: str,
    output_wav: str,
    start_seconds: float = 0.0,
    duration_seconds: Optional[float] = None,
) -> bool:
    """Extract audio from a video clip as 16-bit stereo WAV.

    Returns ``True`` when a non-empty WAV is created and ``False`` when the
    source has no audio stream (so the caller can produce a silent video).
    """
    ffmpeg = _require_ffmpeg()
    cmd = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-ss",
        f"{start_seconds:.6f}",
        "-i",
        input_path,
    ]
    if duration_seconds is not None:
        cmd += ["-t", f"{duration_seconds:.6f}"]
    cmd += [
        "-vn",
        "-ac",
        "2",
        "-ar",
        "44100",
        "-acodec",
        "pcm_s16le",
        output_wav,
    ]
    try:
        _call(cmd)
    except subprocess.CalledProcessError:
        return False
    return os.path.isfile(output_wav) and os.path.getsize(output_wav) > 0


def make_looped_audio(
    wav_path: str,
    output_wav: str,
    output_seconds: float,
    crossfade_seconds: float,
) -> None:
    """Loop and crossfade an audio file using soundfile / numpy."""
    if sf is None:
        raise RuntimeError(
            "soundfile is required for audio processing. Install with 'pip install soundfile'."
        )
    data, sample_rate = sf.read(wav_path, always_2d=True)
    seg = data.astype(np.float32)
    seg_len, channels = seg.shape
    if seg_len < 2:
        raise RuntimeError("Audio segment is too short to loop.")

    max_crossfade = max(seg_len // 2 - 1, 0)
    crossfade_samples = max(0, min(int(round(crossfade_seconds * sample_rate)), max_crossfade))
    target_samples = max(1, int(round(output_seconds * sample_rate)))

    body_len = seg_len - crossfade_samples
    out = np.empty((target_samples, channels), dtype=np.float32)
    written = 0

    if crossfade_samples > 0:
        fade_in = np.linspace(0.0, 1.0, crossfade_samples, dtype=np.float32)[:, None]
        fade_out = 1.0 - fade_in
        tail = seg[body_len:]
        head = seg[:crossfade_samples]
        crossfade_mix = tail * fade_out + head * fade_in
    else:
        crossfade_mix = None

    while written < target_samples:
        body_chunk = seg[:body_len]
        n = min(body_len, target_samples - written)
        out[written : written + n] = body_chunk[:n]
        written += n
        if written >= target_samples:
            break
        if crossfade_mix is not None:
            n = min(crossfade_samples, target_samples - written)
            out[written : written + n] = crossfade_mix[:n]
            written += n

    sf.write(output_wav, out, sample_rate, subtype="PCM_16")


# ---------------------------------------------------------------------------
# Muxing
# ---------------------------------------------------------------------------


def mux_video_audio(
    video_path: str,
    audio_path: Optional[str],
    output_path: str,
) -> None:
    """Mux the looped silent video with the looped audio into an H.264/AAC MP4.

    When ``audio_path`` is ``None`` the function simply copies the video stream
    to ``output_path`` so callers always end up with a valid MP4.
    """
    ffmpeg = _require_ffmpeg()
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", video_path]
    if audio_path:
        cmd += ["-i", audio_path]
    cmd += ["-c:v", "copy", "-map", "0:v:0"]
    if audio_path:
        cmd += [
            "-map",
            "1:a:0",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
        ]
    cmd += ["-movflags", "+faststart", output_path]
    _call(cmd)


# ---------------------------------------------------------------------------
# Top-level pipeline
# ---------------------------------------------------------------------------


def process_video(
    input_path: str,
    output_path: str,
    output_hours: float = 1.0,
    crossfade_seconds: float = 0.5,
    min_segment_seconds: float = 2.0,
    signature_size: int = 96,
    on_progress: Optional[ProgressCallback] = None,
    work_dir: Optional[str] = None,
) -> ProcessResult:
    """Run the full ASMR loop pipeline on a single input file."""
    _require_ffmpeg()
    output_seconds = float(output_hours) * 3600.0
    if output_seconds <= 0:
        raise ValueError("output_hours must be > 0")
    if crossfade_seconds < 0:
        raise ValueError("crossfade_seconds must be >= 0")
    if min_segment_seconds <= 0:
        raise ValueError("min_segment_seconds must be > 0")

    cleanup_work_dir = work_dir is None
    work = work_dir or tempfile.mkdtemp(prefix="asmr_loop_")
    os.makedirs(work, exist_ok=True)

    def progress(pct: float, msg: str) -> None:
        if on_progress is not None:
            on_progress(max(0.0, min(1.0, pct)), msg)

    try:
        progress(0.0, "Membaca frame video")
        frames, fps, _, _ = read_video_frames(
            input_path,
            on_progress=lambda p, m: progress(0.1 * p, m),
        )
        progress(0.1, "Mencari titik loop terbaik")
        analysis = find_best_loop_points(
            frames,
            fps,
            min_segment_seconds=min_segment_seconds,
            signature_size=signature_size,
            on_progress=lambda p, m: progress(0.1 + 0.3 * p, m),
        )
        progress(0.4, "Encoding video loop")

        video_tmp = os.path.join(work, "looped_video.mp4")
        make_looped_video(
            frames,
            fps,
            analysis,
            output_seconds,
            crossfade_seconds,
            video_tmp,
            on_progress=lambda p, m: progress(0.4 + 0.4 * p, m),
        )

        progress(0.8, "Memproses audio")
        audio_in = os.path.join(work, "segment.wav")
        looped_audio = os.path.join(work, "looped_audio.wav")
        has_audio = extract_audio(
            input_path,
            audio_in,
            start_seconds=analysis.start_seconds,
            duration_seconds=analysis.duration_seconds,
        )

        audio_for_mux: Optional[str]
        if has_audio:
            make_looped_audio(
                audio_in,
                looped_audio,
                output_seconds=output_seconds,
                crossfade_seconds=crossfade_seconds,
            )
            audio_for_mux = looped_audio
        else:
            audio_for_mux = None
            LOGGER.warning("Input has no audio stream; producing silent video.")

        progress(0.95, "Muxing video + audio")
        parent = os.path.dirname(os.path.abspath(output_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        mux_video_audio(video_tmp, audio_for_mux, output_path)

        progress(1.0, "Selesai")
        return ProcessResult(
            input_path=input_path,
            output_path=output_path,
            analysis=analysis,
            output_seconds=output_seconds,
            crossfade_seconds=crossfade_seconds,
            has_audio=has_audio,
        )
    finally:
        if cleanup_work_dir:
            shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _iter_inputs(inputs: Iterable[str], batch_dir: Optional[str]) -> List[str]:
    files: List[str] = []
    for entry in inputs:
        p = Path(entry)
        if p.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                files.extend(str(x) for x in p.rglob(f"*{ext}"))
        elif p.is_file():
            files.append(str(p))
        else:
            raise FileNotFoundError(entry)
    if batch_dir:
        p = Path(batch_dir)
        if not p.is_dir():
            raise NotADirectoryError(batch_dir)
        for ext in SUPPORTED_EXTENSIONS:
            files.extend(str(x) for x in p.rglob(f"*{ext}"))
    deduped: List[str] = []
    seen: set[str] = set()
    for f in files:
        if f in seen:
            continue
        seen.add(f)
        deduped.append(f)
    return deduped


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "ASMR Seamless Loop Maker — turn a short clip into a long, smooth ASMR loop. "
            "Pass a single file for one-shot processing or multiple files / --batch-dir for batch mode."
        )
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Input video file(s). Pass multiple paths or a directory for batch mode.",
    )
    parser.add_argument(
        "--batch-dir",
        help="Process every supported video found inside this directory (recursive).",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output MP4 file (single input) or output directory (batch).",
    )
    parser.add_argument(
        "--hours",
        type=float,
        default=1.0,
        help="Output duration in hours (default: 1.0).",
    )
    parser.add_argument(
        "--crossfade",
        type=float,
        default=0.5,
        help="Crossfade duration in seconds (default: 0.5).",
    )
    parser.add_argument(
        "--min-segment",
        type=float,
        default=2.0,
        help="Minimum loop segment length in seconds (default: 2.0).",
    )
    parser.add_argument(
        "--signature-size",
        type=int,
        default=96,
        help="Thumbnail size used for frame signatures (default: 96).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging.",
    )
    return parser


def _print_progress(pct: float, msg: str) -> None:
    bar_width = 30
    filled = int(round(pct * bar_width))
    bar = "#" * filled + "-" * (bar_width - filled)
    sys.stdout.write(f"\r[{bar}] {pct * 100:5.1f}% {msg:<40s}")
    sys.stdout.flush()
    if pct >= 1.0:
        sys.stdout.write("\n")


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )
    try:
        inputs = _iter_inputs(args.inputs, args.batch_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:
        parser.error(str(exc))
        return 2  # pragma: no cover - parser.error calls sys.exit
    if not inputs:
        parser.error("No input videos found. Pass one or more files or use --batch-dir.")
        return 2  # pragma: no cover

    is_batch = len(inputs) > 1 or args.batch_dir is not None
    output_path = Path(args.output)
    if is_batch:
        output_path.mkdir(parents=True, exist_ok=True)

    successes = 0
    for idx, src in enumerate(inputs, start=1):
        if is_batch:
            out_file = output_path / (Path(src).stem + "_asmr_loop.mp4")
        else:
            out_file = output_path
        print(f"\n[{idx}/{len(inputs)}] {src} -> {out_file}")
        try:
            result = process_video(
                input_path=src,
                output_path=str(out_file),
                output_hours=args.hours,
                crossfade_seconds=args.crossfade,
                min_segment_seconds=args.min_segment,
                signature_size=args.signature_size,
                on_progress=_print_progress,
            )
        except Exception as exc:  # noqa: BLE001 - surface any pipeline failure per file
            print(f"  GAGAL: {exc}")
            continue
        successes += 1
        a = result.analysis
        print(
            f"  loop {a.start_seconds:.2f}s -> {a.end_seconds:.2f}s "
            f"(durasi {a.duration_seconds:.2f}s, skor {a.score:.4f}, "
            f"audio={'yes' if result.has_audio else 'no'})"
        )

    print(f"\nSelesai memproses {successes}/{len(inputs)} file.")
    return 0 if successes == len(inputs) else 1


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
