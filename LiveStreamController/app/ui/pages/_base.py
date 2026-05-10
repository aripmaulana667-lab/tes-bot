"""Base page class with helper to run API calls in a worker."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtWidgets import QMessageBox, QWidget

from app.api.client import APIClient, APIError
from app.utils.threads import run_in_thread


class BasePage(QWidget):
    def __init__(self, client: APIClient) -> None:
        super().__init__()
        self.client = client

    def set_client(self, client: APIClient) -> None:
        self.client = client

    # ---- threading helpers ------------------------------------------

    def run_async(
        self,
        fn: Callable[..., Any],
        on_result: Callable[[Any], None],
        *args: Any,
        on_error: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        def default_error(message: str) -> None:
            QMessageBox.critical(self, "Error", message)

        run_in_thread(
            self,
            fn,
            on_result,
            on_error or default_error,
            *args,
            **kwargs,
        )

    def call_api(
        self,
        method_name: str,
        on_result: Callable[[Any], None],
        *args: Any,
        on_error: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        method = getattr(self.client, method_name)
        self.run_async(method, on_result, *args, on_error=on_error, **kwargs)

    # ---- error formatting ------------------------------------------

    def format_error(self, exc: APIError | Exception) -> str:
        if isinstance(exc, APIError):
            return str(exc)
        return f"{type(exc).__name__}: {exc}"
