"""Dependency Status page for the GUI.

Lists every dependency, their status, and surfaces install/repair buttons.
All long-running operations run in a background thread so the GUI never
freezes.
"""
from __future__ import annotations

import os
import threading
from typing import Callable, Dict, List, Optional

try:
    import customtkinter as ctk  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - GUI optional during tests
    ctk = None  # type: ignore[assignment]

from ..core import dependency_manager as deps
from ..utils import config as cfg
from ..utils.logger import get_logger
from .styles import DARK_PALETTE, font

_LOG = get_logger("ui.dependency")


class DependencyPage:
    """A reusable widget that contains the Dependency Status UI."""

    def __init__(self, parent, on_log: Optional[Callable[[str], None]] = None) -> None:
        if ctk is None:
            raise RuntimeError("CustomTkinter is required to build the GUI.")
        self.parent = parent
        self.on_log = on_log
        self._rows: Dict[str, Dict[str, ctk.CTkBaseClass]] = {}
        self._busy = False
        self.frame = ctk.CTkFrame(parent, fg_color=DARK_PALETTE.bg)
        self._build_layout()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self.frame, fg_color=DARK_PALETTE.bg_alt)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Dependency Status",
            font=font(22, "bold"),
            text_color=DARK_PALETTE.text,
        )
        subtitle = ctk.CTkLabel(
            header,
            text="Periksa & install komponen yang dibutuhkan ClipFlow Studio.",
            font=font(12),
            text_color=DARK_PALETTE.text_muted,
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 0))
        subtitle.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        # Action toolbar
        toolbar = ctk.CTkFrame(self.frame, fg_color=DARK_PALETTE.bg_alt)
        toolbar.grid(row=1, column=0, sticky="ew", padx=16, pady=8)
        toolbar.grid_columnconfigure(8, weight=1)

        actions = [
            ("Check All", self.check_all),
            ("Install Missing", self.install_missing),
            ("Open Tools Folder", lambda: self._open_folder(cfg.get_tools_dir())),
            ("Open Config Folder", lambda: self._open_folder(cfg.get_config_dir())),
            ("Check Deno", self.check_deno),
            ("Install Deno Online", self.install_deno),
            ("Repair Deno", self.repair_deno),
            ("Update yt-dlp", lambda: self._install_python_async("yt-dlp", upgrade=True)),
        ]
        for col, (label, cmd) in enumerate(actions):
            btn = ctk.CTkButton(
                toolbar,
                text=label,
                command=cmd,
                fg_color=DARK_PALETTE.accent,
                hover_color=DARK_PALETTE.accent_hover,
                text_color="white",
                font=font(12, "bold"),
                corner_radius=8,
                height=34,
            )
            btn.grid(row=0, column=col, padx=6, pady=8, sticky="w")

        # Scrollable table
        self.table_frame = ctk.CTkScrollableFrame(
            self.frame,
            fg_color=DARK_PALETTE.bg_alt,
            corner_radius=12,
            label_text="",
        )
        self.table_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        self.table_frame.grid_columnconfigure(0, weight=2)
        self.table_frame.grid_columnconfigure(1, weight=1)
        self.table_frame.grid_columnconfigure(2, weight=1)
        self.table_frame.grid_columnconfigure(3, weight=2)

        # Progress + status footer
        footer = ctk.CTkFrame(self.frame, fg_color=DARK_PALETTE.bg_alt)
        footer.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 16))
        footer.grid_columnconfigure(0, weight=1)
        self.progress = ctk.CTkProgressBar(footer, mode="determinate")
        self.progress.set(0)
        self.progress.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))
        self.status_label = ctk.CTkLabel(
            footer,
            text="Idle",
            font=font(12),
            text_color=DARK_PALETTE.text_muted,
        )
        self.status_label.grid(row=1, column=0, sticky="w", padx=12, pady=(4, 12))

        # Initial population
        self._render_rows([])
        self.frame.after(100, self.check_all)

    # ------------------------------------------------------------------
    # Row rendering
    # ------------------------------------------------------------------
    def _render_rows(self, statuses: List[deps.DependencyStatus]) -> None:
        for child in list(self.table_frame.winfo_children()):
            child.destroy()
        self._rows.clear()

        # Header row
        for col, label in enumerate(["Dependency", "Status", "Versi", "Detail / Aksi"]):
            ctk.CTkLabel(
                self.table_frame,
                text=label,
                font=font(12, "bold"),
                text_color=DARK_PALETTE.text_muted,
            ).grid(row=0, column=col, sticky="w", padx=12, pady=(8, 4))

        for idx, status in enumerate(statuses, start=1):
            self._render_status_row(idx, status)

    def _render_status_row(self, row: int, status: deps.DependencyStatus) -> None:
        name_lbl = ctk.CTkLabel(
            self.table_frame,
            text=status.name,
            font=font(13, "bold"),
            text_color=DARK_PALETTE.text,
            anchor="w",
            justify="left",
        )
        name_lbl.grid(row=row, column=0, sticky="w", padx=12, pady=4)

        status_color = DARK_PALETTE.success if status.installed else DARK_PALETTE.danger
        status_text = "Installed" if status.installed else "Not Installed"
        status_lbl = ctk.CTkLabel(
            self.table_frame,
            text=status_text,
            font=font(12, "bold"),
            text_color=status_color,
        )
        status_lbl.grid(row=row, column=1, sticky="w", padx=12, pady=4)

        version_lbl = ctk.CTkLabel(
            self.table_frame,
            text=status.version or "-",
            font=font(12),
            text_color=DARK_PALETTE.text_muted,
        )
        version_lbl.grid(row=row, column=2, sticky="w", padx=12, pady=4)

        actions_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        actions_frame.grid(row=row, column=3, sticky="ew", padx=4, pady=4)

        ctk.CTkButton(
            actions_frame,
            text="Check",
            width=72,
            height=28,
            command=lambda s=status: self._refresh_one(s),
            fg_color=DARK_PALETTE.surface,
            hover_color=DARK_PALETTE.sidebar_active,
            text_color=DARK_PALETTE.text,
            font=font(11),
            corner_radius=6,
        ).pack(side="left", padx=2)

        if not status.installed and status.can_install:
            ctk.CTkButton(
                actions_frame,
                text="Install / Repair",
                width=140,
                height=28,
                command=lambda s=status: self._install_one(s),
                fg_color=DARK_PALETTE.accent,
                hover_color=DARK_PALETTE.accent_hover,
                text_color="white",
                font=font(11, "bold"),
                corner_radius=6,
            ).pack(side="left", padx=2)
        elif status.installed and status.name in deps.PYTHON_PACKAGES:
            ctk.CTkButton(
                actions_frame,
                text="Update",
                width=72,
                height=28,
                command=lambda n=status.name: self._install_python_async(n, upgrade=True),
                fg_color=DARK_PALETTE.surface,
                hover_color=DARK_PALETTE.sidebar_active,
                text_color=DARK_PALETTE.text,
                font=font(11),
                corner_radius=6,
            ).pack(side="left", padx=2)

        if status.error or status.path:
            detail = status.error or status.path or ""
            if len(detail) > 80:
                detail = detail[:77] + "..."
            ctk.CTkLabel(
                actions_frame,
                text=detail,
                font=font(11),
                text_color=DARK_PALETTE.text_muted,
            ).pack(side="left", padx=8)

        self._rows[status.name] = {
            "status": status_lbl,
            "version": version_lbl,
        }

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def grid(self, **kwargs) -> None:
        self.frame.grid(**kwargs)

    def pack(self, **kwargs) -> None:
        self.frame.pack(**kwargs)

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self._busy = busy
        if message:
            self._set_status(message)

    def _set_status(self, message: str) -> None:
        if self.status_label.winfo_exists():
            self.status_label.configure(text=message)
        if self.on_log:
            self.on_log(message)

    def _set_progress(self, value: float) -> None:
        if self.progress.winfo_exists():
            self.progress.set(max(0.0, min(1.0, float(value))))

    def _progress_callback(self, message: str, fraction: float) -> None:
        self.frame.after(0, lambda: (self._set_status(message), self._set_progress(fraction)))

    # -- Background helpers ---------------------------------------------
    def _run_async(self, func: Callable[[], None]) -> None:
        if self._busy:
            self._set_status("Operasi lain sedang berjalan, mohon tunggu.")
            return
        self._set_busy(True, "Memproses ...")
        self._set_progress(0)

        def runner() -> None:
            try:
                func()
            except Exception as exc:  # noqa: BLE001
                _LOG.exception("Dependency action failed: %s", exc)
                self.frame.after(0, lambda: self._set_status(f"Error: {exc}"))
            finally:
                self.frame.after(0, lambda: self._set_busy(False, "Idle"))
                self.frame.after(0, lambda: self._set_progress(0))

        threading.Thread(target=runner, daemon=True, name="dep-action").start()

    # -- Public actions --------------------------------------------------
    def check_all(self) -> None:
        def task() -> None:
            self._progress_callback("Checking dependencies ...", 0.2)
            statuses = deps.check_all_dependencies()
            self.frame.after(0, lambda: self._render_rows(statuses))
            self._progress_callback("Selesai memeriksa dependency.", 1.0)

        self._run_async(task)

    def install_missing(self) -> None:
        def task() -> None:
            self._progress_callback("Installing missing dependencies ...", 0.05)
            report = deps.install_missing_dependencies(progress=self._progress_callback)
            text = ", ".join(f"{k}: {v}" for k, v in report.items()) or "Nothing to install."
            self.frame.after(0, lambda: self._set_status(text))
            self.frame.after(0, lambda: self._render_rows(deps.check_all_dependencies()))

        self._run_async(task)

    def check_deno(self) -> None:
        def task() -> None:
            status = deps.check_deno()
            self.frame.after(
                0,
                lambda: self._set_status(
                    f"Deno: {'installed ' + (status.version or '') if status.installed else 'not installed'}"
                ),
            )

        self._run_async(task)

    def install_deno(self) -> None:
        def task() -> None:
            self._progress_callback("Installing Deno ...", 0.1)
            ok, info = deps.install_deno_windows(progress=self._progress_callback)
            text = info if ok else f"Install Deno gagal: {info}"
            self.frame.after(0, lambda: self._set_status(text))
            self.frame.after(0, lambda: self._render_rows(deps.check_all_dependencies()))

        self._run_async(task)

    def repair_deno(self) -> None:
        def task() -> None:
            self._progress_callback("Repair Deno ...", 0.1)
            ok, info = deps.install_deno_windows(progress=self._progress_callback)
            text = info if ok else f"Repair Deno gagal: {info}"
            self.frame.after(0, lambda: self._set_status(text))
            self.frame.after(0, lambda: self._render_rows(deps.check_all_dependencies()))

        self._run_async(task)

    # -- Per-row actions -------------------------------------------------
    def _refresh_one(self, status: deps.DependencyStatus) -> None:
        # Easiest: refresh everything (cheap).
        self.check_all()

    def _install_one(self, status: deps.DependencyStatus) -> None:
        if status.name == "FFmpeg":
            self._run_async(self._install_ffmpeg_task)
        elif status.name == "Deno":
            self.install_deno()
        elif status.name in deps.PYTHON_PACKAGES:
            self._install_python_async(status.name, upgrade=False)
        elif status.name == "pip":
            self._set_status("pip biasanya sudah terpasang dengan Python. Re-install Python jika hilang.")
        else:
            self._set_status(f"Tidak ada installer otomatis untuk {status.name}.")

    def _install_ffmpeg_task(self) -> None:
        self._progress_callback("Installing FFmpeg ...", 0.1)
        ok, info = deps.download_ffmpeg_windows(progress=self._progress_callback)
        text = f"FFmpeg installed: {info}" if ok else f"Install FFmpeg gagal: {info}"
        self.frame.after(0, lambda: self._set_status(text))
        self.frame.after(0, lambda: self._render_rows(deps.check_all_dependencies()))

    def _install_python_async(self, package: str, *, upgrade: bool) -> None:
        def task() -> None:
            self._progress_callback(f"pip install {'-U ' if upgrade else ''}{package} ...", 0.1)
            ok, output = deps.install_python_package(package, upgrade=upgrade)
            text = f"{package}: OK" if ok else f"{package} gagal: {output[-200:]}"
            self.frame.after(0, lambda: self._set_status(text))
            self.frame.after(0, lambda: self._render_rows(deps.check_all_dependencies()))

        self._run_async(task)

    def _open_folder(self, path: str) -> None:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        if deps.open_folder(path):
            self._set_status(f"Folder dibuka: {path}")
        else:
            self._set_status(f"Tidak bisa membuka folder: {path}")
