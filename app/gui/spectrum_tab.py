"""Spectrum tab — pick visualizer style + tuning."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core import spectrum_engine

from .state import AppState, StateBus
from .widgets import Card, ColorPicker, SliderRow, labeled


class SpectrumTab(QWidget):
    def __init__(self, state: AppState, bus: StateBus, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state = state
        self.bus = bus

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(14)

        # ---- Style --------------------------------------------------------
        style_card = Card("Style")
        self.style = QComboBox()
        self.style.addItems(spectrum_engine.SPECTRUM_STYLES)
        if state.spectrum.style in spectrum_engine.SPECTRUM_STYLES:
            self.style.setCurrentText(state.spectrum.style)
        self.style.currentTextChanged.connect(self._on_style)
        style_card.addLayout(labeled("Style", self.style))

        self.color = ColorPicker(state.spectrum.color)
        self.color.changed.connect(self._on_color)
        style_card.addLayout(labeled("Primary color", self.color))

        self.color2 = ColorPicker(state.spectrum.color2)
        self.color2.changed.connect(self._on_color2)
        style_card.addLayout(labeled("Gradient color", self.color2))

        self.gradient = QCheckBox("Use gradient")
        self.gradient.setChecked(state.spectrum.gradient)
        self.gradient.toggled.connect(self._on_gradient)
        self.glow = QCheckBox("Glow")
        self.glow.setChecked(state.spectrum.glow)
        self.glow.toggled.connect(self._on_glow)
        row = QHBoxLayout()
        row.addWidget(self.gradient)
        row.addWidget(self.glow)
        row.addStretch(1)
        style_card.addLayout(row)

        outer.addWidget(style_card)

        # ---- Tuning -------------------------------------------------------
        tune = Card("Tuning")
        self.sensitivity = SliderRow("Sensitivity", 0.2, 3.0, state.spectrum.sensitivity, 0.05)
        self.sensitivity.changed.connect(self._on_sensitivity)
        tune.addWidget(self.sensitivity)

        self.smoothness = SliderRow("Smoothness", 0.0, 0.95, state.spectrum.smoothness, 0.05)
        self.smoothness.changed.connect(self._on_smoothness)
        tune.addWidget(self.smoothness)

        self.bass_boost = SliderRow("Bass boost", 0.5, 3.0, state.spectrum.bass_boost, 0.05)
        self.bass_boost.changed.connect(self._on_bass)
        tune.addWidget(self.bass_boost)

        self.height = SliderRow("Spectrum height", 0.05, 0.6, state.spectrum.height, 0.01)
        self.height.changed.connect(self._on_height)
        tune.addWidget(self.height)

        self.width = SliderRow("Spectrum width", 0.3, 1.0, state.spectrum.width, 0.01)
        self.width.changed.connect(self._on_width)
        tune.addWidget(self.width)

        self.transparency = SliderRow("Transparency", 0.2, 1.0, state.spectrum.transparency, 0.01)
        self.transparency.changed.connect(self._on_transparency)
        tune.addWidget(self.transparency)

        self.position = QComboBox()
        self.position.addItems(spectrum_engine.POSITIONS)
        self.position.setCurrentText(state.spectrum.position)
        self.position.currentTextChanged.connect(self._on_position)
        tune.addLayout(labeled("Position", self.position))

        self.bars = QSpinBox()
        self.bars.setRange(8, 256)
        self.bars.setValue(state.spectrum.bars)
        self.bars.valueChanged.connect(self._on_bars)
        tune.addLayout(labeled("Number of bars", self.bars))

        self.fps = QSpinBox()
        self.fps.setRange(15, 60)
        self.fps.setValue(state.spectrum.fps)
        self.fps.valueChanged.connect(self._on_fps)
        tune.addLayout(labeled("Visualizer FPS", self.fps))

        outer.addWidget(tune)
        outer.addStretch(1)

    # ---------------------------------------------------------------- handlers

    def _on_style(self, v: str) -> None:
        self.state.spectrum.style = v
        self.bus.state_changed.emit()

    def _on_color(self, v: str) -> None:
        self.state.spectrum.color = v
        self.bus.state_changed.emit()

    def _on_color2(self, v: str) -> None:
        self.state.spectrum.color2 = v
        self.bus.state_changed.emit()

    def _on_gradient(self, checked: bool) -> None:
        self.state.spectrum.gradient = checked
        self.bus.state_changed.emit()

    def _on_glow(self, checked: bool) -> None:
        self.state.spectrum.glow = checked
        self.bus.state_changed.emit()

    def _on_sensitivity(self, v: float) -> None:
        self.state.spectrum.sensitivity = v
        self.bus.state_changed.emit()

    def _on_smoothness(self, v: float) -> None:
        self.state.spectrum.smoothness = v
        self.bus.state_changed.emit()

    def _on_bass(self, v: float) -> None:
        self.state.spectrum.bass_boost = v
        self.bus.state_changed.emit()

    def _on_height(self, v: float) -> None:
        self.state.spectrum.height = v
        self.bus.state_changed.emit()

    def _on_width(self, v: float) -> None:
        self.state.spectrum.width = v
        self.bus.state_changed.emit()

    def _on_transparency(self, v: float) -> None:
        self.state.spectrum.transparency = v
        self.bus.state_changed.emit()

    def _on_position(self, v: str) -> None:
        self.state.spectrum.position = v
        self.bus.state_changed.emit()

    def _on_bars(self, v: int) -> None:
        self.state.spectrum.bars = v
        self.bus.state_changed.emit()

    def _on_fps(self, v: int) -> None:
        self.state.spectrum.fps = v
        self.bus.state_changed.emit()
