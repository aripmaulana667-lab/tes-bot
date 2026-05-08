"""ClipFlow Studio main window.

The main window is intentionally fat-but-readable: it owns the sidebar, the
multiple page frames, and orchestrates the long-running pipelines (download,
transcribe, detect highlights, export) in background threads.
"""
from __future__ import annotations

import os
import threading
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional

try:
    import customtkinter as ctk  # type: ignore[import-not-found]
    from tkinter import filedialog, messagebox
except ImportError:  # pragma: no cover - GUI optional during tests
    ctk = None  # type: ignore[assignment]

from .. import __app_name__, __tagline__, __version__
from ..core import dependency_manager as deps
from ..core import export_presets as presets
from ..core.clip_generator import Clip, generate_clips, make_custom_clip
from ..core.downloader import Downloader, validate_url
from ..core.exporter import ExportSettings, export_clips
from ..core.subtitle_renderer import SubtitleStyle, style_from_dict
from ..core.transcriber import Transcriber, extract_audio, segments_to_dicts
from ..database import db
from ..utils import config as cfg
from ..utils.logger import get_logger
from .dependency_page import DependencyPage
from .styles import (
    DARK_PALETTE,
    SIDEBAR_ICONS,
    SIDEBAR_NAV,
    WINDOW_MIN_SIZE,
    WINDOW_TITLE,
    apply_default_theme,
    font,
)

_LOG = get_logger("ui.main")


# ---------------------------------------------------------------------------
# Helper widgets
# ---------------------------------------------------------------------------
def _section(parent, title: str) -> "ctk.CTkFrame":
    box = ctk.CTkFrame(parent, fg_color=DARK_PALETTE.bg_alt, corner_radius=12)
    label = ctk.CTkLabel(
        box, text=title, font=font(15, "bold"), text_color=DARK_PALETTE.text
    )
    # Use grid so callers (which always use grid for the body) can place
    # additional rows below without mixing geometry managers in the same box.
    label.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
    return box


