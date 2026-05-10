"""Dashboard page with server status and resource cards."""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.api.client import APIClient
from app.ui.pages._base import BasePage
from app.ui.widgets.stat_card import StatCard


def _fmt_seconds(seconds: float) -> str:
    seconds = int(max(0, seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class DashboardPage(BasePage):
    def __init__(self, client: APIClient) -> None:
        super().__init__(client)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch(1)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setProperty("secondary", True)
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(self.refresh_button)
        outer.addLayout(header)

        self.status_label = QLabel("Status server: -")
        self.status_label.setStyleSheet("color: #c4c9d2;")
        outer.addWidget(self.status_label)

        grid = QGridLayout()
        grid.setSpacing(14)
        outer.addLayout(grid)

        self.cpu_card = StatCard("CPU")
        self.ram_card = StatCard("RAM")
        self.disk_card = StatCard("Disk")
        self.video_card = StatCard("Storage Video")
        self.streams_card = StatCard("Live Aktif")
        self.uptime_card = StatCard("Uptime Server")
        self.ffmpeg_card = StatCard("FFmpeg")
        self.connection_card = StatCard("Server")

        cards = [
            self.cpu_card,
            self.ram_card,
            self.disk_card,
            self.video_card,
            self.streams_card,
            self.uptime_card,
            self.ffmpeg_card,
            self.connection_card,
        ]
        for index, card in enumerate(cards):
            grid.addWidget(card, index // 4, index % 4)

        outer.addStretch(1)

    # ---- public ----------------------------------------------------

    def refresh(self) -> None:
        if not self.client.base_url:
            self.status_label.setText("Belum terhubung ke server.")
            return
        self.status_label.setText("Memuat data...")
        self.call_api("server_status", self._on_status, on_error=self._on_status_error)

    # ---- callbacks --------------------------------------------------

    def _on_status(self, data: Dict[str, Any]) -> None:
        self.status_label.setText("Server online")
        self.connection_card.set_value(data.get("app", "?"), data.get("base_dir", ""))
        self.uptime_card.set_value(_fmt_seconds(data.get("uptime_seconds", 0)), "uptime")
        self.streams_card.set_value(str(data.get("active_streams", 0)), "live aktif")
        ffmpeg = data.get("ffmpeg_installed")
        version = data.get("ffmpeg_version") or ""
        self.ffmpeg_card.set_value(
            "Installed" if ffmpeg else "Belum",
            (version[:48] + "...") if len(version) > 48 else version,
        )
        self.call_api("system_resources", self._on_resources)

    def _on_status_error(self, message: str) -> None:
        self.status_label.setText(f"Server offline / error: {message}")

    def _on_resources(self, data: Dict[str, Any]) -> None:
        cpu = data.get("cpu_percent", 0)
        ram = data.get("ram_percent", 0)
        ram_used = data.get("ram_used_mb", 0)
        ram_total = data.get("ram_total_mb", 1)
        disk_used = data.get("disk_used_mb", 0)
        disk_total = data.get("disk_total_mb", 1)
        videos_used = data.get("videos_dir_used_mb", 0)

        self.cpu_card.set_value(f"{cpu:.1f}%", "rata-rata")
        self.ram_card.set_value(f"{ram:.1f}%", f"{ram_used:.0f} / {ram_total:.0f} MB")
        self.disk_card.set_value(
            f"{(disk_used / max(disk_total, 1) * 100):.1f}%",
            f"{disk_used / 1024:.1f} / {disk_total / 1024:.1f} GB",
        )
        self.video_card.set_value(f"{videos_used:.1f} MB", "folder videos")
