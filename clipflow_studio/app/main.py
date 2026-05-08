"""Application entry-point.

This module is responsible for:

1. Bootstrapping the logger and database.
2. Showing a splash screen while we probe dependencies and (optionally)
   pre-load the Whisper model.
3. Handing control to :class:`MainWindow` once everything is ready.

The splash + main window both rely on CustomTkinter, but the rest of the
codebase (the ``core`` package) does *not* import the GUI -- which lets us
unit-test logic without a display.
"""
from __future__ import annotations

import os
import sys
import threading
import time
from typing import List, Optional

from . import __app_name__, __tagline__, __version__
from .core import dependency_manager as deps
from .database import db
from .utils import config as cfg
from .utils.logger import get_logger, setup_logging

_LOG = get_logger("main")


def _ensure_runtime_dirs() -> None:
    """Make sure the folders the app expects always exist on disk."""
    for path in (
        cfg.get_outputs_dir(),
        cfg.get_temp_dir(),
        cfg.get_assets_dir(),
        cfg.get_tools_dir(),
        cfg.get_logs_dir(),
        os.path.join(cfg.get_tools_dir(), "ffmpeg"),
        os.path.join(cfg.get_tools_dir(), "deno"),
    ):
        os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# Splash screen
# ---------------------------------------------------------------------------
class _Splash:
    """Minimal CustomTkinter splash window."""

    _STEPS = (
        "Loading dependencies ...",
        "Checking FFmpeg ...",
        "Checking Deno ...",
        "Initializing AI models ...",
        "Almost ready ...",
    )

    def __init__(self) -> None:
        try:
            import customtkinter as ctk  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "CustomTkinter is required to run ClipFlow Studio. "
                "Run setup.bat or pip install customtkinter."
            ) from exc

        from .ui.styles import DARK_PALETTE, apply_default_theme, font

        apply_default_theme()
        self._ctk = ctk
        self.root = ctk.CTk()
        self.root.title(f"{__app_name__}")
        self.root.geometry("520x320")
        self.root.resizable(False, False)
        self.root.configure(fg_color=DARK_PALETTE.bg)

        ctk.CTkLabel(
            self.root,
            text=f"⚡  {__app_name__}",
            font=font(28, "bold"),
            text_color=DARK_PALETTE.text,
        ).pack(pady=(48, 4))

        ctk.CTkLabel(
            self.root,
            text=__tagline__,
            font=font(13),
            text_color=DARK_PALETTE.text_muted,
        ).pack()
        ctk.CTkLabel(
            self.root,
            text=f"v{__version__}",
            font=font(10),
            text_color=DARK_PALETTE.text_muted,
        ).pack(pady=(2, 28))

        self.progress = ctk.CTkProgressBar(self.root, mode="determinate", width=420)
        self.progress.set(0)
        self.progress.pack(pady=(4, 6))
        self.status_label = ctk.CTkLabel(
            self.root,
            text=self._STEPS[0],
            font=font(11),
            text_color=DARK_PALETTE.text_muted,
        )
        self.status_label.pack()

        self.dependency_label = ctk.CTkLabel(
            self.root,
            text="",
            font=font(10),
            text_color=DARK_PALETTE.text_muted,
            wraplength=460,
            justify="center",
        )
        self.dependency_label.pack(pady=(8, 12))

        self._summary_lines: List[str] = []
        self._done = False

    # ------------------------------------------------------------------
    def update(self, step_idx: int, fraction: float = 0.0, detail: str = "") -> None:
        if not self.root.winfo_exists():
            return
        msg = self._STEPS[min(step_idx, len(self._STEPS) - 1)]
        self.status_label.configure(text=msg)
        self.progress.set(max(0.0, min(1.0, float(fraction))))
        if detail:
            self._summary_lines.append(detail)
            if len(self._summary_lines) > 6:
                self._summary_lines = self._summary_lines[-6:]
            self.dependency_label.configure(text="\n".join(self._summary_lines))
        self.root.update_idletasks()
        self.root.update()

    # ------------------------------------------------------------------
    def close(self) -> None:
        try:
            self.root.destroy()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Boot sequence
# ---------------------------------------------------------------------------
def _boot_sequence(splash: _Splash) -> None:
    """Run the splash status updates synchronously."""
    splash.update(0, 0.05, "Booting ClipFlow Studio ...")
    db.init_db()

    splash.update(1, 0.25, _summarize(deps.check_ffmpeg()))
    splash.update(2, 0.45, _summarize(deps.check_deno()))

    # The Whisper model only loads lazily; we just confirm the package is here.
    splash.update(3, 0.75, _summarize(deps.check_python_package("faster-whisper")))
    splash.update(3, 0.85, _summarize(deps.check_python_package("sentence-transformers")))
    splash.update(4, 1.0, "Ready.")
    time.sleep(0.4)


def _summarize(status: deps.DependencyStatus) -> str:
    if status.installed:
        return f"{status.name}: OK ({status.version or 'installed'})"
    return f"{status.name}: missing"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    setup_logging()
    _ensure_runtime_dirs()
    _LOG.info("Starting %s v%s", __app_name__, __version__)

    # Allow ``python -m clipflow_studio.app.main --diagnostics`` for a CLI report.
    args = argv if argv is not None else sys.argv[1:]
    if "--diagnostics" in args or "--check" in args:
        report = deps.diagnostics_summary()
        sys.stdout.write(report)
        return 0

    try:
        splash = _Splash()
    except RuntimeError as exc:
        _LOG.error("Cannot start GUI: %s", exc)
        sys.stderr.write(f"{exc}\n")
        return 1

    try:
        _boot_sequence(splash)
    except Exception as exc:  # noqa: BLE001
        _LOG.exception("Boot sequence failed: %s", exc)
        try:
            splash.update(4, 1.0, f"Error: {exc}")
            time.sleep(2.0)
        finally:
            splash.close()
        return 1

    splash.close()

    from .ui.main_window import MainWindow  # local import: needs CustomTkinter

    window = MainWindow()
    window.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
