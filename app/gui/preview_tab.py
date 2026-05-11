"""Preview tab — quick still-frame preview of the current configuration."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.core import audio_reader, render_engine

from .state import AppState, StateBus
from .widgets import Card, labeled


class _PreviewWorker(QObject):
    done = Signal(object, str)  # PIL image or None, error string

    def __init__(self, job: render_engine.RenderJob, t: float) -> None:
        super().__init__()
        self.job = job
        self.t = t

    def run(self) -> None:
        try:
            img = render_engine.render_preview_frame(self.job, self.t, max_size=720)
            self.done.emit(img, "")
        except Exception as exc:  # noqa: BLE001
            self.done.emit(None, str(exc))


class PreviewTab(QWidget):
    """A still-frame preview rendered at low resolution."""

    def __init__(self, state: AppState, bus: StateBus, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state = state
        self.bus = bus
        self._lyrics_provider = None
        self._thread: Optional[QThread] = None
        self._worker: Optional[_PreviewWorker] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(14)

        controls = Card("Preview")
        row = QHBoxLayout()
        self.time_spin = QDoubleSpinBox()
        self.time_spin.setRange(0.0, 9999.0)
        self.time_spin.setDecimals(2)
        self.time_spin.setSuffix(" s")
        self.time_spin.setValue(5.0)
        row.addWidget(QLabel("Time"))
        row.addWidget(self.time_spin)

        self.refresh = QPushButton("Refresh preview")
        self.refresh.setObjectName("PrimaryButton")
        self.refresh.clicked.connect(self.refresh_preview)
        row.addWidget(self.refresh)
        row.addStretch(1)
        controls.addLayout(row)

        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 100)
        self.timeline.valueChanged.connect(self._on_timeline)
        controls.addWidget(self.timeline)

        outer.addWidget(controls)

        canvas = Card("")
        self.canvas = QLabel("Preview will appear here.")
        self.canvas.setAlignment(Qt.AlignCenter)
        self.canvas.setMinimumSize(800, 450)
        self.canvas.setStyleSheet("background: #0F172A; color: #94A3B8; border-radius: 10px;")
        canvas.addWidget(self.canvas)
        outer.addWidget(canvas, 1)

        outer.addStretch(0)

        bus.audio_chosen.connect(self._on_audio_chosen)

    def set_lyrics_provider(self, provider) -> None:
        self._lyrics_provider = provider

    def _on_audio_chosen(self, path: str) -> None:
        if not path or not Path(path).exists():
            return
        info = audio_reader.probe(path)
        if info.duration > 0:
            self.timeline.setRange(0, int(info.duration * 10))
            self.timeline.setValue(min(50, int(info.duration * 10 / 2)))
            self.time_spin.setMaximum(info.duration)

    def _on_timeline(self, v: int) -> None:
        self.time_spin.setValue(v / 10.0)

    def refresh_preview(self) -> None:
        path = self.state.audio_path
        if not path or not Path(path).exists():
            QMessageBox.information(self, "Preview", "Pick an audio file on the Input tab first.")
            return
        out = str(Path(self.state.output_dir) / "preview.tmp.mp4")
        job = render_engine.RenderJob(
            audio_path=path,
            output_path=out,
            background=self.state.background,
            spectrum=self.state.spectrum,
            lyrics=self.state.lyrics,
            logo=self.state.logo,
            render=self.state.render,
            lyrics_data=self._lyrics_provider() if self._lyrics_provider else None,
        )
        self.refresh.setEnabled(False)
        self.canvas.setText("Rendering preview…")

        self._thread = QThread(self)
        self._worker = _PreviewWorker(job, self.time_spin.value())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_done)
        self._worker.done.connect(self._thread.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_done(self, image, error: str) -> None:
        self.refresh.setEnabled(True)
        if image is None:
            self.canvas.setText(f"Preview failed:\n{error}")
            self.canvas.setPixmap(QPixmap())
            return
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue(), "PNG")
        # Scale to fit canvas keeping aspect.
        self.canvas.setPixmap(pix.scaled(
            self.canvas.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.canvas.setText("")
