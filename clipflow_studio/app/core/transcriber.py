"""Audio extraction + faster-whisper transcription.

The transcriber emits :class:`TranscriptSegment` objects with both per-segment
and per-word timestamps when available.  The downstream highlight detector
relies on word-level timing for accurate clip boundaries.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional

from ..utils import config as cfg
from ..utils.logger import get_logger
from . import dependency_manager as deps

_LOG = get_logger("transcriber")

ProgressFn = Callable[[str, float], None]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class WordToken:
    text: str
    start: float
    end: float
    probability: float = 1.0


@dataclass
class TranscriptSegment:
    text: str
    start: float
    end: float
    words: List[WordToken] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    language: Optional[str]
    duration: Optional[float]
    segments: List[TranscriptSegment]
    full_text: str


# ---------------------------------------------------------------------------
# Audio extraction (FFmpeg)
# ---------------------------------------------------------------------------
def extract_audio(
    video_path: str,
    *,
    output_path: Optional[str] = None,
    sample_rate: int = 16000,
) -> str:
    """Extract a 16 kHz mono WAV file suitable for whisper."""
    ffmpeg = deps.get_ffmpeg_path()
    if not ffmpeg:
        raise FileNotFoundError("FFmpeg is required to extract audio.")

    if output_path is None:
        base = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(cfg.get_temp_dir(), f"{base}.wav")

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        video_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        output_path,
    ]
    _LOG.info("Extracting audio: %s", " ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"FFmpeg audio extraction failed: {proc.stderr.decode(errors='ignore')[-400:]}"
        )
    return output_path


# ---------------------------------------------------------------------------
# Transcription (faster-whisper)
# ---------------------------------------------------------------------------
class Transcriber:
    """Lightweight wrapper around faster-whisper."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        compute_type: Optional[str] = None,
        device: str = "auto",
    ) -> None:
        self.model_name = model_name or cfg.get("whisper_model", "base")
        self.compute_type = compute_type or cfg.get("whisper_compute_type", "int8")
        self.device = device
        self._model = None  # lazily instantiated

    def _load_model(self):  # type: ignore[no-untyped-def]
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Run pip install faster-whisper."
            ) from exc
        _LOG.info("Loading faster-whisper model %s (%s)", self.model_name, self.compute_type)
        self._model = WhisperModel(
            self.model_name, device=self.device, compute_type=self.compute_type
        )
        return self._model

    def transcribe(
        self,
        audio_path: str,
        *,
        language: Optional[str] = None,
        progress: Optional[ProgressFn] = None,
    ) -> TranscriptionResult:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(audio_path)

        model = self._load_model()
        if progress:
            progress("Transcribing audio ...", 0.05)

        segments_iter, info = model.transcribe(
            audio_path,
            language=language,
            vad_filter=True,
            word_timestamps=True,
            beam_size=1,
        )

        total_duration = float(info.duration or 0.0) or None
        segments: List[TranscriptSegment] = []
        full_text_parts: List[str] = []

        for seg in segments_iter:
            words: List[WordToken] = []
            for word in getattr(seg, "words", []) or []:
                words.append(
                    WordToken(
                        text=word.word.strip(),
                        start=float(word.start),
                        end=float(word.end),
                        probability=float(getattr(word, "probability", 1.0)),
                    )
                )
            segments.append(
                TranscriptSegment(
                    text=seg.text.strip(),
                    start=float(seg.start),
                    end=float(seg.end),
                    words=words,
                )
            )
            full_text_parts.append(seg.text.strip())
            if progress and total_duration:
                progress(
                    f"Transcribed up to {seg.end:.1f}s",
                    min(1.0, float(seg.end) / total_duration),
                )

        return TranscriptionResult(
            language=getattr(info, "language", None),
            duration=total_duration,
            segments=segments,
            full_text=" ".join(full_text_parts).strip(),
        )


def segments_to_dicts(segments: Iterable[TranscriptSegment]) -> List[Dict[str, Any]]:
    """Convert segments to plain dicts (e.g. for SQLite metadata)."""
    return [
        {
            "text": s.text,
            "start": s.start,
            "end": s.end,
            "words": [
                {"text": w.text, "start": w.start, "end": w.end, "probability": w.probability}
                for w in s.words
            ],
        }
        for s in segments
    ]
