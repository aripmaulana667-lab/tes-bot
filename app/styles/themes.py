"""Application theming.

The look is a clean, professional "light editor" feel:
- White-ish surfaces, soft grey separators, a single accent color.
- The user can opt to follow the Windows system theme; on Windows we read the
  AppsUseLightTheme registry key (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\
  Themes\\Personalize) to detect dark mode.
"""
from __future__ import annotations

import platform
from pathlib import Path

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication


QSS_PATH = Path(__file__).with_name("app.qss")


def detect_windows_dark() -> bool:
    """Return True if Windows is currently using a dark theme."""
    if platform.system() != "Windows":
        return False
    try:  # pragma: no cover - Windows only
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False


def _light_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor("#F7F8FA"))
    p.setColor(QPalette.WindowText, QColor("#0F172A"))
    p.setColor(QPalette.Base, QColor("#FFFFFF"))
    p.setColor(QPalette.AlternateBase, QColor("#F1F5F9"))
    p.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
    p.setColor(QPalette.ToolTipText, QColor("#0F172A"))
    p.setColor(QPalette.Text, QColor("#0F172A"))
    p.setColor(QPalette.Button, QColor("#FFFFFF"))
    p.setColor(QPalette.ButtonText, QColor("#0F172A"))
    p.setColor(QPalette.BrightText, QColor("#EF4444"))
    p.setColor(QPalette.Highlight, QColor("#3B82F6"))
    p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    return p


def _dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor("#0F172A"))
    p.setColor(QPalette.WindowText, QColor("#E5E7EB"))
    p.setColor(QPalette.Base, QColor("#111827"))
    p.setColor(QPalette.AlternateBase, QColor("#1F2937"))
    p.setColor(QPalette.ToolTipBase, QColor("#1F2937"))
    p.setColor(QPalette.ToolTipText, QColor("#E5E7EB"))
    p.setColor(QPalette.Text, QColor("#E5E7EB"))
    p.setColor(QPalette.Button, QColor("#1F2937"))
    p.setColor(QPalette.ButtonText, QColor("#E5E7EB"))
    p.setColor(QPalette.BrightText, QColor("#F87171"))
    p.setColor(QPalette.Highlight, QColor("#3B82F6"))
    p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    return p


def apply_theme(app: QApplication, mode: str = "auto") -> str:
    """Apply theme and return the resolved mode ("light" or "dark")."""
    if mode == "auto":
        resolved = "dark" if detect_windows_dark() else "light"
    else:
        resolved = mode

    app.setStyle("Fusion")
    app.setPalette(_dark_palette() if resolved == "dark" else _light_palette())

    if QSS_PATH.exists():
        try:
            qss = QSS_PATH.read_text(encoding="utf-8")
            app.setStyleSheet(qss)
        except OSError:
            pass

    return resolved
