"""LiveStream Server entry point.

Default:    launches the GUI (server_gui.py) so the user can copy
            host/port/username/password/api token easily.
Headless:   pass ``--console`` to run uvicorn directly without GUI.

Run:
    python server_app.py            # GUI
    python server_app.py --console  # headless / no GUI
"""

from __future__ import annotations

import os
import sys


_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def _run_console() -> None:
    import uvicorn

    from app.config import get_settings
    from app.utils.bootstrap import bootstrap_environment

    settings = get_settings()
    bootstrap_environment(settings)

    print(f"[{settings.app_name}] Starting on {settings.host}:{settings.port}")
    print(f"[{settings.app_name}] Base dir: {settings.base_dir}")
    print(f"[{settings.app_name}] Videos dir: {settings.videos_dir}")
    print(f"[{settings.app_name}] Username: {settings.default_admin_username}")
    print(f"[{settings.app_name}] Password: {settings.default_admin_password}")
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


def _run_gui() -> int:
    try:
        from server_gui import main as gui_main  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        print(f"[LiveStreamServer] GUI tidak bisa dimuat ({exc}). Jatuh kembali ke mode console.")
        _run_console()
        return 0
    return gui_main()


def main() -> None:
    args = set(sys.argv[1:])
    if "--console" in args or "--headless" in args or "--no-gui" in args:
        _run_console()
        return
    raise SystemExit(_run_gui())


if __name__ == "__main__":
    main()
