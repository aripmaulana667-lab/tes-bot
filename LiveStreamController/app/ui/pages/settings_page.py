"""Settings page (connection + about)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.api.client import APIClient
from app.ui.pages._base import BasePage
from app.utils.config import ControllerConfig, save_config


class SettingsPage(BasePage):
    connection_changed = Signal(ControllerConfig)

    def __init__(self, config: ControllerConfig, client: APIClient) -> None:
        super().__init__(client)
        self.config = config

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        outer.addWidget(title)

        form = QFormLayout()
        self.host_edit = QLineEdit(config.server_host)
        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(config.server_port)
        self.https_check = QCheckBox("Gunakan HTTPS")
        self.https_check.setChecked(config.use_https)
        self.username_edit = QLineEdit(config.username)
        self.token_edit = QLineEdit(config.api_token)
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.remember_check = QCheckBox("Simpan token di config.json")
        self.remember_check.setChecked(config.remember_token)

        form.addRow("Host", self.host_edit)
        form.addRow("Port", self.port_edit)
        form.addRow("", self.https_check)
        form.addRow("Username", self.username_edit)
        form.addRow("API Token", self.token_edit)
        form.addRow("", self.remember_check)
        outer.addLayout(form)

        button_row = QHBoxLayout()
        self.test_button = QPushButton("Tes Koneksi")
        self.test_button.setProperty("secondary", True)
        self.save_button = QPushButton("Simpan")
        button_row.addStretch(1)
        button_row.addWidget(self.test_button)
        button_row.addWidget(self.save_button)
        outer.addLayout(button_row)

        self.test_button.clicked.connect(self._on_test)
        self.save_button.clicked.connect(self._on_save)

        outer.addStretch(1)

    def refresh(self) -> None:
        return None

    # ---- helpers ----------------------------------------------------

    def _build_config(self) -> ControllerConfig:
        return ControllerConfig(
            server_host=self.host_edit.text().strip() or "127.0.0.1",
            server_port=int(self.port_edit.value()),
            use_https=self.https_check.isChecked(),
            api_token=self.token_edit.text().strip(),
            username=self.username_edit.text().strip() or "admin",
            remember_token=self.remember_check.isChecked(),
        )

    def _on_test(self) -> None:
        cfg = self._build_config()
        client = APIClient(cfg.base_url, cfg.api_token)
        try:
            client.server_status()
            QMessageBox.information(self, "Tes Koneksi", "Berhasil terhubung.")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Tes Koneksi Gagal", str(exc))

    def _on_save(self) -> None:
        cfg = self._build_config()
        if cfg.remember_token:
            save_config(cfg)
        else:
            save_config(ControllerConfig(**{**cfg.to_dict(), "api_token": ""}))
        self.config = cfg
        self.connection_changed.emit(cfg)
        QMessageBox.information(self, "Settings", "Pengaturan disimpan.")
