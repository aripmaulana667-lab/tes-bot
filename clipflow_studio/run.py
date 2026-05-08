"""Entry-point launcher for ClipFlow Studio.

This script is intentionally tiny so that ``run.bat`` and direct ``python run.py``
invocations behave identically.  All real work happens in :mod:`app.main`.
"""
from __future__ import annotations

import os
import sys


def _bootstrap() -> None:
    """Make the ``app`` package importable when launched as ``python run.py``."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def main() -> int:
    _bootstrap()
    from app.main import main as app_main  # noqa: WPS433 (local import on purpose)

    return app_main()


if __name__ == "__main__":
    sys.exit(main() or 0)
