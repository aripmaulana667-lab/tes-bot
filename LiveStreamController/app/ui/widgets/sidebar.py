"""Sidebar with navigation items."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class SidebarButton(QPushButton):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setObjectName("SidebarButton")
        self.setMinimumHeight(40)


class Sidebar(QFrame):
    navigated = Signal(int)

    def __init__(self, items: List[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(210)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)

        title = QLabel("LiveStream\nController")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)
        layout.addSpacing(12)

        self._buttons: List[SidebarButton] = []
        for index, label in enumerate(items):
            btn = SidebarButton(label)
            btn.clicked.connect(lambda _=False, idx=index: self._navigate(idx))
            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch(1)
        self._buttons[0].setChecked(True)

        version_label = QLabel("v1.0.0")
        version_label.setObjectName("SidebarVersion")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

    def _navigate(self, index: int) -> None:
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)
        self.navigated.emit(index)

    def set_active(self, index: int) -> None:
        if 0 <= index < len(self._buttons):
            self._navigate(index)
