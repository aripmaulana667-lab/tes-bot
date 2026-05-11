"""Background tab — single/multi backgrounds, color/gradient/image/video."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core import background_manager

from .state import AppState, StateBus
from .widgets import Card, ColorPicker, FilePicker, SliderRow, labeled


BG_FILTER = "Backgrounds (*.jpg *.jpeg *.png *.webp *.mp4 *.mov *.mkv *.avi);;All files (*.*)"


class BackgroundTab(QWidget):
    def __init__(self, state: AppState, bus: StateBus, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state = state
        self.bus = bus

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(14)

        # ---- Type selector ------------------------------------------------
        type_card = Card("Background type")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Solid color", "Gradient", "Image", "Video"])
        type_map = {"color": 0, "gradient": 1, "image": 2, "video": 3}
        self.type_combo.setCurrentIndex(type_map.get(state.background.type, 0))
        self.type_combo.currentIndexChanged.connect(self._on_type)
        type_card.addLayout(labeled("Type", self.type_combo))

        self.color1 = ColorPicker(state.background.color)
        self.color1.changed.connect(self._on_color1)
        type_card.addLayout(labeled("Primary color", self.color1))

        self.color2 = ColorPicker(state.background.color2)
        self.color2.changed.connect(self._on_color2)
        type_card.addLayout(labeled("Secondary color", self.color2))

        self.file_picker = FilePicker("Image or video file", "file", BG_FILTER)
        self.file_picker.set_value(state.background.path)
        self.file_picker.changed.connect(self._on_path)
        type_card.addLayout(labeled("File", self.file_picker))

        self.fit_combo = QComboBox()
        self.fit_combo.addItems(["cover", "contain", "stretch"])
        self.fit_combo.setCurrentText(state.background.fit)
        self.fit_combo.currentTextChanged.connect(self._on_fit)
        type_card.addLayout(labeled("Fit", self.fit_combo))

        self.ken_burns = QCheckBox("Subtle zoom/pan on still images (Ken Burns)")
        self.ken_burns.setChecked(state.background.ken_burns)
        self.ken_burns.toggled.connect(self._on_ken_burns)
        type_card.addWidget(self.ken_burns)

        outer.addWidget(type_card)

        # ---- Multi-background ---------------------------------------------
        multi_card = Card("Multiple backgrounds in one song")
        self.multi_enable = QCheckBox("Enable multi-background mode")
        self.multi_enable.setChecked(state.background.multi_enabled)
        self.multi_enable.toggled.connect(self._on_multi_enabled)
        multi_card.addWidget(self.multi_enable)

        self.multi_mode = QComboBox()
        self.multi_mode.addItems([
            "Manually picked files",
            "Folder — by order",
            "Folder — random",
        ])
        mode_map = {"manual": 0, "folder_order": 1, "folder_random": 2}
        self.multi_mode.setCurrentIndex(mode_map.get(state.background.multi_mode, 0))
        self.multi_mode.currentIndexChanged.connect(self._on_multi_mode)
        multi_card.addLayout(labeled("Mode", self.multi_mode))

        files_row = QHBoxLayout()
        self.multi_list = QListWidget()
        self.multi_list.setMinimumHeight(120)
        files_row.addWidget(self.multi_list, 1)
        btns = QVBoxLayout()
        add = QPushButton("Add files…")
        add.clicked.connect(self._add_files)
        btns.addWidget(add)
        rem = QPushButton("Remove selected")
        rem.clicked.connect(self._remove_selected)
        btns.addWidget(rem)
        clear = QPushButton("Clear")
        clear.clicked.connect(self._clear_files)
        btns.addWidget(clear)
        btns.addStretch(1)
        files_row.addLayout(btns)
        multi_card.addLayout(files_row)
        self._refresh_multi_list()

        self.multi_folder = FilePicker("Folder of backgrounds", "folder")
        self.multi_folder.set_value(state.background.multi_folder)
        self.multi_folder.changed.connect(self._on_multi_folder)
        multi_card.addLayout(labeled("Folder", self.multi_folder))

        self.interval = SliderRow(
            "Seconds per background",
            minimum=2.0,
            maximum=30.0,
            value=float(state.background.interval),
            step=0.5,
        )
        self.interval.changed.connect(self._on_interval)
        multi_card.addWidget(self.interval)

        self.transition_combo = QComboBox()
        self.transition_combo.addItems(["fade", "cut"])
        self.transition_combo.setCurrentText(state.background.transition)
        self.transition_combo.currentTextChanged.connect(self._on_transition)
        multi_card.addLayout(labeled("Transition", self.transition_combo))

        outer.addWidget(multi_card)
        outer.addStretch(1)

        self._update_visibility()

    # ---------------------------------------------------------------- handlers

    def _on_type(self, idx: int) -> None:
        rev = {0: "color", 1: "gradient", 2: "image", 3: "video"}
        self.state.background.type = rev.get(idx, "color")
        self._update_visibility()
        self.bus.state_changed.emit()

    def _on_color1(self, value: str) -> None:
        self.state.background.color = value
        self.bus.state_changed.emit()

    def _on_color2(self, value: str) -> None:
        self.state.background.color2 = value
        self.state.background.gradient = self.state.background.type in ("gradient",)
        self.bus.state_changed.emit()

    def _on_path(self, value: str) -> None:
        self.state.background.path = value
        self.bus.state_changed.emit()

    def _on_fit(self, value: str) -> None:
        self.state.background.fit = value
        self.bus.state_changed.emit()

    def _on_ken_burns(self, checked: bool) -> None:
        self.state.background.ken_burns = checked
        self.bus.state_changed.emit()

    def _on_multi_enabled(self, checked: bool) -> None:
        self.state.background.multi_enabled = checked
        self.bus.state_changed.emit()

    def _on_multi_mode(self, idx: int) -> None:
        rev = {0: "manual", 1: "folder_order", 2: "folder_random"}
        self.state.background.multi_mode = rev.get(idx, "manual")
        self._update_visibility()
        self.bus.state_changed.emit()

    def _on_multi_folder(self, value: str) -> None:
        self.state.background.multi_folder = value
        self.bus.state_changed.emit()

    def _on_interval(self, v: float) -> None:
        self.state.background.interval = v
        self.bus.state_changed.emit()

    def _on_transition(self, value: str) -> None:
        self.state.background.transition = value
        self.bus.state_changed.emit()

    def _add_files(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        paths, _ = QFileDialog.getOpenFileNames(self, "Add backgrounds", "", BG_FILTER)
        if paths:
            new = list(self.state.background.multi_files)
            for p in paths:
                if p not in new:
                    new.append(p)
            self.state.background.multi_files = new
            self._refresh_multi_list()
            self.bus.state_changed.emit()

    def _remove_selected(self) -> None:
        rows = [item.row() for item in self.multi_list.selectionModel().selectedRows()]
        keep = [
            path for i, path in enumerate(self.state.background.multi_files)
            if i not in rows
        ]
        self.state.background.multi_files = keep
        self._refresh_multi_list()
        self.bus.state_changed.emit()

    def _clear_files(self) -> None:
        self.state.background.multi_files = []
        self._refresh_multi_list()
        self.bus.state_changed.emit()

    def _refresh_multi_list(self) -> None:
        self.multi_list.clear()
        for p in self.state.background.multi_files:
            item = QListWidgetItem(Path(p).name)
            item.setData(Qt.UserRole, p)
            self.multi_list.addItem(item)

    def _update_visibility(self) -> None:
        bg_type = self.state.background.type
        is_media = bg_type in ("image", "video")
        is_gradient = bg_type == "gradient"
        self.file_picker.setVisible(is_media)
        self.fit_combo.setVisible(is_media)
        self.ken_burns.setVisible(is_media or self.state.background.multi_enabled)
        self.color1.setVisible(bg_type in ("color", "gradient"))
        self.color2.setVisible(is_gradient)

        manual = self.state.background.multi_mode == "manual"
        self.multi_list.setVisible(manual)
        self.multi_folder.setVisible(not manual)
