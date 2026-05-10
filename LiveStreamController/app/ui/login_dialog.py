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

        hint = QLabel(
            "Isi <b>IP VPS</b> (yang biasa dipakai untuk RDP). Jangan pakai 127.0.0.1\n"
            "kecuali server jalan di laptop yang sama."
        )
        hint.setStyleSheet("color: #8d96a3;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()
        self.host_edit = QLineEdit(config.server_host)
        self.host_edit.setPlaceholderText("IP VPS, contoh: 203.0.113.10 atau 192.168.40.54")
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

    def _validate_host(self) -> bool:
        host = self.host_edit.text().strip()
        if not host:
            QMessageBox.warning(
                self,
                "Host kosong",
                "Isi Host / IP VPS dulu.\n\n"
                "Pakai IP yang sama yang kamu pakai untuk RDP ke VPS.",
            )
            return False
        return True

    def _on_test(self) -> None:
        if not self._validate_host():
            return
        client, cfg = self._build_client()
        try:
            if not cfg.api_token and self.password_edit.text():
                client.login(cfg.username, self.password_edit.text())
            client.server_status()
            QMessageBox.information(self, "Tes Koneksi", f"Koneksi ke {cfg.base_url} berhasil.")
        except APIError as exc:
            QMessageBox.critical(self, "Tes Koneksi Gagal", self._friendly_error(exc, cfg))

    def _on_connect(self) -> None:
        if not self._validate_host():
            return
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
            QMessageBox.critical(self, "Gagal Terhubung", self._friendly_error(exc, cfg))
            return

        if cfg.remember_token:
            save_config(cfg)
        else:
            persisted = ControllerConfig(**{**cfg.to_dict(), "api_token": ""})
            save_config(persisted)

        self.config = cfg
        self.accept()

    def _friendly_error(self, exc: APIError, cfg: ControllerConfig) -> str:
        msg = str(exc)
        host = cfg.server_host or "127.0.0.1"
        hints = []
        if "actively refused" in msg or "10061" in msg or "ConnectionRefusedError" in msg:
            hints.append(
                f"Tidak ada server yang dengar di {host}:{cfg.server_port}. "
                "Pastikan: (1) server jalan dengan status hijau di VPS, "
                "(2) Host yang kamu isi adalah IP VPS (bukan 127.0.0.1 dari laptop), "
                "(3) port 8765 dibuka di firewall Windows + firewall provider VPS."
            )
        if "timed out" in msg.lower() or "10060" in msg:
            hints.append(
                f"Timeout konek ke {host}:{cfg.server_port}. "
                "Biasanya port di-block firewall \u2014 buka port 8765 di firewall VPS dan firewall provider."
            )
        if cfg.use_https and "HTTPSConnectionPool" in msg:
            hints.append(
                "Server tidak pakai HTTPS. Hilangkan centang 'Gunakan HTTPS' kecuali kamu pasang reverse proxy TLS sendiri."
            )
        if hints:
            return msg + "\n\n" + "\n\n".join(hints)
        return msg

    def get_result(self) -> Optional[Tuple[ControllerConfig, APIClient]]:
        if self.result() != QDialog.Accepted:
            return None
        client = APIClient(self.config.base_url, self.config.api_token)
        return self.config, client