# ---------------------------------------------------------------------------
# Main window class
# ---------------------------------------------------------------------------
class MainWindow:
    def __init__(self) -> None:
        if ctk is None:
            raise RuntimeError("CustomTkinter is required to build the GUI.")
        apply_default_theme()
        self.root = ctk.CTk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_MIN_SIZE[0]}x{WINDOW_MIN_SIZE[1]}")
        self.root.minsize(*WINDOW_MIN_SIZE)
        self.root.configure(fg_color=DARK_PALETTE.bg)

        # State
        self._busy = False
        self.current_project_id: Optional[int] = None
        self.current_video_path: Optional[str] = None
        self.current_audio_path: Optional[str] = None
        self.current_segments: List[Any] = []
        self.current_clips: List[Clip] = []
        self.clip_vars: Dict[int, ctk.BooleanVar] = {}
        self.subtitle_widgets: Dict[str, Any] = {}
        self.export_widgets: Dict[str, Any] = {}

        self._build_layout()
        self._show_page("input")
        self._refresh_history()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)

        self.sidebar = ctk.CTkFrame(self.root, width=240, fg_color=DARK_PALETTE.sidebar, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsw")
        self.sidebar.grid_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(20, 14))
        ctk.CTkLabel(
            brand_frame,
            text=f"⚡ {__app_name__}",
            font=font(18, "bold"),
            text_color=DARK_PALETTE.text,
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand_frame,
            text=__tagline__,
            font=font(11),
            text_color=DARK_PALETTE.text_muted,
        ).pack(anchor="w")

        ctk.CTkFrame(self.sidebar, fg_color=DARK_PALETTE.border, height=1).pack(fill="x", padx=14)

        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        for key, label in SIDEBAR_NAV.items():
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {SIDEBAR_ICONS.get(key, '•')}   {label}",
                anchor="w",
                command=lambda k=key: self._show_page(k),
                fg_color="transparent",
                hover_color=DARK_PALETTE.sidebar_active,
                text_color=DARK_PALETTE.text,
                font=font(13, "bold"),
                corner_radius=8,
                height=42,
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        version_lbl = ctk.CTkLabel(
            self.sidebar,
            text=f"v{__version__}",
            font=font(10),
            text_color=DARK_PALETTE.text_muted,
        )
        version_lbl.pack(side="bottom", pady=10)

        # Pages container
        self.pages_container = ctk.CTkFrame(self.root, fg_color=DARK_PALETTE.bg)
        self.pages_container.grid(row=0, column=1, sticky="nsew")
        self.pages_container.grid_columnconfigure(0, weight=1)
        self.pages_container.grid_rowconfigure(0, weight=1)

        # Status bar (progress + log)
        self.status_bar = ctk.CTkFrame(self.root, fg_color=DARK_PALETTE.bg_alt, height=86)
        self.status_bar.grid(row=1, column=1, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.status_bar.grid_propagate(False)
        self.progress = ctk.CTkProgressBar(self.status_bar)
        self.progress.set(0)
        self.progress.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready.",
            font=font(11),
            text_color=DARK_PALETTE.text_muted,
            anchor="w",
        )
        self.status_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))

        self.pages: Dict[str, ctk.CTkFrame] = {}
        self._build_input_page()
        self._build_analyze_page()
        self._build_preview_page()
        self._build_subtitle_page()
        self._build_export_page()
        self._build_dependency_page()
        self._build_history_page()

    # ------------------------------------------------------------------
    # Page: Input URL
    # ------------------------------------------------------------------
    def _build_input_page(self) -> None:
        page = ctk.CTkFrame(self.pages_container, fg_color=DARK_PALETTE.bg)
        page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            page,
            text="Input URL & Download",
            font=font(22, "bold"),
            text_color=DARK_PALETTE.text,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            page,
            text="Tempel URL YouTube yang Anda miliki haknya. ClipFlow tidak melakukan bypass DRM atau konten private.",
            font=font(12),
            text_color=DARK_PALETTE.text_muted,
            wraplength=720,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24)

        url_card = ctk.CTkFrame(page, fg_color=DARK_PALETTE.bg_alt, corner_radius=14)
        url_card.grid(row=2, column=0, sticky="ew", padx=24, pady=18)
        url_card.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_card,
            placeholder_text="https://www.youtube.com/watch?v=...",
            font=font(13),
            height=44,
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=14, pady=14)

        action_row = ctk.CTkFrame(url_card, fg_color="transparent")
        action_row.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))

        ctk.CTkButton(
            action_row,
            text="Validate URL",
            command=self._on_validate_clicked,
            fg_color=DARK_PALETTE.surface,
            hover_color=DARK_PALETTE.sidebar_active,
            text_color=DARK_PALETTE.text,
            font=font(12, "bold"),
            height=36,
            corner_radius=8,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            action_row,
            text="Download Video",
            command=self._on_download_clicked,
            fg_color=DARK_PALETTE.accent,
            hover_color=DARK_PALETTE.accent_hover,
            text_color="white",
            font=font(12, "bold"),
            height=36,
            corner_radius=8,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            action_row,
            text="Use Local File ...",
            command=self._on_load_local_clicked,
            fg_color=DARK_PALETTE.surface,
            hover_color=DARK_PALETTE.sidebar_active,
            text_color=DARK_PALETTE.text,
            font=font(12, "bold"),
            height=36,
            corner_radius=8,
        ).pack(side="left", padx=(0, 8))

        # Log box
        log_card = _section(page, "Log Proses")
        log_card.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 18))
        page.grid_rowconfigure(3, weight=1)
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)
        self.input_log = ctk.CTkTextbox(
            log_card,
            font=font(11),
            fg_color=DARK_PALETTE.bg,
            text_color=DARK_PALETTE.text,
            wrap="word",
        )
        self.input_log.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.input_log.configure(state="disabled")

        self.pages["input"] = page

    # ------------------------------------------------------------------
    # Page: Analyze
    # ------------------------------------------------------------------
    def _build_analyze_page(self) -> None:
        page = ctk.CTkFrame(self.pages_container, fg_color=DARK_PALETTE.bg)
        page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            page,
            text="Analyze Clips",
            font=font(22, "bold"),
            text_color=DARK_PALETTE.text,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            page,
            text="Transkripsi audio dengan faster-whisper, lalu temukan highlight terbaik.",
            font=font(12),
            text_color=DARK_PALETTE.text_muted,
        ).grid(row=1, column=0, sticky="w", padx=24)

        controls = ctk.CTkFrame(page, fg_color=DARK_PALETTE.bg_alt, corner_radius=14)
        controls.grid(row=2, column=0, sticky="ew", padx=24, pady=18)
        controls.grid_columnconfigure(6, weight=1)

        ctk.CTkLabel(controls, text="Whisper model", text_color=DARK_PALETTE.text_muted, font=font(11)).grid(
            row=0, column=0, padx=(14, 6), pady=14, sticky="w"
        )
        self.whisper_model_var = ctk.StringVar(value=cfg.get("whisper_model", "base"))
        ctk.CTkOptionMenu(
            controls,
            values=["tiny", "base", "small", "medium", "large-v3"],
            variable=self.whisper_model_var,
            width=120,
        ).grid(row=0, column=1, padx=(0, 14), pady=14)

        ctk.CTkLabel(controls, text="Top-K clips", text_color=DARK_PALETTE.text_muted, font=font(11)).grid(
            row=0, column=2, padx=(0, 6), pady=14, sticky="w"
        )
        self.top_k_var = ctk.StringVar(value=str(cfg.get("highlight_top_k", 5)))
        ctk.CTkOptionMenu(
            controls,
            values=["3", "4", "5", "6", "8", "10"],
            variable=self.top_k_var,
            width=80,
        ).grid(row=0, column=3, padx=(0, 14), pady=14)

        ctk.CTkLabel(controls, text="Custom duration (s)", text_color=DARK_PALETTE.text_muted, font=font(11)).grid(
            row=0, column=4, padx=(0, 6), pady=14, sticky="w"
        )
        self.custom_duration_entry = ctk.CTkEntry(controls, width=80, placeholder_text="-")
        self.custom_duration_entry.grid(row=0, column=5, padx=(0, 14), pady=14)

        ctk.CTkButton(
            controls,
            text="Generate Clips",
            command=self._on_generate_clicked,
            fg_color=DARK_PALETTE.accent,
            hover_color=DARK_PALETTE.accent_hover,
            text_color="white",
            font=font(12, "bold"),
            corner_radius=8,
            height=36,
        ).grid(row=0, column=7, padx=14, pady=14, sticky="e")

        log_card = _section(page, "Log Analisis")
        log_card.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 18))
        page.grid_rowconfigure(3, weight=1)
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)
        self.analyze_log = ctk.CTkTextbox(
            log_card,
            font=font(11),
            fg_color=DARK_PALETTE.bg,
            text_color=DARK_PALETTE.text,
            wrap="word",
        )
        self.analyze_log.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.analyze_log.configure(state="disabled")

        self.pages["analyze"] = page

    # ------------------------------------------------------------------
    # Page: Preview / Select
    # ------------------------------------------------------------------
    def _build_preview_page(self) -> None:
        page = ctk.CTkFrame(self.pages_container, fg_color=DARK_PALETTE.bg)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            page,
            text="Preview & Select Clips",
            font=font(22, "bold"),
            text_color=DARK_PALETTE.text,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            page,
            text="Pilih clip yang ingin diekspor. Skor di atas mencerminkan tingkat kemenarikan otomatis.",
            font=font(12),
            text_color=DARK_PALETTE.text_muted,
        ).grid(row=1, column=0, sticky="w", padx=24)

        self.clip_list_frame = ctk.CTkScrollableFrame(
            page,
            fg_color=DARK_PALETTE.bg_alt,
            corner_radius=12,
            label_text="",
        )
        self.clip_list_frame.grid(row=2, column=0, sticky="nsew", padx=24, pady=14)
        self.clip_list_frame.grid_columnconfigure(0, weight=1)

        action_row = ctk.CTkFrame(page, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="e", padx=24, pady=(0, 18))

        ctk.CTkButton(
            action_row,
            text="Select All",
            command=lambda: self._toggle_all(True),
            fg_color=DARK_PALETTE.surface,
            hover_color=DARK_PALETTE.sidebar_active,
            text_color=DARK_PALETTE.text,
            font=font(12, "bold"),
            corner_radius=8,
            height=34,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            action_row,
            text="Clear",
            command=lambda: self._toggle_all(False),
            fg_color=DARK_PALETTE.surface,
            hover_color=DARK_PALETTE.sidebar_active,
            text_color=DARK_PALETTE.text,
            font=font(12, "bold"),
            corner_radius=8,
            height=34,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            action_row,
            text="Export Selected Clips",
            command=lambda: self._show_page("export"),
            fg_color=DARK_PALETTE.accent,
            hover_color=DARK_PALETTE.accent_hover,
            text_color="white",
            font=font(12, "bold"),
            corner_radius=8,
            height=36,
        ).pack(side="left", padx=4)

        self.pages["preview"] = page

    # ------------------------------------------------------------------
    # Page: Subtitle Settings
    # ------------------------------------------------------------------
    def _build_subtitle_page(self) -> None:
        page = ctk.CTkFrame(self.pages_container, fg_color=DARK_PALETTE.bg)
        page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            page,
            text="Subtitle Settings",
            font=font(22, "bold"),
            text_color=DARK_PALETTE.text,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            page,
            text="Atur tampilan subtitle khas clipper: huruf besar, outline tebal, highlight kata penting.",
            font=font(12),
            text_color=DARK_PALETTE.text_muted,
        ).grid(row=1, column=0, sticky="w", padx=24)

        form = ctk.CTkFrame(page, fg_color=DARK_PALETTE.bg_alt, corner_radius=14)
        form.grid(row=2, column=0, sticky="ew", padx=24, pady=18)
        for col in range(4):
            form.grid_columnconfigure(col, weight=1)

        def _add_dropdown(row: int, col: int, label: str, key: str, values: list, default: str) -> None:
            ctk.CTkLabel(form, text=label, font=font(11), text_color=DARK_PALETTE.text_muted).grid(
                row=row, column=col, padx=14, pady=(14, 0), sticky="w"
            )
            var = ctk.StringVar(value=str(cfg.get(key, default)))
            self.subtitle_widgets[key] = var
            ctk.CTkOptionMenu(form, values=[str(v) for v in values], variable=var).grid(
                row=row + 1, column=col, padx=14, pady=(2, 12), sticky="ew"
            )

        def _add_entry(row: int, col: int, label: str, key: str, default: str) -> None:
            ctk.CTkLabel(form, text=label, font=font(11), text_color=DARK_PALETTE.text_muted).grid(
                row=row, column=col, padx=14, pady=(14, 0), sticky="w"
            )
            entry = ctk.CTkEntry(form)
            entry.insert(0, str(cfg.get(key, default)))
            self.subtitle_widgets[key] = entry
            entry.grid(row=row + 1, column=col, padx=14, pady=(2, 12), sticky="ew")

        _add_entry(0, 0, "Font", "subtitle_font", "Arial")
        _add_dropdown(0, 1, "Font size", "subtitle_font_size", [40, 48, 56, 64, 72, 80, 96], "64")
        _add_dropdown(
            0, 2, "Position", "subtitle_position",
            ["bottom-center", "center", "top-center", "bottom-left", "bottom-right"],
            "bottom-center",
        )
        _add_dropdown(0, 3, "Highlight color", "subtitle_highlight_color",
                      ["yellow", "white", "orange", "pink", "red", "green", "blue"], "yellow")

        _add_dropdown(2, 0, "Primary color", "subtitle_color",
                      ["white", "yellow", "orange", "pink", "red", "blue"], "white")
        _add_dropdown(2, 1, "Outline color", "subtitle_outline_color",
                      ["black", "white", "blue", "red"], "black")
        _add_dropdown(2, 2, "Outline width", "subtitle_outline_width", [2, 3, 4, 5, 6, 8], "4")

        animate_var = ctk.BooleanVar(value=bool(cfg.get("subtitle_animate", True)))
        self.subtitle_widgets["subtitle_animate"] = animate_var
        ctk.CTkSwitch(
            form,
            text="Animasi fade-in/out",
            variable=animate_var,
        ).grid(row=3, column=3, padx=14, pady=14, sticky="w")

        ctk.CTkButton(
            form,
            text="Save Subtitle Settings",
            command=self._on_save_subtitle_settings,
            fg_color=DARK_PALETTE.accent,
            hover_color=DARK_PALETTE.accent_hover,
            text_color="white",
            font=font(12, "bold"),
            corner_radius=8,
            height=36,
        ).grid(row=4, column=0, columnspan=4, padx=14, pady=(4, 14), sticky="ew")

        self.pages["subtitle"] = page

    # ------------------------------------------------------------------
    # Page: Export Settings
    # ------------------------------------------------------------------
    def _build_export_page(self) -> None:
        page = ctk.CTkFrame(self.pages_container, fg_color=DARK_PALETTE.bg)
        page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            page,
            text="Export Settings",
            font=font(22, "bold"),
            text_color=DARK_PALETTE.text,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            page,
            text="Pilih platform, resolusi, FPS, crop mode, dan kualitas akhir.",
            font=font(12),
            text_color=DARK_PALETTE.text_muted,
        ).grid(row=1, column=0, sticky="w", padx=24)

        form = ctk.CTkFrame(page, fg_color=DARK_PALETTE.bg_alt, corner_radius=14)
        form.grid(row=2, column=0, sticky="ew", padx=24, pady=18)
        for col in range(4):
            form.grid_columnconfigure(col, weight=1)

        def _label(row: int, col: int, text: str) -> None:
            ctk.CTkLabel(form, text=text, font=font(11), text_color=DARK_PALETTE.text_muted).grid(
                row=row, column=col, padx=14, pady=(14, 0), sticky="w"
            )

        def _menu(row: int, col: int, key: str, values: List[str], default: str):
            var = ctk.StringVar(value=str(cfg.get(f"default_{key}", default)))
            self.export_widgets[key] = var
            menu = ctk.CTkOptionMenu(form, values=values, variable=var)
            menu.grid(row=row + 1, column=col, padx=14, pady=(2, 12), sticky="ew")
            return var, menu

        _label(0, 0, "Platform")
        platform_var, platform_menu = _menu(
            0, 0, "platform", ["tiktok", "reels", "shorts", "custom"], "tiktok"
        )
        _label(0, 1, "Aspect Ratio")
        aspect_var, _ = _menu(0, 1, "aspect_ratio", presets.list_aspect_ratios(), "9:16")
        _label(0, 2, "Resolution")
        resolution_var = ctk.StringVar(value=cfg.get("default_resolution", "1080x1920"))
        self.export_widgets["resolution"] = resolution_var
        resolution_menu = ctk.CTkOptionMenu(
            form,
            values=[r.value for r in presets.list_resolutions(aspect_var.get())],
            variable=resolution_var,
        )
        resolution_menu.grid(row=1, column=2, padx=14, pady=(2, 12), sticky="ew")
        _label(0, 3, "FPS")
        _menu(0, 3, "fps", ["original", "24", "30", "48", "60"], "original")

        _label(2, 0, "Crop Mode")
        _menu(2, 0, "crop_mode", list(presets.list_crop_modes()), "center")
        _label(2, 1, "Quality")
        _menu(2, 1, "quality", presets.list_quality_presets(), "high")
        _label(2, 2, "Codec")
        _menu(2, 2, "codec", presets.list_codecs(), "h264")

        burn_var = ctk.BooleanVar(value=True)
        self.export_widgets["burn_subtitles"] = burn_var
        ctk.CTkSwitch(
            form,
            text="Burn subtitle ke video",
            variable=burn_var,
        ).grid(row=3, column=3, padx=14, pady=14, sticky="w")

        def _on_aspect_change(_value: str = "") -> None:
            choices = [r.value for r in presets.list_resolutions(aspect_var.get())]
            resolution_menu.configure(values=choices)
            if choices:
                resolution_var.set(choices[1] if len(choices) > 1 else choices[0])

        aspect_var.trace_add("write", lambda *_args: _on_aspect_change())

        def _on_platform_change(_value: str = "") -> None:
            preset = presets.get_platform(platform_var.get())
            aspect_var.set(preset.aspect_ratio)
            _on_aspect_change()
            resolution_var.set(preset.default_resolution.value)

        platform_var.trace_add("write", lambda *_args: _on_platform_change())

        ctk.CTkButton(
            form,
            text="Export Selected Clips",
            command=self._on_export_clicked,
            fg_color=DARK_PALETTE.accent,
            hover_color=DARK_PALETTE.accent_hover,
            text_color="white",
            font=font(12, "bold"),
            corner_radius=8,
            height=40,
        ).grid(row=4, column=0, columnspan=4, padx=14, pady=14, sticky="ew")

        self.pages["export"] = page

    # ------------------------------------------------------------------
    # Page: Dependency Status
    # ------------------------------------------------------------------
    def _build_dependency_page(self) -> None:
        page = ctk.CTkFrame(self.pages_container, fg_color=DARK_PALETTE.bg)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        self.dependency_page = DependencyPage(page, on_log=self._set_status)
        self.dependency_page.frame.grid(row=0, column=0, sticky="nsew")
        self.pages["dependency"] = page

    # ------------------------------------------------------------------
    # Page: History
    # ------------------------------------------------------------------
    def _build_history_page(self) -> None:
        page = ctk.CTkFrame(self.pages_container, fg_color=DARK_PALETTE.bg)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            page,
            text="History",
            font=font(22, "bold"),
            text_color=DARK_PALETTE.text,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            page,
            text="Riwayat project tersimpan di SQLite.",
            font=font(12),
            text_color=DARK_PALETTE.text_muted,
        ).grid(row=1, column=0, sticky="w", padx=24)

        self.history_frame = ctk.CTkScrollableFrame(
            page,
            fg_color=DARK_PALETTE.bg_alt,
            corner_radius=12,
            label_text="",
        )
        self.history_frame.grid(row=2, column=0, sticky="nsew", padx=24, pady=14)
        self.history_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            page,
            text="Refresh History",
            command=self._refresh_history,
            fg_color=DARK_PALETTE.accent,
            hover_color=DARK_PALETTE.accent_hover,
            text_color="white",
            font=font(12, "bold"),
            corner_radius=8,
            height=34,
        ).grid(row=3, column=0, sticky="e", padx=24, pady=(0, 18))

        self.pages["history"] = page

    # ------------------------------------------------------------------
    # Page navigation
    # ------------------------------------------------------------------
    def _show_page(self, key: str) -> None:
        for name, page in self.pages.items():
            if name == key:
                page.grid(row=0, column=0, sticky="nsew")
            else:
                page.grid_forget()
        for name, button in self.nav_buttons.items():
            if name == key:
                button.configure(fg_color=DARK_PALETTE.sidebar_active)
            else:
                button.configure(fg_color="transparent")
        if key == "history":
            self._refresh_history()
        if key == "preview":
            self._render_clip_list()

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def _append_log(self, textbox: "ctk.CTkTextbox", message: str) -> None:
        textbox.configure(state="normal")
        textbox.insert("end", message + "\n")
        textbox.see("end")
        textbox.configure(state="disabled")

    def _set_status(self, message: str) -> None:
        if self.status_label.winfo_exists():
            self.status_label.configure(text=message)

    def _set_progress(self, value: float) -> None:
        if self.progress.winfo_exists():
            self.progress.set(max(0.0, min(1.0, float(value))))

    def _ui_progress(self, message: str, fraction: float) -> None:
        self.root.after(0, lambda: (self._set_status(message), self._set_progress(fraction)))

    def _ui_log(self, target: "ctk.CTkTextbox", message: str) -> None:
        self.root.after(0, lambda: self._append_log(target, message))

    # ------------------------------------------------------------------
    # Background thread plumbing
    # ------------------------------------------------------------------
    def _run_background(self, fn: Callable[[], None], name: str = "bg") -> None:
        if self._busy:
            messagebox.showinfo(__app_name__, "Operasi lain sedang berjalan, mohon tunggu.")
            return
        self._busy = True
        self._set_progress(0)

        def runner() -> None:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                _LOG.exception("Background task failed: %s", exc)
                self.root.after(0, lambda: self._set_status(f"Error: {exc}"))
                self.root.after(
                    0, lambda: messagebox.showerror(__app_name__, f"Operasi gagal:\n{exc}")
                )
            finally:
                self._busy = False
                self.root.after(0, lambda: self._set_progress(0))

        threading.Thread(target=runner, daemon=True, name=name).start()

    # ------------------------------------------------------------------
    # Validate / Download
    # ------------------------------------------------------------------
    def _on_validate_clicked(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showinfo(__app_name__, "Masukkan URL terlebih dahulu.")
            return

        def task() -> None:
            self._ui_progress("Memvalidasi URL ...", 0.2)
            result = validate_url(url)
            source = result.get("source", "python")
            if result.get("valid"):
                self._ui_progress(f"URL valid (via {source}).", 1.0)
                self._ui_log(self.input_log, f"[OK] URL valid (via {source}): {url}")
            else:
                self._ui_progress(
                    f"URL tidak valid: {result.get('error')} (via {source})", 1.0
                )
                self._ui_log(
                    self.input_log,
                    f"[ERR] URL tidak valid: {result.get('error')} (via {source})",
                )

        self._run_background(task, "validate")

    def _on_download_clicked(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showinfo(__app_name__, "Masukkan URL terlebih dahulu.")
            return
        if not deps.get_ffmpeg_path():
            if not messagebox.askyesno(
                __app_name__,
                "FFmpeg belum terinstall. Download tetap dilanjutkan tetapi merge format mungkin gagal.\nLanjutkan?",
            ):
                return

        def update_question() -> bool:
            answer: List[bool] = []
            evt = threading.Event()

            def ask() -> None:
                answer.append(
                    messagebox.askyesno(
                        __app_name__,
                        "Download gagal. Update yt-dlp dan coba lagi?",
                    )
                )
                evt.set()

            self.root.after(0, ask)
            evt.wait()
            return bool(answer and answer[0])

        def task() -> None:
            self._ui_progress("Memvalidasi URL ...", 0.05)
            self._ui_log(self.input_log, f"Memulai download: {url}")
            downloader = Downloader()
            result = downloader.download(
                url,
                progress=self._ui_progress,
                on_update_question=update_question,
            )
            if result.success and result.video_path:
                self.current_video_path = result.video_path
                project_id = db.add_project(
                    url=url,
                    title=result.title,
                    video_path=result.video_path,
                    duration=result.duration,
                    metadata=result.metadata,
                )
                self.current_project_id = project_id
                self._ui_log(self.input_log, f"[OK] Saved to {result.video_path}")
                self._ui_progress(f"Download selesai: {result.title or result.video_path}", 1.0)
            else:
                self._ui_log(self.input_log, f"[ERR] {result.error}")
                if result.metadata:
                    self._ui_log(self.input_log, f"Metadata fallback: {result.metadata}")
                self._ui_progress(f"Download gagal: {result.error}", 0)

        self._run_background(task, "download")

    def _on_load_local_clicked(self) -> None:
        path = filedialog.askopenfilename(
            title="Pilih video",
            filetypes=[("Video", "*.mp4 *.mkv *.mov *.webm"), ("Semua file", "*.*")],
        )
        if not path:
            return
        self.current_video_path = path
        title = os.path.basename(path)
        project_id = db.add_project(
            url=path,
            title=title,
            video_path=path,
        )
        self.current_project_id = project_id
        self._append_log(self.input_log, f"[OK] Memakai file lokal: {path}")
        self._set_status(f"Video lokal siap dianalisis: {title}")

    # ------------------------------------------------------------------
    # Analyze
    # ------------------------------------------------------------------
    def _on_generate_clicked(self) -> None:
        if not self.current_video_path or not os.path.exists(self.current_video_path):
            messagebox.showinfo(__app_name__, "Belum ada video yang siap dianalisis.")
            return

        try:
            top_k = int(self.top_k_var.get())
        except ValueError:
            top_k = 5
        try:
            custom_duration_text = self.custom_duration_entry.get().strip()
            custom_duration = int(custom_duration_text) if custom_duration_text else None
        except ValueError:
            custom_duration = None

        whisper_model = self.whisper_model_var.get()
        cfg.set_value("whisper_model", whisper_model)
        cfg.set_value("highlight_top_k", top_k)

        def task() -> None:
            self._ui_progress("Mengekstrak audio ...", 0.05)
            self._ui_log(self.analyze_log, "Mengekstrak audio dengan FFmpeg ...")
            audio_path = extract_audio(self.current_video_path)
            self.current_audio_path = audio_path
            self._ui_log(self.analyze_log, f"Audio: {audio_path}")

            self._ui_progress("Mentranskrip audio (faster-whisper) ...", 0.2)
            transcriber = Transcriber(model_name=whisper_model)
            result = transcriber.transcribe(audio_path, progress=self._ui_progress)
            self.current_segments = result.segments
            self._ui_log(self.analyze_log, f"Bahasa: {result.language}, segmen: {len(result.segments)}")

            self._ui_progress("Mendeteksi highlight ...", 0.7)
            clips = generate_clips(
                result.segments,
                top_k=top_k,
                custom_duration=custom_duration,
            )
            self.current_clips = clips
            for clip in clips:
                clip.selected = True
                self._ui_log(
                    self.analyze_log,
                    f"  Clip {clip.index + 1}: {clip.start:.1f}-{clip.end:.1f}s "
                    f"(score {clip.score:.2f}, {','.join(clip.reasons)})",
                )
            if self.current_project_id:
                db.update_project(
                    self.current_project_id,
                    audio_path=audio_path,
                    duration=result.duration,
                    metadata={
                        "language": result.language,
                        "segments": segments_to_dicts(result.segments)[:200],
                        "highlights": [c.to_dict() for c in clips],
                    },
                )
                for clip in clips:
                    clip.db_id = db.add_clip(
                        project_id=self.current_project_id,
                        start_time=clip.start,
                        end_time=clip.end,
                        score=clip.score,
                        transcript=clip.transcript,
                        duration_preset=clip.duration_preset,
                        metadata={"reasons": clip.reasons},
                    )
            self._ui_progress(f"Selesai: {len(clips)} clip ditemukan.", 1.0)
            self.root.after(0, self._render_clip_list)
            self.root.after(0, lambda: self._show_page("preview"))

        self._run_background(task, "analyze")

    # ------------------------------------------------------------------
    # Preview / Selection
    # ------------------------------------------------------------------
    def _render_clip_list(self) -> None:
        for child in list(self.clip_list_frame.winfo_children()):
            child.destroy()
        self.clip_vars.clear()
        if not self.current_clips:
            ctk.CTkLabel(
                self.clip_list_frame,
                text="Belum ada clip. Jalankan analisis terlebih dahulu.",
                font=font(12),
                text_color=DARK_PALETTE.text_muted,
            ).grid(row=0, column=0, padx=20, pady=20, sticky="w")
            return
        for idx, clip in enumerate(self.current_clips):
            card = ctk.CTkFrame(self.clip_list_frame, fg_color=DARK_PALETTE.surface, corner_radius=10)
            card.grid(row=idx, column=0, sticky="ew", padx=8, pady=6)
            card.grid_columnconfigure(1, weight=1)

            var = ctk.BooleanVar(value=clip.selected)
            self.clip_vars[clip.index] = var
            cb = ctk.CTkCheckBox(card, text="", variable=var, command=lambda c=clip, v=var: setattr(c, "selected", v.get()))
            cb.grid(row=0, column=0, padx=12, pady=12)

            header = ctk.CTkLabel(
                card,
                text=(
                    f"Clip {clip.index + 1}  ·  {clip.start:.1f}s → {clip.end:.1f}s  "
                    f"·  durasi {clip.end - clip.start:.1f}s  ·  skor {clip.score:.2f}"
                ),
                font=font(13, "bold"),
                text_color=DARK_PALETTE.text,
                anchor="w",
            )
            header.grid(row=0, column=1, sticky="w", padx=10, pady=(12, 0))

            reasons = ", ".join(clip.reasons) or "n/a"
            sub = ctk.CTkLabel(
                card,
                text=f"Reason: {reasons}",
                font=font(11),
                text_color=DARK_PALETTE.text_muted,
                anchor="w",
            )
            sub.grid(row=1, column=1, sticky="w", padx=10)

            preview = clip.transcript
            if len(preview) > 320:
                preview = preview[:317] + "..."
            ctk.CTkLabel(
                card,
                text=preview,
                font=font(11),
                text_color=DARK_PALETTE.text_muted,
                anchor="w",
                wraplength=900,
                justify="left",
            ).grid(row=2, column=1, sticky="w", padx=10, pady=(2, 12))

    def _toggle_all(self, value: bool) -> None:
        for clip in self.current_clips:
            clip.selected = value
        for var in self.clip_vars.values():
            var.set(value)

    # ------------------------------------------------------------------
    # Subtitle / Export actions
    # ------------------------------------------------------------------
    def _on_save_subtitle_settings(self) -> None:
        updates: Dict[str, Any] = {}
        for key, widget in self.subtitle_widgets.items():
            if isinstance(widget, ctk.StringVar):
                updates[key] = self._coerce(widget.get())
            elif isinstance(widget, ctk.BooleanVar):
                updates[key] = bool(widget.get())
            else:  # CTkEntry
                updates[key] = self._coerce(widget.get())
        cfg.update(updates)
        self._set_status("Subtitle settings tersimpan.")

    def _on_export_clicked(self) -> None:
        selected = [c for c in self.current_clips if c.selected]
        if not selected:
            messagebox.showinfo(__app_name__, "Pilih minimal satu clip terlebih dahulu.")
            return
        if not self.current_video_path:
            messagebox.showinfo(__app_name__, "Belum ada video sumber yang dimuat.")
            return
        if not deps.get_ffmpeg_path():
            messagebox.showwarning(
                __app_name__,
                "FFmpeg belum terinstall. Buka Dependency Status untuk install otomatis.",
            )
            return

        settings = ExportSettings(
            platform=self._get_export_value("platform", "tiktok"),
            aspect_ratio=self._get_export_value("aspect_ratio", "9:16"),
            resolution=self._get_export_value("resolution", "1080x1920"),
            fps=self._get_export_value("fps", "original"),
            crop_mode=self._get_export_value("crop_mode", "center"),
            quality=self._get_export_value("quality", "high"),
            codec=self._get_export_value("codec", "h264"),
            burn_subtitles=bool(self.export_widgets.get("burn_subtitles").get())
            if "burn_subtitles" in self.export_widgets
            else True,
        )
        cfg.update({f"default_{k}": v for k, v in asdict(settings).items() if isinstance(v, str)})
        style = style_from_dict({k: self._coerce(v.get() if hasattr(v, "get") else v)
                                 for k, v in self.subtitle_widgets.items()})

        def task() -> None:
            self._ui_progress("Memulai export ...", 0.05)
            results = export_clips(
                source_video=self.current_video_path,
                clips=selected,
                settings=settings,
                project_id=self.current_project_id or 0,
                output_dir=cfg.get_outputs_dir(),
                subtitle_style=style,
                progress=self._ui_progress,
            )
            success = sum(1 for r in results if r.success)
            failed = sum(1 for r in results if not r.success)
            for clip, result in zip(selected, results):
                if (
                    result.success
                    and result.output_path
                    and self.current_project_id
                    and clip.db_id is not None
                ):
                    db.mark_clip_exported(clip.db_id, result.output_path)
            self._ui_progress(
                f"Export selesai: {success} OK, {failed} gagal.",
                1.0,
            )
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    __app_name__,
                    f"Export selesai. {success} berhasil, {failed} gagal.\nLokasi: {cfg.get_outputs_dir()}",
                ),
            )

        self._run_background(task, "export")

    def _get_export_value(self, key: str, default: str) -> str:
        widget = self.export_widgets.get(key)
        if widget is None:
            return default
        try:
            return str(widget.get())
        except Exception:  # noqa: BLE001
            return default

    @staticmethod
    def _coerce(value: Any) -> Any:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.lower() in {"true", "false"}:
                return stripped.lower() == "true"
            try:
                return int(stripped)
            except ValueError:
                pass
        return value

    # ------------------------------------------------------------------
    # History page
    # ------------------------------------------------------------------
    def _refresh_history(self) -> None:
        for child in list(self.history_frame.winfo_children()):
            child.destroy()
        try:
            projects = db.list_projects(limit=50)
        except Exception as exc:  # noqa: BLE001
            ctk.CTkLabel(
                self.history_frame,
                text=f"DB error: {exc}",
                text_color=DARK_PALETTE.danger,
            ).grid(row=0, column=0, padx=20, pady=20)
            return
        if not projects:
            ctk.CTkLabel(
                self.history_frame,
                text="Belum ada project. Mulai dari halaman Input URL.",
                text_color=DARK_PALETTE.text_muted,
            ).grid(row=0, column=0, padx=20, pady=20, sticky="w")
            return
        for idx, project in enumerate(projects):
            card = ctk.CTkFrame(self.history_frame, fg_color=DARK_PALETTE.surface, corner_radius=10)
            card.grid(row=idx, column=0, sticky="ew", padx=8, pady=6)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                card,
                text=f"#{project['id']} · {project.get('title') or project.get('url')}",
                font=font(13, "bold"),
                text_color=DARK_PALETTE.text,
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 0))
            ctk.CTkLabel(
                card,
                text=f"{project.get('url')}",
                font=font(11),
                text_color=DARK_PALETTE.text_muted,
                anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 12))

    # ------------------------------------------------------------------
    # Mainloop
    # ------------------------------------------------------------------
    def run(self) -> None:
        self.root.mainloop()
