"""Stat card widget for the dashboard."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class StatCard(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setMinimumHeight(96)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._title = QLabel(title)
        self._title.setObjectName("StatCardTitle")
        self._value = QLabel("-")
        self._value.setObjectName("StatCardValue")
        self._sub = QLabel("")
        self._sub.setObjectName("StatCardSub")

        for label in (self._title, self._value, self._sub):
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            layout.addWidget(label)
        layout.addStretch(1)

    def set_value(self, value: str, subtitle: str = "") -> None:
        self._value.setText(value)
        self._sub.setText(subtitle)
