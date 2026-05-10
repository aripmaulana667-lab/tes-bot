"""Reusable QThread worker helpers."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Signal


class Worker(QObject):
    """Run a callable on a worker thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
        else:
            self.finished.emit(result)


def run_in_thread(
    parent: QObject,
    fn: Callable[..., Any],
    on_result: Callable[[Any], None],
    on_error: Callable[[str], None],
    *args: Any,
    **kwargs: Any,
) -> QThread:
    """Helper that wires up a QThread + Worker and returns the thread."""

    thread = QThread(parent)
    worker = Worker(fn, *args, **kwargs)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(on_result)
    worker.failed.connect(on_error)

    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()
    return thread
