"""Batch render orchestrator.

Drives ``render_engine.render_video`` for a list of audio files, threading
results back to the GUI with per-file and overall progress.
"""
from __future__ import annotations

import copy
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional

from . import audio_reader, background_manager, render_engine


@dataclass
class BatchItem:
    audio_path: str
    output_path: str
    background_override: Optional[str] = None


@dataclass
class BatchSettings:
    background_mode: str = "order"  # order | match | random | none
    background_folder: str = ""


@dataclass
class BatchProgress:
    item_index: int
    item_count: int
    current_file: str
    current_progress: float  # 0..1 for current song
    overall_progress: float  # 0..1 across the whole batch
    eta: float
    message: str = ""


ProgressCallback = Callable[[BatchProgress], None]
LogCallback = Callable[[str], None]


def build_items(
    folder: str,
    output_dir: str,
    settings: BatchSettings,
) -> list[BatchItem]:
    """Enumerate audio files in ``folder`` and pair with backgrounds."""
    audio_files = audio_reader.list_supported_in_folder(folder)
    bg_map: dict[str, Optional[str]] = {}
    if settings.background_folder and settings.background_mode != "none":
        bg_map = background_manager.match_for_batch(
            audio_files,
            settings.background_folder,
            mode=settings.background_mode,
        )

    items: list[BatchItem] = []
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for a in audio_files:
        out = Path(output_dir) / f"{a.stem}.mp4"
        items.append(
            BatchItem(
                audio_path=str(a),
                output_path=str(out),
                background_override=bg_map.get(str(a)),
            )
        )
    return items


def run(
    items: list[BatchItem],
    base_job: render_engine.RenderJob,
    on_progress: Optional[ProgressCallback] = None,
    on_log: Optional[LogCallback] = None,
    cancel_event: Optional[threading.Event] = None,
) -> list[str]:
    """Render each item sequentially.

    Sequential is intentional — running multiple FFmpeg jobs at once on a
    "potato laptop" is counter-productive and would make the UI feel frozen.
    """
    on_progress = on_progress or (lambda *_: None)
    on_log = on_log or (lambda *_: None)
    cancel_event = cancel_event or threading.Event()
    outputs: list[str] = []

    start = time.monotonic()
    for idx, item in enumerate(items):
        if cancel_event.is_set():
            on_log("[batch] cancelled")
            break
        on_log(f"[batch] ({idx + 1}/{len(items)}) {Path(item.audio_path).name}")

        job = copy.deepcopy(base_job)
        job.audio_path = item.audio_path
        job.output_path = item.output_path
        job.background_override = item.background_override
        job.lyrics_data = None  # always re-extract per file

        def _proxy(p: render_engine.RenderProgress, _idx=idx, _count=len(items)) -> None:
            elapsed = time.monotonic() - start
            overall = (_idx + p.fraction) / max(1, _count)
            eta_total = elapsed * (1 - overall) / max(overall, 1e-3) if overall > 0 else 0.0
            on_progress(
                BatchProgress(
                    item_index=_idx,
                    item_count=_count,
                    current_file=Path(item.audio_path).name,
                    current_progress=p.fraction,
                    overall_progress=overall,
                    eta=eta_total,
                    message=p.message,
                )
            )

        try:
            out = render_engine.render_video(
                job,
                on_progress=_proxy,
                on_log=on_log,
                cancel_event=cancel_event,
            )
            outputs.append(out)
            on_log(f"[batch] ok -> {out}")
        except Exception as exc:  # noqa: BLE001
            on_log(f"[batch] FAILED for {item.audio_path}: {exc}")

    on_log(f"[batch] complete in {time.monotonic() - start:.1f}s; {len(outputs)}/{len(items)} successful")
    return outputs


__all__ = ["BatchItem", "BatchSettings", "BatchProgress", "build_items", "run"]
