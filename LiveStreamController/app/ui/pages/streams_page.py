"""Streams page: multi live management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.api.client import APIClient
from app.ui.pages._base import BasePage


def _fmt_started(started_at: Optional[str], stopped_at: Optional[str], status: str) -> str:
    if not started_at:
        return "-"
    started = started_at.replace("T", " ")[:19]
    if status == "running":
        return f"sejak {started}"
    if stopped_at:
        return f"{started} → {stopped_at.replace('T', ' ')[:19]}"
    return started


class StartLiveDialog(QDialog):
    def __init__(self, accounts: List[Dict[str, Any]], videos: List[Dict[str, Any]]) -> None:
        super().__init__()
        self.setWindowTitle("Start Live")
        self.setModal(True)
        self.resize(500, 480)

        self._accounts = [a for a in accounts if a.get("is_active", True)]
        self._videos = videos

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Pilih akun (boleh lebih dari satu):"))
        self.accounts_list = QListWidget()
        self.accounts_list.setSelectionMode(QListWidget.MultiSelection)
        for acc in self._accounts:
            item = QListWidgetItem(f"{acc['name']} — {acc['platform']}")
            item.setData(Qt.UserRole, acc["id"])
            self.accounts_list.addItem(item)
        layout.addWidget(self.accounts_list)

        form = QFormLayout()
        self.video_combo = QComboBox()
        for video in self._videos:
            self.video_combo.addItem(video.get("original_name") or video.get("filename"), video.get("id"))
        form.addRow("Video", self.video_combo)

        self.bitrate_edit = QLineEdit("2500k")
        self.resolution_edit = QLineEdit("1280x720")
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(30)
        self.audio_edit = QLineEdit("128k")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "ultrafast", "superfast", "veryfast", "faster", "fast", "medium",
        ])
        self.preset_combo.setCurrentText("veryfast")
        self.loop_check = QCheckBox("Loop video")
        self.loop_check.setChecked(True)
        self.auto_check = QCheckBox("Auto-restart jika error")

        form.addRow("Bitrate", self.bitrate_edit)
        form.addRow("Resolusi", self.resolution_edit)
        form.addRow("FPS", self.fps_spin)
        form.addRow("Audio bitrate", self.audio_edit)
        form.addRow("Preset", self.preset_combo)
        form.addRow("", self.loop_check)
        form.addRow("", self.auto_check)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Start Lives")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_account_ids(self) -> List[int]:
        return [item.data(Qt.UserRole) for item in self.accounts_list.selectedItems()]

    def video_id(self) -> Optional[int]:
        return self.video_combo.currentData()

    def common_payload(self) -> Dict[str, Any]:
        return {
            "bitrate": self.bitrate_edit.text().strip() or "2500k",
            "resolution": self.resolution_edit.text().strip() or "1280x720",
            "fps": int(self.fps_spin.value()),
            "audio_bitrate": self.audio_edit.text().strip() or "128k",
            "preset": self.preset_combo.currentText(),
            "loop": self.loop_check.isChecked(),
            "auto_restart": self.auto_check.isChecked(),
        }


class StreamsPage(BasePage):
    COLUMNS = [
        "ID",
        "Akun",
        "Platform",
        "Video",
        "Status",
        "Started",
        "Bitrate",
        "Loop",
        "PID",
    ]

    def __init__(self, client: APIClient) -> None:
        super().__init__(client)
        self._items: List[Dict[str, Any]] = []
        self._filtered: List[Dict[str, Any]] = []
        self._accounts: List[Dict[str, Any]] = []
        self._videos: List[Dict[str, Any]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Multi Live")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch(1)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Semua", "Aktif", "Berhenti", "Error"])
        self.filter_combo.currentIndexChanged.connect(self._render)
        header.addWidget(self.filter_combo)

        self.start_button = QPushButton("Start Lives")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setProperty("secondary", True)
        self.restart_button = QPushButton("Restart")
        self.restart_button.setProperty("secondary", True)
        self.logs_button = QPushButton("Logs")
        self.logs_button.setProperty("secondary", True)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", True)

        for btn in (self.start_button, self.stop_button, self.restart_button, self.logs_button, self.refresh_button):
            header.addWidget(btn)
        outer.addLayout(header)

        self.start_button.clicked.connect(self._on_start)
        self.stop_button.clicked.connect(self._on_stop)
        self.restart_button.clicked.connect(self._on_restart)
        self.logs_button.clicked.connect(self._on_logs)
        self.refresh_button.clicked.connect(self.refresh)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        outer.addWidget(self.table, 1)

        # Auto refresh while page is visible.
        self._timer = QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self._auto_refresh)
        self._timer.start()

    def refresh(self) -> None:
        self.call_api("list_streams", self._on_list)
        self.call_api("list_accounts", self._on_accounts)
        self.call_api("list_videos", self._on_videos)

    def _auto_refresh(self) -> None:
        if not self.client.base_url or not self.isVisible():
            return
        self.call_api("list_streams", self._on_list, on_error=lambda _m: None)

    def selected(self) -> Optional[Dict[str, Any]]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        index = rows[0].row()
        if 0 <= index < len(self._filtered):
            return self._filtered[index]
        return None

    def _on_list(self, items: List[Dict[str, Any]]) -> None:
        self._items = items or []
        self._render()

    def _on_accounts(self, items: List[Dict[str, Any]]) -> None:
        self._accounts = items or []

    def _on_videos(self, items: List[Dict[str, Any]]) -> None:
        self._videos = items or []

    def _render(self) -> None:
        filt = self.filter_combo.currentText()
        mapping = {"Aktif": "running", "Berhenti": "stopped", "Error": "error"}
        target = mapping.get(filt)
        self._filtered = [s for s in self._items if not target or s.get("status") == target]
        self.table.setRowCount(len(self._filtered))
        for row, stream in enumerate(self._filtered):
            cells = [
                str(stream.get("id")),
                stream.get("account_name", ""),
                stream.get("platform", ""),
                stream.get("video_name", ""),
                stream.get("status", ""),
                _fmt_started(stream.get("started_at"), stream.get("stopped_at"), stream.get("status", "")),
                stream.get("bitrate", ""),
                "Ya" if stream.get("loop") else "Tidak",
                str(stream.get("pid") or "-"),
            ]
            for col, value in enumerate(cells):
                self.table.setItem(row, col, QTableWidgetItem(value))

    # ---- actions ---------------------------------------------------

    def _on_start(self) -> None:
        if not self._accounts:
            QMessageBox.information(self, "Start Live", "Belum ada akun. Tambah akun dulu.")
            return
        if not self._videos:
            QMessageBox.information(self, "Start Live", "Belum ada video. Upload dulu.")
            return
        dialog = StartLiveDialog(self._accounts, self._videos)
        if dialog.exec() != QDialog.Accepted:
            return
        account_ids = dialog.selected_account_ids()
        video_id = dialog.video_id()
        if not account_ids or not video_id:
            QMessageBox.warning(self, "Start Live", "Pilih akun dan video terlebih dulu.")
            return
        common = dialog.common_payload()
        payloads = [
            {**common, "account_id": account_id, "video_id": video_id}
            for account_id in account_ids
        ]
        self.run_async(
            self.client.start_streams,
            lambda _r: self.refresh(),
            payloads,
        )

    def _on_stop(self) -> None:
        stream = self.selected()
        if not stream:
            return
        reply = QMessageBox.question(
            self,
            "Konfirmasi",
            f"Stop stream {stream.get('id')} ({stream.get('account_name')})?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.run_async(self.client.stop_stream, lambda _d: self.refresh(), stream["id"])

    def _on_restart(self) -> None:
        stream = self.selected()
        if not stream:
            return
        self.run_async(self.client.restart_stream, lambda _d: self.refresh(), stream["id"])

    def _on_logs(self) -> None:
        stream = self.selected()
        if not stream:
            return

        def on_logs(data: Dict[str, Any]) -> None:
            text = "\n".join(data.get("lines", [])) or "(belum ada log)"
            QMessageBox.information(
                self, f"Log Stream #{stream['id']}", text[-4000:]
            )

        self.run_async(self.client.stream_logs, on_logs, stream["id"], 200)
