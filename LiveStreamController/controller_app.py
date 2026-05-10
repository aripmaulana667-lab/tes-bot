"""LiveStream Controller entry point.

Run with:  python controller_app.py
"""

from __future__ import annotations

import os
import sys


_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.utils.config import load_config


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("LiveStream Controller")
    app.setStyle("Fusion")

    config = load_config()
    window = MainWindow(config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
