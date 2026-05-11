"""Input tab — choose a single song or a folder for batch render."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.core import audio_reader

from .state import AppState, StateBus
from .widgets import Card, FilePicker, labeled


SUPPORTED_FILTER = "Audio files (*.mp3 *.wav *.flac *.m4a *.aac);;All files (*.*)"


class InputTab(QWidget):
    def __init__(self, state: AppState, bus: StateBus, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state = state
        self.bus = bus

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(14)

        # Mode selection
        mode_card = Card("Input mode")
        mode_layout = QHBoxLayout()
        self.radio_single = QRadioButton("Single file")
        self.radio_batch = QRadioButton("Batch (folder)")
        self.radio_single.setChecked(state.input_mode == "single")
        self.radio_batch.setChecked(state.input_mode == "batch")
        self.radio_single.toggled.connect(self._update_mode)
        self.radio_batch.toggled.connect(self._update_mode)
        mode_layout.addWidget(self.radio_single)
        mode_layout.addWidget(self.radio_batch)
        mode_layout.addStretch(1)
        mode_card.addLayout(mode_layout)
        outer.addWidget(mode_card)

        # Single file picker
        self.single_card = Card("Single file")
        self.single_picker = FilePicker("Pick an audio file", "file", SUPPORTED_FILTER)
        self.single_picker.set_value(state.audio_path)
        self.single_picker.changed.connect(self._on_single_changed)
        self.single_card.addWidget(self.single_picker)

        self.single_meta = QLabel("")
        self.single_meta.setObjectName("Subtle")
        self.single_card.addWidget(self.single_meta)
        outer.addWidget(self.single_card)

        # Batch picker
        self.batch_card = Card("Batch")
        self.folder_picker = FilePicker("Pick a folder of audio files", "folder")
        self.folder_picker.set_value(state.audio_folder)
        self.folder_picker.changed.connect(self._on_folder_changed)
        self.batch_card.addWidget(self.folder_picker)

        self.batch_list = QListWidget()
        self.batch_list.setMinimumHeight(160)
        self.batch_card.addWidget(self.batch_list)

        bg_mode_combo = QComboBox()
        bg_mode_combo.addItems([
            "By order (folder)",
            "By matching name",
            "Random (folder)",
            "Don't override",
        ])
        index_map = {"order": 0, "match": 1, "random": 2, "none": 3}
        bg_mode_combo.setCurrentIndex(index_map.get(state.batch.background_mode, 0))
        bg_mode_combo.currentIndexChanged.connect(self._on_bg_mode)
        self.batch_card.addLayout(labeled("Batch BG mode", bg_mode_combo))
        self.bg_mode_combo = bg_mode_combo

        self.batch_bg_picker = FilePicker("Folder containing backgrounds", "folder")
        self.batch_bg_picker.set_value(state.batch.background_folder)
        self.batch_bg_picker.changed.connect(self._on_batch_bg_folder)
        self.batch_card.addLayout(labeled("Background folder", self.batch_bg_picker))

        outer.addWidget(self.batch_card)

        # Output dir
        out_card = Card("Output")
        self.output_picker = FilePicker("Where to save rendered videos", "folder")
        self.output_picker.set_value(state.output_dir)
        self.output_picker.changed.connect(self._on_output_changed)
        out_card.addLayout(labeled("Output folder", self.output_picker))
        outer.addWidget(out_card)

        outer.addStretch(1)
        self._update_mode()
        if state.audio_path:
            self._on_single_changed(state.audio_path)
        if state.audio_folder:
            self._refresh_batch_list()

    # ---------------------------------------------------------------- handlers

    def _update_mode(self) -> None:
        single = self.radio_single.isChecked()
        self.state.input_mode = "single" if single else "batch"
        self.single_card.setVisible(single)
        self.batch_card.setVisible(not single)
        self.bus.state_changed.emit()

    def _on_single_changed(self, value: str) -> None:
        self.state.audio_path = value
        path = Path(value)
        if value and path.is_file() and audio_reader.is_supported(path):
            info = audio_reader.probe(path)
            mins, secs = divmod(int(info.duration or 0), 60)
            text = f"{info.title}"
            if info.artist:
                text += f"  •  {info.artist}"
            text += f"  •  {mins:02d}:{secs:02d}  •  {info.sample_rate} Hz / {info.channels}ch"
            self.single_meta.setText(text)
            self.bus.audio_chosen.emit(str(path))
        else:
            self.single_meta.setText("No file selected." if not value else "Unsupported or missing file.")
        self.bus.state_changed.emit()

    def _on_folder_changed(self, value: str) -> None:
        self.state.audio_folder = value
        self._refresh_batch_list()
        self.bus.state_changed.emit()

    def _refresh_batch_list(self) -> None:
        self.batch_list.clear()
        if not self.state.audio_folder:
            return
        files = audio_reader.list_supported_in_folder(self.state.audio_folder)
        for f in files:
            item = QListWidgetItem(f.name)
            item.setData(Qt.UserRole, str(f))
            self.batch_list.addItem(item)
        if files:
            self.batch_list.addItem(QListWidgetItem(f"{len(files)} file(s) queued"))

    def _on_bg_mode(self, idx: int) -> None:
        mapping = {0: "order", 1: "match", 2: "random", 3: "none"}
        self.state.batch.background_mode = mapping.get(idx, "order")
        self.bus.state_changed.emit()

    def _on_batch_bg_folder(self, value: str) -> None:
        self.state.batch.background_folder = value
        self.bus.state_changed.emit()

    def _on_output_changed(self, value: str) -> None:
        self.state.output_dir = value or self.state.output_dir
        self.bus.state_changed.emit()
