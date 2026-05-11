"""Main application window."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core import ffmpeg_manager

from .background_tab import BackgroundTab
from .input_tab import InputTab
from .log_tab import LogTab
from .logo_tab import LogoTab
from .lyrics_tab import LyricsTab
from .preview_tab import PreviewTab
from .render_tab import RenderTab
from .spectrum_tab import SpectrumTab
from .state import StateBus, load_state, save_state


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Music Spectrum Lyric Video Maker")
        self.resize(1280, 800)

        self.state = load_state()
        self.bus = StateBus()

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(8)
        self.setCentralWidget(container)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.input_tab = InputTab(self.state, self.bus)
        self.background_tab = BackgroundTab(self.state, self.bus)
        self.logo_tab = LogoTab(self.state, self.bus)
        self.lyrics_tab = LyricsTab(self.state, self.bus)
        self.spectrum_tab = SpectrumTab(self.state, self.bus)
        self.render_tab = RenderTab(self.state, self.bus)
        self.preview_tab = PreviewTab(self.state, self.bus)
        self.log_tab = LogTab(self.state, self.bus)

        self.tabs.addTab(self.input_tab, "Input")
        self.tabs.addTab(self.background_tab, "Background")
        self.tabs.addTab(self.logo_tab, "Logo")
        self.tabs.addTab(self.lyrics_tab, "Lyrics")
        self.tabs.addTab(self.spectrum_tab, "Spectrum")
        self.tabs.addTab(self.render_tab, "Render")
        self.tabs.addTab(self.preview_tab, "Preview")
        self.tabs.addTab(self.log_tab, "Log")

        layout.addWidget(self.tabs)

        self.render_tab.set_lyrics_provider(self.lyrics_tab.current_data)
        self.preview_tab.set_lyrics_provider(self.lyrics_tab.current_data)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("Ready")
        status.addWidget(self.status_label)
        self.ffmpeg_label = QLabel("FFmpeg: checking…")
        status.addPermanentWidget(self.ffmpeg_label)

        self.bus.state_changed.connect(self._on_state_changed)
        self.bus.ffmpeg_status_changed.connect(self._on_ffmpeg)

        # Persist state on a small debounce so tab changes don't hammer disk.
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(800)
        self._save_timer.timeout.connect(lambda: save_state(self.state))

        QTimer.singleShot(50, self.render_tab.detect_initial)

    # ------------------------------------------------------------------

    def _on_state_changed(self) -> None:
        self._save_timer.start()

    def _on_ffmpeg(self, status) -> None:
        if status.found:
            self.ffmpeg_label.setText(f"FFmpeg: {status.version}")
        else:
            self.ffmpeg_label.setText("FFmpeg: NOT INSTALLED — open Render tab")

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        save_state(self.state)
        super().closeEvent(event)
