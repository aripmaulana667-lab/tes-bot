"""Logo tab."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.core import logo_processor

from .state import AppState, StateBus
from .widgets import Card, FilePicker, SliderRow, labeled


LOGO_FILTER = "Logo (*.png *.jpg *.jpeg *.webp);;All files (*.*)"


class LogoTab(QWidget):
    def __init__(self, state: AppState, bus: StateBus, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state = state
        self.bus = bus

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(14)

        card = Card("Logo")

        self.enable = QCheckBox("Show logo overlay")
        self.enable.setChecked(state.logo.enabled)
        self.enable.toggled.connect(self._on_enable)
        card.addWidget(self.enable)

        self.picker = FilePicker("Logo file", "file", LOGO_FILTER)
        self.picker.set_value(state.logo.path)
        self.picker.changed.connect(self._on_path)
        card.addLayout(labeled("File", self.picker))

        self.position = QComboBox()
        self.position.addItems(logo_processor.LOGO_POSITIONS)
        self.position.setCurrentText(state.logo.position)
        self.position.currentTextChanged.connect(self._on_position)
        card.addLayout(labeled("Position", self.position))

        self.size_slider = SliderRow("Size", 0.03, 0.4, state.logo.size, 0.01)
        self.size_slider.changed.connect(self._on_size)
        card.addWidget(self.size_slider)

        self.opacity_slider = SliderRow("Opacity", 0.1, 1.0, state.logo.opacity, 0.05)
        self.opacity_slider.changed.connect(self._on_opacity)
        card.addWidget(self.opacity_slider)

        self.circle = QCheckBox("Circle crop")
        self.circle.setChecked(state.logo.circle)
        self.circle.toggled.connect(self._on_circle)
        card.addWidget(self.circle)

        outer.addWidget(card)

        preview_card = Card("Preview")
        self.preview = QLabel()
        self.preview.setMinimumSize(280, 200)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("background: #F1F5F9; border-radius: 8px;")
        preview_card.addWidget(self.preview)
        outer.addWidget(preview_card)

        outer.addStretch(1)
        self._refresh_preview()

    # ---------------------------------------------------------------- handlers

    def _on_enable(self, checked: bool) -> None:
        self.state.logo.enabled = checked
        self.bus.state_changed.emit()

    def _on_path(self, value: str) -> None:
        self.state.logo.path = value
        self._refresh_preview()
        self.bus.state_changed.emit()

    def _on_position(self, value: str) -> None:
        self.state.logo.position = value
        self.bus.state_changed.emit()

    def _on_size(self, value: float) -> None:
        self.state.logo.size = value
        self.bus.state_changed.emit()

    def _on_opacity(self, value: float) -> None:
        self.state.logo.opacity = value
        self._refresh_preview()
        self.bus.state_changed.emit()

    def _on_circle(self, checked: bool) -> None:
        self.state.logo.circle = checked
        self._refresh_preview()
        self.bus.state_changed.emit()

    def _refresh_preview(self) -> None:
        p = Path(self.state.logo.path)
        if not p.exists():
            self.preview.setText("No logo selected.")
            self.preview.setPixmap(QPixmap())
            return
        try:
            prepared = logo_processor.prepare(self.state.logo, (320, 240))
        except Exception:  # noqa: BLE001
            self.preview.setText("Could not load logo")
            self.preview.setPixmap(QPixmap())
            return
        if prepared is None:
            self.preview.setText("Logo disabled or missing")
            return
        from io import BytesIO

        buf = BytesIO()
        prepared.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue(), "PNG")
        self.preview.setText("")
        self.preview.setPixmap(pix)
