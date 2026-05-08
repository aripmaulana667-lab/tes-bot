"""Centralized styling constants and helpers for the CustomTkinter UI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Palette:
    bg: str
    bg_alt: str
    sidebar: str
    sidebar_active: str
    surface: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    success: str
    danger: str
    warning: str


DARK_PALETTE = Palette(
    bg="#0f1115",
    bg_alt="#151820",
    sidebar="#0c0e13",
    sidebar_active="#1f2937",
    surface="#1a1d24",
    border="#252a33",
    text="#e6e8ee",
    text_muted="#8a92a3",
    accent="#5b8def",
    accent_hover="#3f6fdc",
    success="#4ade80",
    danger="#ef4444",
    warning="#facc15",
)


SIDEBAR_NAV: Dict[str, str] = {
    "input": "Input URL",
    "analyze": "Analyze Clips",
    "preview": "Preview Clips",
    "subtitle": "Subtitle Settings",
    "export": "Export Settings",
    "dependency": "Dependency Status",
    "history": "History",
}


# Sidebar icon glyphs (text-based to avoid bundling images).
SIDEBAR_ICONS: Dict[str, str] = {
    "input": "🎬",
    "analyze": "🧠",
    "preview": "🎞️",
    "subtitle": "✦",
    "export": "⬆",
    "dependency": "⚙",
    "history": "🕒",
}


WINDOW_TITLE = "ClipFlow Studio - AI Smart Video Clipper"
WINDOW_MIN_SIZE = (1180, 760)


def apply_default_theme() -> None:
    """Switch CustomTkinter to dark mode + blue accent."""
    try:
        import customtkinter as ctk  # type: ignore[import-not-found]

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
    except ImportError:
        # CustomTkinter not installed yet; we still allow the rest of the
        # codebase to import.
        pass


def font(size: int = 13, weight: str = "normal", family: str = "Segoe UI") -> tuple:
    return (family, size, weight)
