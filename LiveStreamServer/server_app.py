"""LiveStream Server entry point.

Run with:  python server_app.py
"""

from __future__ import annotations

import os
import sys

# Ensure the local app package is importable when run directly.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import uvicorn

from app.config import get_settings
from app.utils.bootstrap import bootstrap_environment


def main() -> None:
    settings = get_settings()
    bootstrap_environment(settings)

    print(f"[{settings.app_name}] Starting on {settings.host}:{settings.port}")
    print(f"[{settings.app_name}] Base dir: {settings.base_dir}")
    print(f"[{settings.app_name}] Videos dir: {settings.videos_dir}")
    if settings.api_token:
        print(f"[{settings.app_name}] API token: {settings.api_token}")
    print(f"[{settings.app_name}] Open http://{settings.host}:{settings.port}/docs for the OpenAPI UI.")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
