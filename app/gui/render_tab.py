"""Render tab — settings + Render button + FFmpeg status + progress."""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core import audio_reader, batch_processor, ffmpeg_manager, render_engine

from .state import AppState, StateBus
from .widgets import Card, FilePicker, HSpacer, labeled


class _RenderWorker(QObject):
    progress = Signal(float, str, str)  # frac, message, current_file
    log = Signal(str)
    finished = Signal(bool, str)  # ok, message

    def __init__(self, kind: str, job, items=None) -> None:
        super().__init__()
        self.kind = kind
        self.job = job
        self.items = items
        self.cancel_event = threading.Event()

    def run(self) -> None:
        try:
            if self.kind == "single":
                output = render_engine.render_video(
                    self.job,
                    on_progress=lambda p: self.progress.emit(p.fraction, p.message, Path(self.job.output_path).name),
                    on_log=self.log.emit,
                    cancel_event=self.cancel_event,
                )
                self.finished.emit(True, output)
            else:
                outputs = batch_processor.run(
                    self.items,
                    self.job,
                    on_progress=lambda p: self.progress.emit(
                        p.overall_progress, p.message, p.current_file
                    ),
                    on_log=self.log.emit,
                    cancel_event=self.cancel_event,
                )
                self.finished.emit(True, f"{len(outputs)} file(s) rendered.")
        except Exception as exc:  # noqa: BLE001
            self.finished.emit(False, str(exc))

    def cancel(self) -> None:
        self.cancel_event.set()


