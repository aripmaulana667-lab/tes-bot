"""Log/console tab."""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .state import AppState, StateBus
from .widgets import Card


class LogTab(QWidget):
    def __init__(self, state: AppState, bus: StateBus, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state = state
        self.bus = bus

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(14)

        card = Card("Log / Console")
        self.view = QPlainTextEdit()
        self.view.setObjectName("LogView")
        self.view.setReadOnly(True)
        card.addWidget(self.view)

        btns = QHBoxLayout()
        clear = QPushButton("Clear")
        clear.clicked.connect(self.view.clear)
        btns.addWidget(clear)
        save = QPushButton("Save log…")
        save.clicked.connect(self._save_log)
        btns.addWidget(save)
        open_out = QPushButton("Open output folder")
        open_out.clicked.connect(self._open_output)
        btns.addWidget(open_out)
        btns.addStretch(1)
        card.addLayout(btns)

        outer.addWidget(card, 1)

        bus.log_emitted.connect(self.append)
        self.append(f"[{_ts()}] Music Spectrum Lyric Video Maker ready.")

    def append(self, line: str) -> None:
        if not line:
            return
        self.view.appendPlainText(f"[{_ts()}] {line}")

    def _save_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save log", str(Path(self.state.output_dir) / "render.log"), "Log files (*.log *.txt)"
        )
        if not path:
            return
        Path(path).write_text(self.view.toPlainText(), encoding="utf-8")
        self.append(f"Log saved to {path}")

    def _open_output(self) -> None:
        out = Path(self.state.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(out)))


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")
