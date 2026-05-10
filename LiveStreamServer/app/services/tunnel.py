"""Cloudflare quick-tunnel manager.

Runs ``cloudflared.exe tunnel --url http://localhost:<port>`` so the
server is reachable from the internet without opening any inbound port
on the VPS. Cloudflared connects out to Cloudflare on TCP/443 and
returns a public URL of the form ``https://<random>.trycloudflare.com``
that the controller on the laptop can hit directly.

This module:

- downloads ``cloudflared.exe`` (or the appropriate binary for non-Windows
  hosts when developing) on first use,
- spawns the tunnel as a subprocess,
- parses the public URL from cloudflared's stdout,
- exposes start / stop / status helpers and a callback for URL updates.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import threading
import time
from typing import Callable, Optional

import requests

from app.config import Settings, get_settings


_CF_RELEASES = {
    "windows-amd64": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
    "linux-amd64": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
    "linux-arm64": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64",
    "darwin-amd64": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz",
}


_CREATE_NO_WINDOW = 0x08000000  # Windows-only flag for subprocess


def _platform_key() -> str:
    if os.name == "nt":
        return "windows-amd64"
    import platform

    machine = platform.machine().lower()
    if "arm" in machine or "aarch64" in machine:
        return "linux-arm64"
    if "darwin" in os.uname().sysname.lower():  # type: ignore[attr-defined]
        return "darwin-amd64"
    return "linux-amd64"


def _binary_name() -> str:
    return "cloudflared.exe" if os.name == "nt" else "cloudflared"


def cloudflared_path(settings: Optional[Settings] = None) -> str:
    settings = settings or get_settings()
    return os.path.join(settings.bin_dir, "cloudflared", _binary_name())


def is_installed(settings: Optional[Settings] = None) -> bool:
    return os.path.isfile(cloudflared_path(settings))


def install_cloudflared(
    settings: Optional[Settings] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> str:
    """Download cloudflared if missing. Returns absolute path."""

    settings = settings or get_settings()
    target = cloudflared_path(settings)
    if os.path.isfile(target):
        return target

    os.makedirs(os.path.dirname(target), exist_ok=True)
    url = _CF_RELEASES[_platform_key()]

    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        downloaded = 0
        tmp = target + ".part"
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=131072):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if progress:
                    try:
                        progress(downloaded, total)
                    except Exception:  # noqa: BLE001
                        pass
        shutil.move(tmp, target)

    if os.name != "nt":
        try:
            os.chmod(target, 0o755)
        except OSError:
            pass

    return target


_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


class TunnelManager:
    """Owns a single cloudflared subprocess + the URL it produces."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._proc: Optional[subprocess.Popen] = None
        self._reader: Optional[threading.Thread] = None
        self._url: Optional[str] = None
        self._lock = threading.Lock()
        self._on_url: Optional[Callable[[str], None]] = None
        self._on_log: Optional[Callable[[str], None]] = None
        self._on_exit: Optional[Callable[[int], None]] = None

    # ------------------------------------------------------------------
    # callbacks
    # ------------------------------------------------------------------
    def on_url(self, cb: Callable[[str], None]) -> None:
        self._on_url = cb

    def on_log(self, cb: Callable[[str], None]) -> None:
        self._on_log = cb

    def on_exit(self, cb: Callable[[int], None]) -> None:
        self._on_exit = cb

    # ------------------------------------------------------------------
    # state
    # ------------------------------------------------------------------
    @property
    def url(self) -> Optional[str]:
        return self._url

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    # ------------------------------------------------------------------
    # control
    # ------------------------------------------------------------------
    def start(self) -> None:
        with self._lock:
            if self.is_running:
                return
            binary = cloudflared_path(self.settings)
            if not os.path.isfile(binary):
                install_cloudflared(self.settings, progress=lambda d, t: self._emit_log(
                    f"download cloudflared: {d}/{t} bytes"
                ) if t else None)

            target = f"http://127.0.0.1:{self.settings.port}"
            cmd = [
                binary,
                "tunnel",
                "--no-autoupdate",
                "--url",
                target,
            ]
            self._url = None
            kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "bufsize": 1,
            }
            if os.name == "nt":
                kwargs["creationflags"] = _CREATE_NO_WINDOW
            self._proc = subprocess.Popen(cmd, **kwargs)  # noqa: S603
            self._reader = threading.Thread(target=self._read_loop, daemon=True)
            self._reader.start()

    def stop(self) -> None:
        with self._lock:
            proc = self._proc
            self._proc = None
            self._url = None
        if proc is None:
            return
        try:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _read_loop(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:
            return
        for raw in proc.stdout:
            line = raw.rstrip("\r\n")
            self._emit_log(line)
            if self._url is None:
                m = _URL_RE.search(line)
                if m:
                    self._url = m.group(0)
                    if self._on_url:
                        try:
                            self._on_url(self._url)
                        except Exception:  # noqa: BLE001
                            pass
        rc = proc.wait()
        if self._on_exit:
            try:
                self._on_exit(rc)
            except Exception:  # noqa: BLE001
                pass

    def _emit_log(self, line: str) -> None:
        if self._on_log:
            try:
                self._on_log(line)
            except Exception:  # noqa: BLE001
                pass


_global: Optional[TunnelManager] = None


def get_tunnel() -> TunnelManager:
    global _global
    if _global is None:
        _global = TunnelManager()
    return _global
