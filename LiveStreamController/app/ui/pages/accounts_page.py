"""Accounts management page."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
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
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.api.client import APIClient
from app.ui.pages._base import BasePage


PLATFORMS = ["YouTube", "Facebook", "TikTok", "Custom RTMP"]


class AccountDialog(QDialog):
    def __init__(self, account: Optional[Dict[str, Any]] = None) -> None:
        super().__init__()
        self.setWindowTitle("Akun Live")
        self.setModal(True)
        self.account = account or {}

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit(self.account.get("name", ""))
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(PLATFORMS)
        if self.account.get("platform"):
            idx = self.platform_combo.findText(self.account["platform"], Qt.MatchFixedString)
            if idx >= 0:
                self.platform_combo.setCurrentIndex(idx)
            else:
                self.platform_combo.setEditText(self.account["platform"])
        self.platform_combo.setEditable(True)

        self.rtmp_edit = QLineEdit(self.account.get("rtmp_url", ""))
        self.key_edit = QLineEdit("")
        self.key_edit.setPlaceholderText(
            "kosongkan untuk biarkan tidak berubah" if account else "stream key dari platform"
        )
        self.key_edit.setEchoMode(QLineEdit.Password)

        self.bitrate_edit = QLineEdit(self.account.get("default_bitrate", "2500k"))
        self.resolution_edit = QLineEdit(self.account.get("default_resolution", "1280x720"))
        self.active_check = QCheckBox("Aktif")
        self.active_check.setChecked(bool(self.account.get("is_active", True)))

        form.addRow("Nama", self.name_edit)
        form.addRow("Platform", self.platform_combo)
        form.addRow("RTMP URL", self.rtmp_edit)
        form.addRow("Stream Key", self.key_edit)
        form.addRow("Bitrate default", self.bitrate_edit)
        form.addRow("Resolusi default", self.resolution_edit)
        form.addRow("", self.active_check)
        layout.addLayout(form)

        if self.account.get("stream_key_masked"):
            current = QLabel(f"Stream key saat ini: {self.account['stream_key_masked']}")
            current.setStyleSheet("color: #8d96a3;")
            layout.addWidget(current)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def payload(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": self.name_edit.text().strip(),
            "platform": self.platform_combo.currentText().strip() or "Custom RTMP",
            "rtmp_url": self.rtmp_edit.text().strip(),
            "default_bitrate": self.bitrate_edit.text().strip() or "2500k",
            "default_resolution": self.resolution_edit.text().strip() or "1280x720",
            "is_active": self.active_check.isChecked(),
        }
        if self.key_edit.text():
            data["stream_key"] = self.key_edit.text().strip()
        return data


class AccountsPage(BasePage):
    COLUMNS = ["ID", "Nama", "Platform", "RTMP URL", "Stream Key", "Bitrate", "Resolusi", "Aktif"]

    def __init__(self, client: APIClient) -> None:
        super().__init__(client)
        self._items: List[Dict[str, Any]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Akun Live")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch(1)

        self.add_button = QPushButton("Tambah Akun")
        self.edit_button = QPushButton("Edit")
        self.edit_button.setProperty("secondary", True)
        self.toggle_button = QPushButton("Aktif/Nonaktif")
        self.toggle_button.setProperty("secondary", True)
        self.delete_button = QPushButton("Hapus")
        self.delete_button.setProperty("danger", True)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", True)

        for btn in (self.add_button, self.edit_button, self.toggle_button, self.delete_button, self.refresh_button):
            header.addWidget(btn)
        outer.addLayout(header)

        self.add_button.clicked.connect(self._on_add)
        self.edit_button.clicked.connect(self._on_edit)
        self.toggle_button.clicked.connect(self._on_toggle)
        self.delete_button.clicked.connect(self._on_delete)
        self.refresh_button.clicked.connect(self.refresh)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        outer.addWidget(self.table, 1)

    def refresh(self) -> None:
        self.call_api("list_accounts", self._on_list)

    def selected(self) -> Optional[Dict[str, Any]]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        index = rows[0].row()
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def _on_list(self, items: List[Dict[str, Any]]) -> None:
        self._items = items or []
        self.table.setRowCount(len(self._items))
        for row, acc in enumerate(self._items):
            cells = [
                str(acc.get("id")),
                acc.get("name", ""),
                acc.get("platform", ""),
                acc.get("rtmp_url", ""),
                acc.get("stream_key_masked", ""),
                acc.get("default_bitrate", ""),
                acc.get("default_resolution", ""),
                "Ya" if acc.get("is_active") else "Tidak",
            ]
            for col, value in enumerate(cells):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def _on_add(self) -> None:
        dialog = AccountDialog()
        if dialog.exec() != QDialog.Accepted:
            return
        payload = dialog.payload()
        if not payload.get("stream_key"):
            QMessageBox.warning(self, "Akun", "Stream key wajib diisi.")
            return
        self.run_async(self.client.create_account, lambda _d: self.refresh(), payload)

    def _on_edit(self) -> None:
        acc = self.selected()
        if not acc:
            return
        dialog = AccountDialog(acc)
        if dialog.exec() != QDialog.Accepted:
            return
        self.run_async(
            self.client.update_account,
            lambda _d: self.refresh(),
            acc["id"],
            dialog.payload(),
        )

    def _on_toggle(self) -> None:
        acc = self.selected()
        if not acc:
            return
        new_status = not acc.get("is_active", True)
        self.run_async(
            self.client.update_account,
            lambda _d: self.refresh(),
            acc["id"],
            {"is_active": new_status},
        )

    def _on_delete(self) -> None:
        acc = self.selected()
        if not acc:
            return
        reply = QMessageBox.question(
            self,
            "Konfirmasi",
            f"Hapus akun '{acc.get('name')}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.run_async(self.client.delete_account, lambda _d: self.refresh(), acc["id"])
