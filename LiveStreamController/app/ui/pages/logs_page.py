"""Logs page: tail FFmpeg logs for a chosen stream."""

from __future__ import annotations

from typing import Any, Dict, List

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from app.api.client import APIClient
from app.ui.pages._base import BasePage


class LogsPage(BasePage):
    def __init__(self, client: APIClient) -> None:
        super().__init__(client)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(12)

        title = QLabel("Logs")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        outer.addWidget(title)

        row = QHBoxLayout()
        row.addWidget(QLabel("Stream:"))
        self.combo = QComboBox()
        self.combo.setMinimumWidth(260)
        row.addWidget(self.combo)

        self.refresh_streams_button = QPushButton("Reload daftar")
        self.refresh_streams_button.setProperty("secondary", True)
        self.refresh_logs_button = QPushButton("Refresh log")
        self.refresh_logs_button.setProperty("secondary", True)
        self.tail_check = QPushButton("Auto Tail: ON")
        self.tail_check.setCheckable(True)
        self.tail_check.setChecked(True)
        self.tail_check.setProperty("secondary", True)
        row.addWidget(self.refresh_streams_button)
        row.addWidget(self.refresh_logs_button)
        row.addWidget(self.tail_check)
        row.addStretch(1)
        outer.addLayout(row)

        self.refresh_streams_button.clicked.connect(self._reload_streams)
        self.refresh_logs_button.clicked.connect(self._reload_logs)
        self.tail_check.toggled.connect(self._on_toggle_tail)

        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        outer.addWidget(self.editor, 1)

        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self._auto_tail)
        self._timer.start()

    def refresh(self) -> None:
        self._reload_streams()

    # ---- handlers --------------------------------------------------

    def _reload_streams(self) -> None:
        self.call_api("list_streams", self._populate_streams, on_error=lambda _m: None)

    def _populate_streams(self, items: List[Dict[str, Any]]) -> None:
        current = self.combo.currentData()
        self.combo.clear()
        for stream in items or []:
            label = f"#{stream['id']} {stream.get('account_name','?')} ({stream.get('status','?')})"
            self.combo.addItem(label, stream["id"])
        if current is not None:
            idx = self.combo.findData(current)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)

    def _reload_logs(self) -> None:
        sid = self.combo.currentData()
        if sid is None:
            return
        self.run_async(
            self.client.stream_logs,
            self._render_logs,
            sid,
            300,
            on_error=lambda _m: None,
        )

    def _render_logs(self, data: Dict[str, Any]) -> None:
        text = "\n".join(data.get("lines", []))
        self.editor.setPlainText(text)
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.End)
        self.editor.setTextCursor(cursor)

    def _on_toggle_tail(self, checked: bool) -> None:
        self.tail_check.setText(f"Auto Tail: {'ON' if checked else 'OFF'}")
        if checked:
            self._timer.start()
        else:
            self._timer.stop()

    def _auto_tail(self) -> None:
        if not self.isVisible() or not self.tail_check.isChecked():
            return
        self._reload_logs()
