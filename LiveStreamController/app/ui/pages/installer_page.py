"""Installer page: trigger remote install + diagnostics."""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from app.api.client import APIClient
from app.ui.pages._base import BasePage


class InstallerPage(BasePage):
    def __init__(self, client: APIClient) -> None:
        super().__init__(client)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(14)

        title = QLabel("Auto Installer")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        outer.addWidget(title)

        info = QLabel(
            "Tombol di bawah mengirim perintah ke SERVER APP di VPS. "
            "Proses install tetap dilakukan oleh server, controller hanya pemicu."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #c4c9d2;")
        outer.addWidget(info)

        button_row = QHBoxLayout()
        self.install_button = QPushButton("Install FFmpeg")
        self.force_button = QPushButton("Re-install (force)")
        self.force_button.setProperty("secondary", True)
        self.check_button = QPushButton("Cek FFmpeg")
        self.check_button.setProperty("secondary", True)
        self.deps_button = QPushButton("Cek Dependency")
        self.deps_button.setProperty("secondary", True)
        self.health_button = QPushButton("Server Health")
        self.health_button.setProperty("secondary", True)
        for btn in (self.install_button, self.force_button, self.check_button, self.deps_button, self.health_button):
            button_row.addWidget(btn)
        button_row.addStretch(1)
        outer.addLayout(button_row)

        self.install_button.clicked.connect(self._on_install)
        self.force_button.clicked.connect(lambda: self._on_install(True))
        self.check_button.clicked.connect(self._on_check)
        self.deps_button.clicked.connect(self._on_deps)
        self.health_button.clicked.connect(self._on_health)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Output akan tampil di sini...")
        outer.addWidget(self.output, 1)

    def refresh(self) -> None:
        return None

    # ---- handlers --------------------------------------------------

    def _append(self, message: str) -> None:
        self.output.appendPlainText(message)

    def _on_install(self, force: bool = False) -> None:
        self._append(f"-> Install FFmpeg (force={force}) ...")
        self.install_button.setEnabled(False)
        self.force_button.setEnabled(False)

        def restore() -> None:
            self.install_button.setEnabled(True)
            self.force_button.setEnabled(True)

        def on_done(data: Dict[str, Any]) -> None:
            restore()
            status = "BERHASIL" if data.get("installed") else "GAGAL"
            self._append(f"   {status}: {data.get('message', '')}")
            if data.get("path"):
                self._append(f"   path: {data['path']}")
            if data.get("version"):
                self._append(f"   versi: {data['version']}")

        def on_err(message: str) -> None:
            restore()
            self._append(f"   ERROR: {message}")
            QMessageBox.critical(self, "Install gagal", message)

        self.run_async(self.client.install_ffmpeg, on_done, force, on_error=on_err)

    def _on_check(self) -> None:
        self._append("-> Cek FFmpeg ...")
        self.run_async(
            self.client.check_ffmpeg,
            lambda d: self._append(
                f"   installed={d.get('installed')} path={d.get('path')} version={(d.get('version') or '')[:80]}"
            ),
            on_error=lambda m: self._append(f"   ERROR: {m}"),
        )

    def _on_deps(self) -> None:
        self._append("-> Cek dependency Python di server ...")
        self.run_async(
            self.client.check_deps,
            lambda d: self._append(f"   ok={d.get('ok')} {d.get('message')}"),
            on_error=lambda m: self._append(f"   ERROR: {m}"),
        )

    def _on_health(self) -> None:
        self._append("-> Server status ...")
        self.run_async(
            self.client.server_status,
            lambda d: self._append(
                f"   app={d.get('app')} uptime={d.get('uptime_seconds'):.0f}s"
                f" ffmpeg={d.get('ffmpeg_installed')} active={d.get('active_streams')}"
            ),
            on_error=lambda m: self._append(f"   ERROR: {m}"),
        )
