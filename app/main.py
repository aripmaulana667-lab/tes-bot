"""Music Spectrum Lyric Video Maker - application entry point."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_repo_on_path() -> None:
    """Allow `python app/main.py` and `python -m app.main` to both work."""
    here = Path(__file__).resolve().parent.parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))


def main() -> int:
    _ensure_repo_on_path()

    # Qt env tweaks for Windows/HiDPI must happen before QApplication is created.
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    from PySide6.QtWidgets import QApplication

    from app.gui.main_window import MainWindow
    from app.styles.themes import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("Music Spectrum Lyric Video Maker")
    app.setOrganizationName("MSLVM")
    apply_theme(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover - GUI entry point
    raise SystemExit(main())