class RenderTab(QWidget):
    """Render tab."""

    request_lyrics_data = Signal()

    def __init__(self, state: AppState, bus: StateBus, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state = state
        self.bus = bus
        self._worker: Optional[_RenderWorker] = None
        self._thread: Optional[QThread] = None
        self._lyrics_provider = None
        self._ffmpeg_status: Optional[ffmpeg_manager.FFmpegStatus] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(14)

        # ---- Render settings ---------------------------------------------
        settings_card = Card("Render settings")

        self.preset = QComboBox()
        self.preset.addItem("Custom")
        for name in render_engine.PRESETS.keys():
            self.preset.addItem(name)
        self.preset.currentTextChanged.connect(self._on_preset)
        settings_card.addLayout(labeled("Preset", self.preset))

        self.resolution = QComboBox()
        self.resolution.addItems(["720p", "1080p", "1440p", "4K", "Custom"])
        self.resolution.setCurrentText(state.render.resolution)
        self.resolution.currentTextChanged.connect(self._on_resolution)
        settings_card.addLayout(labeled("Resolution", self.resolution))

        custom_row = QHBoxLayout()
        self.custom_w = QSpinBox()
        self.custom_w.setRange(160, 7680)
        self.custom_w.setValue(state.render.custom_size[0] if state.render.custom_size else 1920)
        self.custom_w.valueChanged.connect(self._on_custom)
        self.custom_h = QSpinBox()
        self.custom_h.setRange(90, 4320)
        self.custom_h.setValue(state.render.custom_size[1] if state.render.custom_size else 1080)
        self.custom_h.valueChanged.connect(self._on_custom)
        custom_row.addWidget(self.custom_w)
        custom_row.addWidget(QLabel("×"))
        custom_row.addWidget(self.custom_h)
        custom_row.addStretch(1)
        settings_card.addLayout(labeled("Custom WxH", _row_widget(custom_row)))

        self.fps = QComboBox()
        self.fps.addItems(["24", "30", "60"])
        self.fps.setCurrentText(str(state.render.fps))
        self.fps.currentTextChanged.connect(lambda v: self._update_render("fps", int(v)))
        settings_card.addLayout(labeled("FPS", self.fps))

        self.quality = QComboBox()
        self.quality.addItems(["Low", "Medium", "High", "Best"])
        self.quality.setCurrentText(state.render.quality)
        self.quality.currentTextChanged.connect(lambda v: self._update_render("quality", v))
        settings_card.addLayout(labeled("Quality", self.quality))

        self.encoder = QComboBox()
        self.encoder.addItems([
            "auto", "libx264", "h264_nvenc", "h264_qsv", "h264_amf"
        ])
        self.encoder.setCurrentText(state.render.encoder)
        self.encoder.currentTextChanged.connect(lambda v: self._update_render("encoder", v))
        settings_card.addLayout(labeled("Encoder", self.encoder))

        outer.addWidget(settings_card)

        # ---- FFmpeg status -----------------------------------------------
        ffm = Card("FFmpeg")
        self.ffmpeg_status_label = QLabel("FFmpeg status: checking…")
        ffm.addWidget(self.ffmpeg_status_label)

        ffm_row = QHBoxLayout()
        self.btn_detect = QPushButton("Detect")
        self.btn_detect.clicked.connect(self._detect_ffmpeg)
        ffm_row.addWidget(self.btn_detect)
        self.btn_install = QPushButton("Install FFmpeg Online")
        self.btn_install.setObjectName("PrimaryButton")
        self.btn_install.clicked.connect(self._install_ffmpeg)
        ffm_row.addWidget(self.btn_install)
        self.btn_pick = QPushButton("Pick path…")
        self.btn_pick.clicked.connect(self._pick_ffmpeg)
        ffm_row.addWidget(self.btn_pick)
        self.btn_test = QPushButton("Test")
        self.btn_test.clicked.connect(self._test_ffmpeg)
        ffm_row.addWidget(self.btn_test)
        self.btn_reset = QPushButton("Reset path")
        self.btn_reset.clicked.connect(self._reset_ffmpeg)
        ffm_row.addWidget(self.btn_reset)
        ffm_row.addStretch(1)
        ffm.addLayout(ffm_row)
        outer.addWidget(ffm)

        # ---- Progress + actions ------------------------------------------
        action = Card("Render")
        self.estimate_label = QLabel("Estimate: -")
        action.addWidget(self.estimate_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setFormat("Idle")
        action.addWidget(self.progress)

        self.current_label = QLabel("")
        self.current_label.setObjectName("Subtle")
        action.addWidget(self.current_label)

        btn_row = QHBoxLayout()
        self.btn_render = QPushButton("Render")
        self.btn_render.setObjectName("PrimaryButton")
        self.btn_render.clicked.connect(self._start_render)
        btn_row.addWidget(self.btn_render)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("DangerButton")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_render)
        btn_row.addWidget(self.btn_cancel)

        self.btn_open_output = QPushButton("Open output folder")
        self.btn_open_output.clicked.connect(self._open_output)
        btn_row.addWidget(self.btn_open_output)

        btn_row.addStretch(1)
        action.addLayout(btn_row)

        outer.addWidget(action)
        outer.addStretch(1)

        bus.state_changed.connect(self._refresh_estimate)
        bus.audio_chosen.connect(lambda _p: self._refresh_estimate())

    # ---------------------------------------------------------------- helpers

    def set_lyrics_provider(self, provider) -> None:
        """Inject a callable returning the current LyricsData."""
        self._lyrics_provider = provider

    def detect_initial(self) -> None:
        self._detect_ffmpeg()

    def _update_render(self, field: str, value) -> None:
        setattr(self.state.render, field, value)
        self.preset.blockSignals(True)
        self.preset.setCurrentText("Custom")
        self.preset.blockSignals(False)
        self.bus.state_changed.emit()

    def _on_preset(self, name: str) -> None:
        preset = render_engine.PRESETS.get(name)
        if not preset:
            return
        self.state.render.resolution = preset["resolution"]
        self.state.render.fps = preset["fps"]
        self.state.render.quality = preset["quality"]
        self.state.render.fast = preset["fast"]
        self.resolution.setCurrentText(self.state.render.resolution)
        self.fps.setCurrentText(str(self.state.render.fps))
        self.quality.setCurrentText(self.state.render.quality)
        self.bus.state_changed.emit()

    def _on_resolution(self, v: str) -> None:
        self.state.render.resolution = v
        self.custom_w.setEnabled(v == "Custom")
        self.custom_h.setEnabled(v == "Custom")
        self.preset.blockSignals(True)
        self.preset.setCurrentText("Custom")
        self.preset.blockSignals(False)
        self.bus.state_changed.emit()

    def _on_custom(self, _v: int) -> None:
        self.state.render.custom_size = (self.custom_w.value(), self.custom_h.value())
        self.bus.state_changed.emit()

    # ---------------------------------------------------------------- ffmpeg

    def _detect_ffmpeg(self) -> None:
        status = ffmpeg_manager.probe_ffmpeg(self.state.ffmpeg_path)
        self._set_ffmpeg_status(status)

    def _install_ffmpeg(self) -> None:
        self.ffmpeg_status_label.setText("FFmpeg: downloading…")
        self.btn_install.setEnabled(False)

        thread = QThread(self)
        worker = _FFmpegInstallerWorker()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._on_ffmpeg_progress)
        worker.finished.connect(self._on_ffmpeg_installed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self._installer_thread = thread
        self._installer_worker = worker

    def _on_ffmpeg_progress(self, frac: float, msg: str) -> None:
        self.ffmpeg_status_label.setText(f"FFmpeg: {msg}")
        self.progress.setValue(int(frac * 1000))

    def _on_ffmpeg_installed(self, status: ffmpeg_manager.FFmpegStatus) -> None:
        self.btn_install.setEnabled(True)
        self._set_ffmpeg_status(status)
        if not status.found:
            QMessageBox.warning(self, "FFmpeg install failed", status.error or "Unknown error")

    def _pick_ffmpeg(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Pick the FFmpeg executable",
            "",
            "FFmpeg (ffmpeg ffmpeg.exe);;All files (*.*)",
        )
        if path:
            ffmpeg_manager.save_configured_path(path)
            self.state.ffmpeg_path = path
            self._detect_ffmpeg()

    def _test_ffmpeg(self) -> None:
        status = ffmpeg_manager.probe_ffmpeg(self.state.ffmpeg_path)
        if status.found:
            QMessageBox.information(
                self,
                "FFmpeg",
                f"FFmpeg OK\nVersion: {status.version}\nPath: {status.ffmpeg_path}\nEncoders: "
                f"NVENC={status.has_nvenc} QSV={status.has_qsv} AMF={status.has_amf}",
            )
        else:
            QMessageBox.warning(self, "FFmpeg", status.error or "FFmpeg not found")
        self._set_ffmpeg_status(status)

    def _reset_ffmpeg(self) -> None:
        ffmpeg_manager.save_configured_path("")
        self.state.ffmpeg_path = ""
        self._detect_ffmpeg()

    def _set_ffmpeg_status(self, status: ffmpeg_manager.FFmpegStatus) -> None:
        self._ffmpeg_status = status
        self.bus.ffmpeg_status_changed.emit(status)
        if status.found:
            extras = []
            if status.has_nvenc:
                extras.append("NVENC")
            if status.has_qsv:
                extras.append("QSV")
            if status.has_amf:
                extras.append("AMF")
            extras_text = (" • " + ", ".join(extras)) if extras else ""
            self.ffmpeg_status_label.setText(
                f"FFmpeg installed — {status.version}{extras_text}  ({status.ffmpeg_path})"
            )
            self.ffmpeg_status_label.setProperty("status", "ok")
            self.ffmpeg_status_label.setObjectName("StatusOk")
            self.state.ffmpeg_path = status.ffmpeg_path
        else:
            self.ffmpeg_status_label.setText("FFmpeg not installed. Click 'Install FFmpeg Online'.")
            self.ffmpeg_status_label.setObjectName("StatusBad")
        self.ffmpeg_status_label.style().unpolish(self.ffmpeg_status_label)
        self.ffmpeg_status_label.style().polish(self.ffmpeg_status_label)

    # ---------------------------------------------------------------- render

    def _build_job(self) -> render_engine.RenderJob:
        # Single output file derived from audio name.
        if self.state.input_mode == "single":
            audio = self.state.audio_path
            out = str(Path(self.state.output_dir) / (Path(audio).stem + ".mp4"))
        else:
            audio = self.state.audio_path or ""
            out = str(Path(self.state.output_dir) / "batch.mp4")

        return render_engine.RenderJob(
            audio_path=audio,
            output_path=out,
            background=self.state.background,
            spectrum=self.state.spectrum,
            lyrics=self.state.lyrics,
            logo=self.state.logo,
            render=self.state.render,
            lyrics_data=self._lyrics_provider() if self._lyrics_provider else None,
        )

    def _start_render(self) -> None:
        status = ffmpeg_manager.probe_ffmpeg(self.state.ffmpeg_path)
        if not status.found:
            QMessageBox.warning(self, "FFmpeg required", "Install FFmpeg first.")
            return
        if self.state.input_mode == "single":
            if not self.state.audio_path or not Path(self.state.audio_path).exists():
                QMessageBox.warning(self, "Audio required", "Pick an audio file on the Input tab.")
                return
            job = self._build_job()
            self._launch(_RenderWorker("single", job))
        else:
            if not self.state.audio_folder or not Path(self.state.audio_folder).exists():
                QMessageBox.warning(self, "Folder required", "Pick an audio folder on the Input tab.")
                return
            settings = batch_processor.BatchSettings(
                background_mode=self.state.batch.background_mode,
                background_folder=self.state.batch.background_folder,
            )
            items = batch_processor.build_items(
                self.state.audio_folder, self.state.output_dir, settings
            )
            if not items:
                QMessageBox.information(self, "Nothing to render", "No supported audio files in the folder.")
                return
            job = self._build_job()
            self._launch(_RenderWorker("batch", job, items=items))

    def _launch(self, worker: _RenderWorker) -> None:
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._on_progress)
        worker.log.connect(self.bus.log_emitted.emit)
        worker.finished.connect(self._on_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._worker = worker
        self._thread = thread
        self.btn_render.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress.setFormat("Starting…")
        self.progress.setValue(0)
        thread.start()

    def _on_progress(self, frac: float, msg: str, file: str) -> None:
        self.progress.setValue(int(max(0.0, min(1.0, frac)) * 1000))
        self.progress.setFormat(f"{int(frac * 100)}% — {msg}")
        self.current_label.setText(file)

    def _on_finished(self, ok: bool, message: str) -> None:
        self.btn_render.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        if ok:
            self.progress.setFormat("Done")
            self.progress.setValue(1000)
            self.bus.log_emitted.emit(f"[render] success: {message}")
        else:
            self.progress.setFormat("Failed")
            self.bus.log_emitted.emit(f"[render] failed: {message}")
            QMessageBox.warning(self, "Render failed", message)
        self._worker = None
        self._thread = None

    def _cancel_render(self) -> None:
        if self._worker is not None:
            self._worker.cancel()

    def _open_output(self) -> None:
        out = Path(self.state.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(out)))

    def _refresh_estimate(self) -> None:
        path = self.state.audio_path
        if not path or not Path(path).exists():
            self.estimate_label.setText("Estimate: pick an audio file first.")
            return
        try:
            job = self._build_job()
            estimate = render_engine.estimate_duration(job, self._ffmpeg_status)
        except Exception:  # noqa: BLE001
            self.estimate_label.setText("Estimate: -")
            return
        if estimate <= 0:
            self.estimate_label.setText("Estimate: -")
            return
        mins, secs = divmod(int(estimate), 60)
        self.estimate_label.setText(f"Estimated render time: ~{mins}m {secs}s")


def _row_widget(layout) -> QWidget:
    w = QWidget()
    w.setLayout(layout)
    return w


class _FFmpegInstallerWorker(QObject):
    progress = Signal(float, str)
    finished = Signal(object)

    def run(self) -> None:
        def report(frac: float, msg: str) -> None:
            self.progress.emit(frac, msg)

        status = ffmpeg_manager.install_online(on_progress=report)
        self.finished.emit(status)
