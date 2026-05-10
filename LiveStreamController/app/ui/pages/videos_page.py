"""Video gallery page."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.api.client import APIClient
from app.ui.pages._base import BasePage


def _fmt_size(bytes_value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_value or 0)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _fmt_duration(seconds: Optional[float]) -> str:
    if not seconds:
        return "-"
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


class VideosPage(BasePage):
    COLUMNS = ["ID", "Nama", "Ukuran", "Durasi", "Tanggal"]

    def __init__(self, client: APIClient) -> None:
        super().__init__(client)
        self._items: List[Dict[str, Any]] = []
        self._filtered: List[Dict[str, Any]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Galeri Video")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch(1)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Cari video...")
        self.search_edit.setFixedWidth(220)
        self.search_edit.textChanged.connect(self._render)
        header.addWidget(self.search_edit)

        self.upload_button = QPushButton("Upload")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", True)
        self.rename_button = QPushButton("Rename")
        self.rename_button.setProperty("secondary", True)
        self.delete_button = QPushButton("Hapus")
        self.delete_button.setProperty("danger", True)
        for btn in (self.upload_button, self.refresh_button, self.rename_button, self.delete_button):
            header.addWidget(btn)

        outer.addLayout(header)

        self.upload_button.clicked.connect(self._on_upload)
        self.refresh_button.clicked.connect(self.refresh)
        self.rename_button.clicked.connect(self._on_rename)
        self.delete_button.clicked.connect(self._on_delete)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        outer.addWidget(self.progress)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        outer.addWidget(self.table, 1)

    def refresh(self) -> None:
        self.call_api("list_videos", self._on_list)

    # ---- selection -------------------------------------------------

    def selected_video(self) -> Optional[Dict[str, Any]]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        index = rows[0].row()
        if 0 <= index < len(self._filtered):
            return self._filtered[index]
        return None

    # ---- handlers --------------------------------------------------

    def _on_list(self, items: List[Dict[str, Any]]) -> None:
        self._items = items or []
        self._render()

    def _render(self) -> None:
        query = self.search_edit.text().strip().lower()
        self._filtered = [
            v for v in self._items
            if not query or query in v.get("original_name", "").lower() or query in v.get("filename", "").lower()
        ]
        self.table.setRowCount(len(self._filtered))
        for row, video in enumerate(self._filtered):
            self.table.setItem(row, 0, QTableWidgetItem(str(video.get("id"))))
            self.table.setItem(row, 1, QTableWidgetItem(video.get("original_name") or video.get("filename", "")))
            self.table.setItem(row, 2, QTableWidgetItem(_fmt_size(video.get("size", 0))))
            self.table.setItem(row, 3, QTableWidgetItem(_fmt_duration(video.get("duration"))))
            self.table.setItem(row, 4, QTableWidgetItem((video.get("created_at") or "").replace("T", " ")[:19]))

    def _on_upload(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih video untuk di-upload",
            "",
            "Video (*.mp4 *.mkv *.mov *.avi)",
        )
        if not path:
            return
        self.progress.setVisible(True)
        self.upload_button.setEnabled(False)

        def restore() -> None:
            self.progress.setVisible(False)
            self.upload_button.setEnabled(True)

        def on_done(_data: Dict[str, Any]) -> None:
            restore()
            QMessageBox.information(self, "Upload", "Upload berhasil")
            self.refresh()

        def on_err(message: str) -> None:
            restore()
            QMessageBox.critical(self, "Upload gagal", message)

        self.run_async(self.client.upload_video, on_done, path, on_error=on_err)

    def _on_rename(self) -> None:
        video = self.selected_video()
        if not video:
            QMessageBox.information(self, "Rename", "Pilih video dulu.")
            return
        new_name, ok = QInputDialog.getText(
            self,
            "Rename",
            "Nama baru (sertakan ekstensi):",
            text=video.get("original_name") or video.get("filename", ""),
        )
        if not ok or not new_name.strip():
            return
        self.run_async(
            self.client.rename_video,
            lambda _d: self.refresh(),
            video["id"],
            new_name.strip(),
        )

    def _on_delete(self) -> None:
        video = self.selected_video()
        if not video:
            QMessageBox.information(self, "Hapus", "Pilih video dulu.")
            return
        reply = QMessageBox.question(
            self,
            "Konfirmasi",
            f"Hapus video '{video.get('original_name')}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.run_async(
            self.client.delete_video,
            lambda _d: self.refresh(),
            video["id"],
        )
