"""Initial login / connection dialog."""

from __future__ import annotations

from typing import Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.api.client import APIClient, APIError
from app.utils.config import ControllerConfig, save_config


class LoginDialog(QDialog):
    def __init__(self, config: ControllerConfig) -> None:
        super().__init__()
        self.setWindowTitle("Hubungkan ke Server")
        self.setModal(True)
        self.config = config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Konfigurasi Koneksi Server")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        form = QFormLayout()
        self.host_edit = QLineEdit(config.server_host)
        self.host_edit.setPlaceholderText("contoh: 203.0.113.10 atau vps.example.com")
        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(config.server_port)
        self.https_check = QCheckBox("Gunakan HTTPS")
        self.https_check.setChecked(config.use_https)
        self.username_edit = QLineEdit(config.username)
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("kosongkan jika pakai API token")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.token_edit = QLineEdit(config.api_token)
        self.token_edit.setPlaceholderText("opsional kalau tahu API token-nya")
        self.remember_check = QCheckBox("Simpan token di config")
        self.remember_check.setChecked(config.remember_token)

        form.addRow("Host / IP", self.host_edit)
        form.addRow("Port", self.port_edit)
        form.addRow("", self.https_check)
        form.addRow("Username", self.username_edit)
        form.addRow("Password", self.password_edit)
        form.addRow("API Token", self.token_edit)
        form.addRow("", self.remember_check)
        layout.addLayout(form)

        button_row = QHBoxLayout()
        self.test_button = QPushButton("Tes Koneksi")
        self.test_button.setProperty("secondary", True)
        self.connect_button = QPushButton("Hubungkan")
        button_row.addStretch(1)
        button_row.addWidget(self.test_button)
        button_row.addWidget(self.connect_button)
        layout.addLayout(button_row)

        self.test_button.clicked.connect(self._on_test)
        self.connect_button.clicked.connect(self._on_connect)
        self.password_edit.returnPressed.connect(self._on_connect)

    def _build_client(self) -> Tuple[APIClient, ControllerConfig]:
        cfg = ControllerConfig(
            server_host=self.host_edit.text().strip() or "127.0.0.1",
            server_port=int(self.port_edit.value()),
            use_https=self.https_check.isChecked(),
            api_token=self.token_edit.text().strip(),
            username=self.username_edit.text().strip() or "admin",
            remember_token=self.remember_check.isChecked(),
        )
        client = APIClient(cfg.base_url, cfg.api_token)
        return client, cfg

    def _on_test(self) -> None:
        client, cfg = self._build_client()
        try:
            if not cfg.api_token and self.password_edit.text():
                client.login(cfg.username, self.password_edit.text())
            client.server_status() if cfg.api_token or client.token else client.server_status()
            QMessageBox.information(self, "Tes Koneksi", "Koneksi ke server berhasil.")
        except APIError as exc:
            QMessageBox.critical(self, "Tes Koneksi Gagal", str(exc))

    def _on_connect(self) -> None:
        client, cfg = self._build_client()
        try:
            if not cfg.api_token:
                if not self.password_edit.text():
                    QMessageBox.warning(self, "Login", "Isi password atau API token.")
                    return
                data = client.login(cfg.username, self.password_edit.text())
                cfg.api_token = data.get("api_token", "")
            else:
                client.token = cfg.api_token
            client.server_status()
        except APIError as exc:
            QMessageBox.critical(self, "Gagal Terhubung", str(exc))
            return

        if cfg.remember_token:
            save_config(cfg)
        else:
            persisted = ControllerConfig(**{**cfg.to_dict(), "api_token": ""})
            save_config(persisted)

        self.config = cfg
        self.accept()

    def get_result(self) -> Optional[Tuple[ControllerConfig, APIClient]]:
        if self.result() != QDialog.Accepted:
            return None
        client = APIClient(self.config.base_url, self.config.api_token)
        return self.config, client
