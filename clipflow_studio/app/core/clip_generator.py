"""Compose ``Clip`` objects from a transcript + the highlight detector output.

The clip generator's job is to:

1. Snap each highlight's start/end to natural sentence boundaries.
2. Provide multiple variants per highlight (15s, 30s, 45s, 60s + custom).
3. Filter clips that overlap heavily with one another.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from ..utils.logger import get_logger
from .highlight_detector import Highlight, detect_highlights
from .transcriber import TranscriptSegment, WordToken

_LOG = get_logger("clip_generator")


@dataclass
class Clip:
    """A user-selectable clip ready to be rendered/exported."""

    index: int
    start: float
    end: float
    score: float
    transcript: str
    duration_preset: int
    reasons: List[str] = field(default_factory=list)
    segments: List[TranscriptSegment] = field(default_factory=list)
    selected: bool = False

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "score": self.score,
            "transcript": self.transcript,
            "duration_preset": self.duration_preset,
            "reasons": list(self.reasons),
            "selected": self.selected,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _snap_to_sentence_boundary(
    segments: Sequence[TranscriptSegment],
    target_start: float,
    target_end: float,
) -> tuple[float, float]:
    """Snap to nearest segment.start <= target_start and segment.end >= target_end."""
    if not segments:
        return target_start, target_end
    new_start = target_start
    new_end = target_end
    # Prefer the latest segment.start that is <= target_start
    for seg in segments:
        if seg.start <= target_start:
            new_start = seg.start
        else:
            break
    # Prefer the earliest segment.end that is >= target_end
    for seg in segments:
        if seg.end >= target_end:
            new_end = seg.end
            break
    return new_start, new_end


def _segments_in_window(
    segments: Sequence[TranscriptSegment],
    start: float,
    end: float,
) -> List[TranscriptSegment]:
    out: List[TranscriptSegment] = []
    for seg in segments:
        if seg.end < start:
            continue
        if seg.start > end:
            break
        out.append(seg)
    return out


# ---------------------------------------------------------------------------
# Clip generation
# ---------------------------------------------------------------------------
def generate_clips(
    segments: Sequence[TranscriptSegment],
    *,
    top_k: int = 5,
    duration_presets: Sequence[int] = (15, 30, 45, 60),
    custom_duration: Optional[int] = None,
    use_embeddings: bool = True,
) -> List[Clip]:
    """Run highlight detection and convert results into ``Clip`` objects."""
    durations: List[int] = list(duration_presets)
    if custom_duration and custom_duration not in durations:
        durations.append(int(custom_duration))

    highlights = detect_highlights(
        segments,
        top_k=top_k,
        durations=tuple(durations),
        use_embeddings=use_embeddings,
    )
    clips: List[Clip] = []
    for i, h in enumerate(highlights):
        start, end = _snap_to_sentence_boundary(segments, h.start, h.end)
        window_segments = _segments_in_window(segments, start, end)
        transcript = " ".join(s.text for s in window_segments).strip() or h.transcript
        clip = Clip(
            index=i,
            start=round(start, 3),
            end=round(end, 3),
            score=h.score,
            transcript=transcript,
            duration_preset=h.duration_target or durations[0],
            reasons=list(h.reasons),
            segments=list(window_segments),
        )
        clips.append(clip)
    return clips


def make_custom_clip(
    segments: Sequence[TranscriptSegment],
    start: float,
    end: float,
    *,
    index: int = 0,
) -> Clip:
    """Build a clip from a manual time range (used by the UI custom mode)."""
    start, end = _snap_to_sentence_boundary(segments, start, end)
    window = _segments_in_window(segments, start, end)
    return Clip(
        index=index,
        start=round(start, 3),
        end=round(end, 3),
        score=0.5,
        transcript=" ".join(s.text for s in window).strip(),
        duration_preset=int(round(end - start)),
        reasons=["custom"],
        segments=list(window),
    )


def words_in_clip(clip: Clip) -> List[WordToken]:
    words: List[WordToken] = []
    for seg in clip.segments:
        for word in seg.words:
            if word.end < clip.start or word.start > clip.end:
                continue
            words.append(word)
    return words
