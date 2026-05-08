"""Detect interesting/highlight segments from a transcript.

The detector combines simple, free heuristics with optional semantic similarity
from ``sentence-transformers`` to assign a score to each transcript segment:

- Emotional / strong-language keywords (multilingual)
- Punchline-style endings ("the truth is", "hasilnya", "ternyata", ...)
- Questions
- Short, emphatic sentences
- Topic shifts (segments whose embedding is far from neighbors)
- Repeated keywords (TF-IDF style)

If ``sentence-transformers`` is unavailable, the detector still works using
just the heuristics.  This keeps the installer cost low while still producing
useful clips.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ..utils.logger import get_logger
from .transcriber import TranscriptSegment

_LOG = get_logger("highlight")

ProgressFn = Callable[[str, float], None]


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------
@dataclass
class Highlight:
    start: float
    end: float
    score: float
    transcript: str
    reasons: List[str] = field(default_factory=list)
    segment_indices: List[int] = field(default_factory=list)
    duration_target: Optional[int] = None


# ---------------------------------------------------------------------------
# Heuristic vocabulary
# ---------------------------------------------------------------------------
_EMOTIONAL_KEYWORDS = {
    # English
    "love", "hate", "amazing", "incredible", "shocking", "shocked", "wow",
    "crazy", "insane", "unbelievable", "horrible", "awesome", "terrible",
    "afraid", "scared", "angry", "happy", "excited",
    # Indonesian / Malay
    "luar biasa", "gila", "edan", "keren", "marah", "bahagia", "sedih",
    "kaget", "ngeri", "ajaib", "dahsyat", "terbaik", "paling",
}

_PUNCHLINE_TRIGGERS = {
    "the truth is", "in the end", "ultimately", "the reality is", "actually",
    "ternyata", "hasilnya", "kesimpulannya", "pada akhirnya", "yang penting",
    "intinya", "rahasianya", "the point is", "the key is",
}

_TOPIC_SHIFT_TRIGGERS = {
    "now", "next", "however", "but", "anyway", "moving on", "let's",
    "selanjutnya", "kemudian", "tapi", "namun", "sekarang", "berikutnya",
    "lanjut", "oke", "okay",
}


_WORD_RE = re.compile(r"[\w'\-]+", re.UNICODE)
_QUESTION_RE = re.compile(r"\?$|^(?:why|what|how|when|where|who|kenapa|kenapa|bagaimana|apa|siapa|kapan)\b", re.IGNORECASE)


def _tokenize(text: str) -> List[str]:
    return [tok.lower() for tok in _WORD_RE.findall(text)]


def _contains_phrase(text_lower: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text_lower for phrase in phrases)


# ---------------------------------------------------------------------------
# Optional embedder
# ---------------------------------------------------------------------------
class _SafeEmbedder:
    """Best-effort wrapper for sentence-transformers; degrades gracefully."""

    _MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self) -> None:
        self._model = None
        self._available = True

    def encode(self, texts: Sequence[str]) -> Optional[List[List[float]]]:
        if not self._available:
            return None
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

                self._model = SentenceTransformer(self._MODEL_NAME)
            except Exception as exc:  # noqa: BLE001
                _LOG.warning("sentence-transformers unavailable: %s", exc)
                self._available = False
                return None
        try:
            vectors = self._model.encode(list(texts), show_progress_bar=False)
            return [list(map(float, vec)) for vec in vectors]
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("Embedding failed: %s", exc)
            self._available = False
            return None


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


# ---------------------------------------------------------------------------
# Per-segment scoring
# ---------------------------------------------------------------------------
def _segment_keyword_score(text: str, global_freq: Counter) -> Tuple[float, List[str]]:
    tokens = _tokenize(text)
    if not tokens:
        return 0.0, []
    score = 0.0
    reasons: List[str] = []
    text_lower = text.lower()

    # Emotional vocabulary
    emotional_hits = [t for t in tokens if t in _EMOTIONAL_KEYWORDS]
    emotional_phrase_hits = [p for p in _EMOTIONAL_KEYWORDS if " " in p and p in text_lower]
    if emotional_hits or emotional_phrase_hits:
        score += 0.35 * len(set(emotional_hits + emotional_phrase_hits))
        reasons.append("emotional")

    # Punchlines
    if _contains_phrase(text_lower, _PUNCHLINE_TRIGGERS):
        score += 0.45
        reasons.append("punchline")

    # Questions
    if _QUESTION_RE.search(text.strip()):
        score += 0.4
        reasons.append("question")

    # Topic shifts (start of segment)
    first_two = " ".join(tokens[:2])
    if any(first_two.startswith(t) for t in _TOPIC_SHIFT_TRIGGERS):
        score += 0.2
        reasons.append("topic_shift")

    # Strong short sentences (5–14 words)
    if 5 <= len(tokens) <= 14:
        score += 0.1
        reasons.append("punchy")

    # Repeated keywords (TF style — words seen multiple times globally)
    important_hits = [t for t in tokens if global_freq.get(t, 0) >= 3 and len(t) >= 4]
    if important_hits:
        score += min(0.4, 0.05 * len(set(important_hits)))
        reasons.append("keyword")

    return score, reasons


def _topic_shift_boost(
    segments: Sequence[TranscriptSegment],
    embeddings: Optional[List[List[float]]],
) -> List[float]:
    if not embeddings:
        return [0.0] * len(segments)
    boosts = [0.0] * len(segments)
    for i in range(len(segments)):
        if i == 0:
            continue
        prev = embeddings[i - 1]
        cur = embeddings[i]
        sim = _cosine(prev, cur)
        # Lower similarity → bigger topic shift
        if sim < 0.55:
            boosts[i] += 0.25
    return boosts


# ---------------------------------------------------------------------------
# Highlight grouping
# ---------------------------------------------------------------------------
def _build_highlights(
    segments: Sequence[TranscriptSegment],
    scores: Sequence[float],
    reasons: Sequence[List[str]],
    durations: Sequence[int],
    top_k: int,
    *,
    min_gap: float = 2.0,
) -> List[Highlight]:
    """Greedy: pick the highest-scoring segments and grow each into a window."""
    indexed = sorted(
        range(len(segments)), key=lambda i: scores[i], reverse=True
    )
    selected: List[Highlight] = []
    for idx in indexed:
        if scores[idx] <= 0:
            continue
        anchor = segments[idx]
        for target in durations:
            window = _grow_window(segments, idx, target_duration=target)
            if not window:
                continue
            start_idx, end_idx = window
            start_t = segments[start_idx].start
            end_t = segments[end_idx].end
            if any(_overlaps(h, start_t, end_t, min_gap) for h in selected):
                continue
            transcript = " ".join(s.text for s in segments[start_idx : end_idx + 1]).strip()
            window_score = max(scores[start_idx : end_idx + 1])
            selected.append(
                Highlight(
                    start=start_t,
                    end=end_t,
                    score=round(float(window_score), 3),
                    transcript=transcript,
                    reasons=sorted(set(reasons[idx])),
                    segment_indices=list(range(start_idx, end_idx + 1)),
                    duration_target=target,
                )
            )
            break  # one duration per anchor is enough; rotate to next anchor
        if len(selected) >= top_k:
            break
    selected.sort(key=lambda h: -h.score)
    return selected


def _overlaps(highlight: Highlight, start: float, end: float, min_gap: float) -> bool:
    return not (end + min_gap <= highlight.start or start - min_gap >= highlight.end)


def _grow_window(
    segments: Sequence[TranscriptSegment],
    idx: int,
    target_duration: int,
) -> Optional[Tuple[int, int]]:
    """Expand around ``idx`` until the window reaches ``target_duration`` seconds."""
    if not segments:
        return None
    start = idx
    end = idx
    while True:
        cur_start = segments[start].start
        cur_end = segments[end].end
        if cur_end - cur_start >= target_duration:
            return start, end
        # Expand on the side that adds less
        prev_gap = cur_start - segments[start - 1].end if start > 0 else math.inf
        next_gap = segments[end + 1].start - cur_end if end + 1 < len(segments) else math.inf
        if prev_gap == math.inf and next_gap == math.inf:
            return start, end
        if next_gap <= prev_gap:
            end += 1
        else:
            start -= 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def detect_highlights(
    segments: Sequence[TranscriptSegment],
    *,
    top_k: int = 5,
    durations: Sequence[int] = (15, 30, 45, 60),
    use_embeddings: bool = True,
    progress: Optional[ProgressFn] = None,
) -> List[Highlight]:
    if not segments:
        return []

    if progress:
        progress("Tokenizing transcript ...", 0.1)

    global_freq: Counter = Counter()
    for seg in segments:
        global_freq.update(_tokenize(seg.text))

    base_scores: List[float] = []
    base_reasons: List[List[str]] = []
    for seg in segments:
        score, reasons = _segment_keyword_score(seg.text, global_freq)
        base_scores.append(score)
        base_reasons.append(reasons)

    embeddings: Optional[List[List[float]]] = None
    if use_embeddings:
        if progress:
            progress("Computing semantic embeddings (optional) ...", 0.4)
        embedder = _SafeEmbedder()
        embeddings = embedder.encode([seg.text for seg in segments])

    boosts = _topic_shift_boost(segments, embeddings)
    final_scores: List[float] = [base + boost for base, boost in zip(base_scores, boosts)]
    for i, boost in enumerate(boosts):
        if boost > 0 and "topic_shift" not in base_reasons[i]:
            base_reasons[i].append("topic_shift")

    if progress:
        progress("Selecting top highlights ...", 0.85)

    highlights = _build_highlights(
        segments,
        scores=final_scores,
        reasons=base_reasons,
        durations=tuple(durations),
        top_k=top_k,
    )

    if progress:
        progress(f"Picked {len(highlights)} clips.", 1.0)
    return highlights


def highlight_to_dict(h: Highlight) -> Dict[str, Any]:
    return {
        "start": h.start,
        "end": h.end,
        "score": h.score,
        "transcript": h.transcript,
        "reasons": h.reasons,
        "duration_target": h.duration_target,
        "segment_indices": h.segment_indices,
    }
