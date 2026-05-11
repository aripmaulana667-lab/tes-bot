"""Batch render orchestration."""
from __future__ import annotations

import asyncio
import random
from pathlib import Path
from typing import List, Optional

from ..config import (
    ALLOWED_BG_EXT,
    ALLOWED_LYRIC_EXT,
    ALLOWED_MUSIC_EXT,
    BACKGROUNDS_DIR,
    LYRICS_DIR,
    MUSIC_DIR,
)
from ..models.render import (
    BackgroundConfig,
    BatchRenderRequest,
    RenderRequest,
)
from .jobs import Job, store
from .render import render_job


def _list_files(folder: Path, allowed_ext: set) -> List[Path]:
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in allowed_ext])


def _resolve_folder(name_or_path: str, default: Path) -> Path:
    p = Path(name_or_path)
    if p.is_absolute() and p.exists():
        return p
    candidate = default / name_or_path
    if candidate.exists():
        return candidate
    return default


def _match_lyrics(music_file: Path, lyrics_files: List[Path]) -> Optional[Path]:
    stem = music_file.stem.lower()
    for lf in lyrics_files:
        if lf.stem.lower() == stem:
            return lf
    return None


def _select_backgrounds(
    idx: int,
    music_file: Path,
    bg_files: List[Path],
    mode: str,
    multi: bool,
) -> List[Path]:
    if not bg_files:
        return []
    if mode == "by_name":
        stem = music_file.stem.lower()
        matches = [b for b in bg_files if b.stem.lower() == stem]
        if matches:
            return matches
        return bg_files[: 1 if not multi else min(5, len(bg_files))]
    if mode == "random":
        if multi:
            count = min(len(bg_files), max(2, random.randint(2, 5)))
            return random.sample(bg_files, count)
        return [random.choice(bg_files)]
    # sequence
    if multi:
        return bg_files
    return [bg_files[idx % len(bg_files)]]


async def run_batch(parent: Job, request: BatchRenderRequest) -> None:
    music_folder = _resolve_folder(request.music_dir, MUSIC_DIR)
    lyrics_folder = _resolve_folder(request.lyrics_dir, LYRICS_DIR)
    bg_folder = _resolve_folder(request.background_dir, BACKGROUNDS_DIR)

    await store.update(
        parent,
        status="rendering",
        message=(
            f"Folder musik: {music_folder.name} | lirik: {lyrics_folder.name} | "
            f"background: {bg_folder.name}"
        ),
    )

    music_files = _list_files(music_folder, ALLOWED_MUSIC_EXT)
    lyrics_files = _list_files(lyrics_folder, ALLOWED_LYRIC_EXT)
    bg_files = _list_files(bg_folder, ALLOWED_BG_EXT)

    if not music_files:
        await store.update(parent, status="failed", error="Tidak ada file musik di folder yang dipilih.")
        return

    total = len(music_files)
    done = 0
    failed = 0
    skipped = 0

    for idx, music in enumerate(music_files):
        if parent.cancel_event.is_set():
            await store.update(parent, status="cancelled", message="Batch dibatalkan.")
            return

        child = store.create("batch_item", parent_id=parent.id)
        await store.update(child, music_file=music.name, message="Menunggu ...")

        lyric = _match_lyrics(music, lyrics_files)
        if lyric is None:
            skipped += 1
            await store.update(
                child,
                status="skipped",
                message=f"Lirik tidak ditemukan untuk {music.name}",
                log_line=f"SKIP: lirik untuk {music.name} tidak ada",
            )
            await store.update(
                parent,
                progress=(idx + 1) / total,
                message=f"{idx+1}/{total} | skip {skipped} | gagal {failed}",
            )
            continue

        backgrounds = _select_backgrounds(
            idx, music, bg_files, request.match_mode, request.multi_background
        )

        # Copy files into expected storage folders if outside
        try:
            _copy_into(music, MUSIC_DIR)
            _copy_into(lyric, LYRICS_DIR)
            for b in backgrounds:
                _copy_into(b, BACKGROUNDS_DIR)
        except Exception as exc:
            await store.update(child, status="failed", error=f"Gagal menyalin file: {exc}")
            failed += 1
            continue

        req = RenderRequest(
            music_file=music.name,
            output_name=music.stem,
            lyrics=request.lyrics.model_copy(update={"file": lyric.name}),
            spectrum=request.spectrum,
            logo=request.logo,
            background=BackgroundConfig(
                mode="multiple" if (request.multi_background and len(backgrounds) > 1) else "single",
                files=[b.name for b in backgrounds],
                slideshow_duration=request.background.slideshow_duration,
                randomize=request.background.randomize,
                dark_overlay=request.background.dark_overlay,
                blur=request.background.blur,
            ),
            render=request.render,
        )

        try:
            await render_job(child, req, preview=False)
            done += 1
        except asyncio.CancelledError:
            await store.update(parent, status="cancelled", message="Batch dibatalkan.")
            return
        except Exception as exc:
            failed += 1
            await store.update(child, status="failed", error=str(exc), message="Gagal.")

        await store.update(
            parent,
            progress=(idx + 1) / total,
            message=f"{idx+1}/{total} | sukses {done} | skip {skipped} | gagal {failed}",
        )

    final_status = "done"
    if failed and not done:
        final_status = "failed"
    await store.update(
        parent,
        status=final_status,
        progress=1.0,
        message=f"Batch selesai. Sukses {done}, skip {skipped}, gagal {failed}.",
    )


def _copy_into(src: Path, dest_folder: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(str(src))
    target = dest_folder / src.name
    if target.resolve() == src.resolve():
        return
    if target.exists():
        return
    import shutil

    shutil.copy2(src, target)
