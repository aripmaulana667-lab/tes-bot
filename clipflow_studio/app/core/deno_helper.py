"""Helper that drives the Deno fallback scripts.

Deno is **not** the primary downloader.  We use it for:

- Lightweight YouTube URL validation when the Python regex check refuses a URL.
- Fetching basic public metadata when yt-dlp fails (e.g. read the page title).
- Persisting an error log next to the project so the user can debug.

All scripts live in ``app/helpers/deno/`` and are invoked through the local
``tools/deno/deno`` binary when available, otherwise the global ``deno``.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from ..utils import config as cfg
from ..utils.logger import get_logger
from . import dependency_manager as deps

_LOG = get_logger("deno")


def get_deno_path() -> Optional[str]:
    return deps.get_deno_path()


def save_deno_path(path: str) -> None:
    deps.save_deno_path(path)


def check_deno():  # type: ignore[no-untyped-def]
    return deps.check_deno()


def install_deno_windows(progress=None):  # type: ignore[no-untyped-def]
    return deps.install_deno_windows(progress=progress)


def get_helper_dir() -> str:
    return os.path.join(
        cfg.get_project_root(), "app", "helpers", "deno"
    )


def get_helper_script(name: str) -> str:
    return os.path.join(get_helper_dir(), name)


def _save_error_log(payload: Dict[str, Any]) -> str:
    logs_dir = cfg.get_logs_dir()
    path = os.path.join(logs_dir, f"deno_error_{int(time.time() * 1000)}.json")
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
    except OSError:
        _LOG.warning("Failed to write Deno error log to %s", path)
    return path


def run_deno_script(script_path: str, args: List[str]) -> Tuple[bool, Dict[str, Any], str]:
    """Run a Deno script.

    Returns a tuple ``(ok, parsed_json, raw_stderr)``.
    The script must print a single JSON object on stdout for ``parsed_json``
    to be populated; otherwise the function falls back to ``{}`` and returns
    ``ok=False``.
    """
    deno = get_deno_path()
    if not deno:
        _LOG.warning("Deno is not installed; cannot run %s", script_path)
        return False, {"error": "deno_not_installed"}, ""
    if not os.path.exists(script_path):
        return False, {"error": f"script_not_found: {script_path}"}, ""

    cmd = [
        deno,
        "run",
        "--quiet",
        "--allow-net",
        "--allow-read",
        script_path,
        *args,
    ]
    _LOG.info("Running Deno: %s", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        return False, {"error": str(exc)}, ""
    except subprocess.TimeoutExpired:
        return False, {"error": "deno_timeout"}, ""

    stderr = proc.stderr.decode(errors="ignore")
    stdout = proc.stdout.decode(errors="ignore").strip()
    if proc.returncode != 0:
        _save_error_log(
            {
                "script": script_path,
                "args": args,
                "returncode": proc.returncode,
                "stderr": stderr,
                "stdout": stdout,
            }
        )
        return False, {"error": stderr.strip() or "deno_failed"}, stderr

    try:
        parsed = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        parsed = {"raw": stdout}
    return True, parsed, stderr


def validate_youtube_url_with_deno(url: str) -> Dict[str, Any]:
    script = get_helper_script("validate_url.ts")
    ok, data, _stderr = run_deno_script(script, [url])
    if not ok:
        return {"valid": False, "platform": None, "url": url, "error": data.get("error")}
    return data


def fetch_video_metadata_with_deno(url: str) -> Dict[str, Any]:
    script = get_helper_script("fetch_metadata.ts")
    ok, data, _stderr = run_deno_script(script, [url])
    if not ok:
        return {"status": "error", "url": url, "error": data.get("error"), "platform": "youtube"}
    return data
