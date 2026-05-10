"""Main window of the controller app."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QStatusBar, QWidget

from app.api.client import APIClient
from app.ui.login_dialog import LoginDialog
from app.ui.pages.accounts_page import AccountsPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.installer_page import InstallerPage
from app.ui.pages.logs_page import LogsPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.streams_page import StreamsPage
from app.ui.pages.videos_page import VideosPage
from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.styles import STYLESHEET
from app.utils.config import ControllerConfig


NAV_ITEMS = [
    "Dashboard",
    "Videos",
    "Accounts",
    "Streams",
    "Installer",
    "Logs",
    "Settings",
]


class MainWindow(QMainWindow):
    def __init__(self, config: ControllerConfig) -> None:
        super().__init__()
        self.setWindowTitle("LiveStream Controller")
        self.resize(1200, 720)
        self.setStyleSheet(STYLESHEET)

        self.config = config
        self.client = APIClient(config.base_url, config.api_token)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(central)

        self.sidebar = Sidebar(NAV_ITEMS)
        layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.dashboard_page = DashboardPage(self.client)
        self.videos_page = VideosPage(self.client)
        self.accounts_page = AccountsPage(self.client)
        self.streams_page = StreamsPage(self.client)
        self.installer_page = InstallerPage(self.client)
        self.logs_page = LogsPage(self.client)
        self.settings_page = SettingsPage(self.config, self.client)
        self.settings_page.connection_changed.connect(self._on_connection_changed)

        for page in [
            self.dashboard_page,
            self.videos_page,
            self.accounts_page,
            self.streams_page,
            self.installer_page,
            self.logs_page,
            self.settings_page,
        ]:
            self.stack.addWidget(page)

        self.sidebar.navigated.connect(self._on_nav)

        status = QStatusBar()
        self.setStatusBar(status)
        self._update_status()

        # If we have no token, prompt the user immediately.
        if not self.config.api_token:
            QTimer.singleShot(50, self._open_login_dialog)
        else:
            QTimer.singleShot(50, self.dashboard_page.refresh)

    # ---- helpers ----------------------------------------------------

    def _on_nav(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()

    def _open_login_dialog(self) -> None:
        dialog = LoginDialog(self.config)
        if dialog.exec():
            result = dialog.get_result()
            if result is not None:
                cfg, client = result
                self.config = cfg
                self.client.update_connection(cfg.base_url, cfg.api_token)
                self._broadcast_client()
                self._update_status()
                self.dashboard_page.refresh()

    def _on_connection_changed(self, cfg: ControllerConfig) -> None:
        self.config = cfg
        self.client.update_connection(cfg.base_url, cfg.api_token)
        self._broadcast_client()
        self._update_status()
        self.dashboard_page.refresh()

    def _broadcast_client(self) -> None:
        for page in (
            self.dashboard_page,
            self.videos_page,
            self.accounts_page,
            self.streams_page,
            self.installer_page,
            self.logs_page,
            self.settings_page,
        ):
            if hasattr(page, "set_client"):
                page.set_client(self.client)

    def _update_status(self) -> None:
        if self.client.base_url:
            self.statusBar().showMessage(f"Server: {self.client.base_url}")
        else:
            self.statusBar().showMessage("Belum terhubung")
