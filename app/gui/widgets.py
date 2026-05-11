"""Small reusable widgets used across tabs."""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class Card(QFrame):
    """A white rounded "card" surface used to group settings on a tab."""

    def __init__(self, title: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        if title:
            label = QLabel(title)
            label.setObjectName("SectionTitle")
            layout.addWidget(label)
        self._body = QVBoxLayout()
        self._body.setSpacing(8)
        layout.addLayout(self._body)

    def addWidget(self, w: QWidget) -> None:
        self._body.addWidget(w)

    def addLayout(self, lyt) -> None:
        self._body.addLayout(lyt)


class FilePicker(QWidget):
    """Line edit + Browse button, supports files and folders."""

    changed = Signal(str)

    def __init__(
        self,
        title: str,
        mode: str = "file",  # file | files | folder
        filters: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.mode = mode
        self.filters = filters
        self._title = title

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(title)
        self.edit.textChanged.connect(self.changed.emit)
        layout.addWidget(self.edit, 1)

        self.button = QPushButton("Browse…")
        self.button.clicked.connect(self._open)
        layout.addWidget(self.button)

    def _open(self) -> None:
        if self.mode == "folder":
            path = QFileDialog.getExistingDirectory(self, self._title)
            if path:
                self.edit.setText(path)
        elif self.mode == "files":
            paths, _ = QFileDialog.getOpenFileNames(self, self._title, "", self.filters)
            if paths:
                self.edit.setText(";".join(paths))
        else:
            path, _ = QFileDialog.getOpenFileName(self, self._title, "", self.filters)
            if path:
                self.edit.setText(path)

    def value(self) -> str:
        return self.edit.text().strip()

    def set_value(self, value: str) -> None:
        self.edit.setText(value)


class ColorPicker(QWidget):
    """Hex color picker with a small color swatch."""

    changed = Signal(str)

    def __init__(self, value: str = "#3B82F6", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._value = value
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.swatch = QLabel()
        self.swatch.setFixedSize(28, 22)
        self.swatch.setStyleSheet(
            f"background-color: {value}; border: 1px solid #CBD5E1; border-radius: 4px;"
        )
        layout.addWidget(self.swatch)

        self.line = QLineEdit(value)
        self.line.setMaxLength(9)
        self.line.editingFinished.connect(self._sync_from_text)
        layout.addWidget(self.line, 1)

        btn = QPushButton("Pick")
        btn.clicked.connect(self._pick)
        layout.addWidget(btn)

    def value(self) -> str:
        return self._value

    def set_value(self, value: str) -> None:
        self._value = value
        self.line.setText(value)
        self.swatch.setStyleSheet(
            f"background-color: {value}; border: 1px solid #CBD5E1; border-radius: 4px;"
        )

    def _sync_from_text(self) -> None:
        text = self.line.text().strip()
        if not text.startswith("#"):
            text = "#" + text
        if QColor(text).isValid():
            self.set_value(text)
            self.changed.emit(text)
        else:
            self.line.setText(self._value)

    def _pick(self) -> None:
        color = QColorDialog.getColor(QColor(self._value), self, "Pick a color")
        if color.isValid():
            self.set_value(color.name())
            self.changed.emit(self._value)


class SliderRow(QWidget):
    """Labelled slider + numeric spinbox."""

    changed = Signal(float)

    def __init__(
        self,
        label: str,
        minimum: float = 0.0,
        maximum: float = 1.0,
        value: float = 0.5,
        step: float = 0.01,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._min = minimum
        self._max = maximum
        self._step = step
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        lab = QLabel(label)
        lab.setMinimumWidth(120)
        layout.addWidget(lab)

        self.slider = QSlider(Qt.Horizontal)
        scale = self._scale()
        self.slider.setRange(0, scale)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(self._on_slider)
        layout.addWidget(self.slider, 1)

        self.spin = QSpinBox()
        self.spin.setRange(0, scale)
        self.spin.valueChanged.connect(self._on_spin)
        layout.addWidget(self.spin)

        self.set_value(value)

    def _scale(self) -> int:
        return int(round((self._max - self._min) / self._step))

    def _on_slider(self, v: int) -> None:
        self.spin.blockSignals(True)
        self.spin.setValue(v)
        self.spin.blockSignals(False)
        self.changed.emit(self.value())

    def _on_spin(self, v: int) -> None:
        self.slider.blockSignals(True)
        self.slider.setValue(v)
        self.slider.blockSignals(False)
        self.changed.emit(self.value())

    def value(self) -> float:
        return round(self._min + self.slider.value() * self._step, 4)

    def set_value(self, v: float) -> None:
        clamped = max(self._min, min(self._max, v))
        ticks = int(round((clamped - self._min) / self._step))
        self.slider.blockSignals(True)
        self.spin.blockSignals(True)
        self.slider.setValue(ticks)
        self.spin.setValue(ticks)
        self.slider.blockSignals(False)
        self.spin.blockSignals(False)


class HSpacer(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


def labeled(text: str, widget: QWidget) -> QHBoxLayout:
    """Helper: label-on-left layout for a single control."""
    lyt = QHBoxLayout()
    lyt.setContentsMargins(0, 0, 0, 0)
    lyt.setSpacing(10)
    lab = QLabel(text)
    lab.setMinimumWidth(120)
    lyt.addWidget(lab)
    lyt.addWidget(widget, 1)
    return lyt
