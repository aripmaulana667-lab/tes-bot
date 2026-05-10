"""Tkinter GUI launcher for the LiveStream Server.

Menampilkan Host/IP, Port, Username, Password, API Token dengan tombol
copy, plus Start/Stop server dan tail log. Tkinter sudah bawaan Python,
tidak perlu install tambahan.

Run with:  python server_gui.py
"""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import tkinter as tk
import webbrowser
from collections import deque
from tkinter import messagebox, ttk
from typing import Deque, List, Optional


_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


# We import lazily inside callbacks where it makes sense, so that an early
# import error still surfaces in the GUI rather than killing the launcher
# silently.
def _bootstrap_settings():
    from app.config import get_settings  # noqa: WPS433
    from app.utils.bootstrap import bootstrap_environment  # noqa: WPS433

    settings = get_settings()
    bootstrap_environment(settings)
    return settings


def _detect_local_ips() -> List[str]:
    """Return a deduplicated list of plausible LAN IPs."""

    ips: List[str] = ["127.0.0.1"]

    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and ip not in ips:
            ips.append(ip)
    except OSError:
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ip and ":" not in ip and ip not in ips:
                ips.append(ip)
    except OSError:
        pass

    # The classic UDP socket trick to find the outbound LAN IP.
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        if ip and ip not in ips:
            ips.append(ip)
    except OSError:
        pass

    return ips


class _LogBuffer(logging.Handler):
    """Logging handler that pushes lines into a deque and a Tk Text widget."""

    def __init__(self, sink: Deque[str], tk_text: tk.Text) -> None:
        super().__init__(level=logging.INFO)
        self._sink = sink
        self._tk_text = tk_text
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
        except Exception:  # noqa: BLE001
            return
        self._sink.append(line)
        try:
            self._tk_text.after(0, self._append, line)
        except RuntimeError:
            # Tk has been destroyed.
            pass

    def _append(self, line: str) -> None:
        try:
            self._tk_text.configure(state="normal")
            self._tk_text.insert("end", line + "\n")
            self._tk_text.see("end")
            self._tk_text.configure(state="disabled")
        except tk.TclError:
            pass


class _ServerThread(threading.Thread):
    """Run uvicorn in a background thread so Tk can keep the main loop."""

    def __init__(self, host: str, port: int) -> None:
        super().__init__(daemon=True, name="uvicorn-server")
        self.host = host
        self.port = port
        self._server: Optional["uvicorn.Server"] = None  # noqa: F821
        self._started = threading.Event()
        self._stopped = threading.Event()

    def run(self) -> None:
        import uvicorn  # local import: heavy

        config = uvicorn.Config(
            "app.main:app",
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False,
            # Don't let uvicorn reset logging — we install our own handler that
            # forwards records into the GUI text widget.
            log_config=None,
        )
        server = uvicorn.Server(config)
        # Disable signal handlers because we're not on the main thread.
        server.install_signal_handlers = lambda: None  # type: ignore[assignment]
        self._server = server
        try:
            self._started.set()
            server.run()
        finally:
            self._stopped.set()

    def stop(self, timeout: float = 8.0) -> None:
        if self._server is not None:
            self._server.should_exit = True
        self._stopped.wait(timeout=timeout)


class ServerWindow(tk.Tk):
    PALETTE = {
        "bg": "#1c1f24",
        "card": "#232830",
        "muted": "#8d96a3",
        "fg": "#ffffff",
        "accent": "#2c6bff",
        "ok": "#27c46c",
        "err": "#e25555",
    }

    def __init__(self) -> None:
        super().__init__()
        self.title("LiveStream Server")
        self.geometry("820x720")
        self.configure(bg=self.PALETTE["bg"])
        self.minsize(720, 520)

        self.settings = _bootstrap_settings()

        self._server_thread: Optional[_ServerThread] = None
        self._log_buffer: Deque[str] = deque(maxlen=600)
        self._show_password = tk.BooleanVar(value=False)
        self._show_token = tk.BooleanVar(value=False)
        self._host_var = tk.StringVar()
        self._available_ips = _detect_local_ips()
        if self._available_ips:
            self._host_var.set(self._available_ips[0])

        self._build_styles()
        self._build_layout()
        self._refresh_ffmpeg_label()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # Auto-start server so the controller can connect right away.
        self.after(150, self._start_server)

    # ---- styling ---------------------------------------------------

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        bg, card, fg, muted, accent = (
            self.PALETTE["bg"], self.PALETTE["card"], self.PALETTE["fg"],
            self.PALETTE["muted"], self.PALETTE["accent"],
        )
        style.configure(".", background=bg, foreground=fg, fieldbackground=card)
        style.configure("Card.TFrame", background=card)
        style.configure("Header.TLabel", background=bg, foreground=fg, font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", background=bg, foreground=muted, font=("Segoe UI", 10))
        style.configure("Field.TLabel", background=card, foreground=muted, font=("Segoe UI", 10))
        style.configure("Status.TLabel", background=card, foreground=fg, font=("Segoe UI", 11, "bold"))
        style.configure("TButton", padding=6)
        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#ffffff",
            borderwidth=0,
            padding=8,
        )
        style.map("Accent.TButton", background=[("active", "#3b78ff")])
        style.configure(
            "Secondary.TButton",
            background="#2a313b",
            foreground="#d6dae3",
            padding=6,
            borderwidth=0,
        )
        style.map("Secondary.TButton", background=[("active", "#313945")])
        style.configure("TEntry", fieldbackground=card, foreground=fg, insertcolor=fg)
        style.configure("TCombobox", fieldbackground=card, foreground=fg)

    # ---- layout ----------------------------------------------------

    def _build_layout(self) -> None:
        bg = self.PALETTE["bg"]
        outer = tk.Frame(self, bg=bg)
        outer.pack(fill="both", expand=True, padx=18, pady=14)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        header = tk.Frame(outer, bg=bg)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="LiveStream Server", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        self.status_dot = tk.Label(header, text="● starting", bg=bg, fg=self.PALETTE["muted"], font=("Segoe UI", 11, "bold"))
        self.status_dot.grid(row=0, column=1, sticky="e", padx=(8, 0))

        sub = ttk.Label(
            outer,
            text="Salin Host/IP + Port + API Token ke aplikasi controller di laptop kamu.",
            style="Sub.TLabel",
        )
        sub.grid(row=1, column=0, sticky="w", pady=(2, 12))

        # ---- connection info card ---------------------------------
        card = ttk.Frame(outer, style="Card.TFrame", padding=16)
        card.grid(row=2, column=0, sticky="nsew")
        card.columnconfigure(1, weight=1)

        self._row = 0
        self.host_combo = self._row_combo(card, "Host / IP", self._host_var, self._available_ips)
        self.port_value = self._row_text(card, "Port", str(self.settings.port))
        self.user_value = self._row_text(card, "Username", self.settings.default_admin_username)
        self.pwd_value = self._row_secret(
            card,
            "Password",
            self.settings.default_admin_password,
            self._show_password,
        )
        self.token_value = self._row_secret(
            card,
            "API Token",
            self.settings.api_token,
            self._show_token,
        )
        self.base_url_var = tk.StringVar(value=self._compute_base_url())
        self.base_url_entry = self._row_entry(card, "Base URL", self.base_url_var)
        self._host_var.trace_add("write", lambda *_: self.base_url_var.set(self._compute_base_url()))

        # ---- tunnel URL row ---------------------------------------
        self.tunnel_url_var = tk.StringVar(value="(belum aktif)")
        self.tunnel_url_entry = self._row_entry(card, "Tunnel URL", self.tunnel_url_var)

        # ---- ffmpeg status ----------------------------------------
        self.ffmpeg_label = ttk.Label(card, text="FFmpeg: ...", style="Status.TLabel")
        self.ffmpeg_label.grid(row=self._row, column=0, columnspan=3, sticky="w", pady=(12, 0))
        self._row += 1

        # ---- action row -------------------------------------------
        actions = tk.Frame(card, bg=self.PALETTE["card"])
        actions.grid(row=self._row, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        self._row += 1
        ttk.Button(actions, text="Start Server", style="Accent.TButton", command=self._start_server).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Stop", style="Secondary.TButton", command=self._stop_server).pack(side="left", padx=6)
        ttk.Button(actions, text="Buka Port Firewall", style="Secondary.TButton", command=self._open_firewall).pack(side="left", padx=6)
        ttk.Button(actions, text="Open /docs", style="Secondary.TButton", command=self._open_docs).pack(side="left", padx=6)
        ttk.Button(actions, text="Copy ALL", style="Secondary.TButton", command=self._copy_all).pack(side="left", padx=6)
        ttk.Button(actions, text="Refresh IPs", style="Secondary.TButton", command=self._refresh_ips).pack(side="left", padx=6)

        # ---- tunnel actions row -----------------------------------
        tunnel_actions = tk.Frame(card, bg=self.PALETTE["card"])
        tunnel_actions.grid(row=self._row, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self._row += 1
        self.tunnel_btn = ttk.Button(
            tunnel_actions,
            text="Aktifkan Tunnel Internet",
            style="Accent.TButton",
            command=self._toggle_tunnel,
        )
        self.tunnel_btn.pack(side="left", padx=(0, 6))
        ttk.Button(
            tunnel_actions,
            text="Copy URL Tunnel",
            style="Secondary.TButton",
            command=self._copy_tunnel_url,
        ).pack(side="left", padx=6)
        ttk.Label(
            tunnel_actions,
            text="\u2192 controller bisa konek dari mana saja, tanpa buka port firewall",
            style="Sub.TLabel",
        ).pack(side="left", padx=10)

        # ---- log view ---------------------------------------------
        log_frame = ttk.Frame(outer, style="Card.TFrame", padding=10)
        log_frame.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        outer.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)

        ttk.Label(log_frame, text="Server Log", style="Status.TLabel").grid(row=0, column=0, sticky="w")
        self.log_text = tk.Text(
            log_frame,
            height=10,
            bg="#161a20",
            fg="#cdd2db",
            insertbackground="#cdd2db",
            highlightthickness=0,
            relief="flat",
            wrap="none",
            state="disabled",
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

    def _row_text(self, parent: ttk.Frame, label: str, value: str) -> tk.StringVar:
        var = tk.StringVar(value=value)
        return self._row_entry(parent, label, var)

    def _row_entry(self, parent: ttk.Frame, label: str, var: tk.StringVar) -> tk.StringVar:
        ttk.Label(parent, text=label, style="Field.TLabel").grid(row=self._row, column=0, sticky="w", padx=(0, 12), pady=4)
        entry = ttk.Entry(parent, textvariable=var)
        entry.configure(state="readonly")
        entry.grid(row=self._row, column=1, sticky="ew", pady=4)
        ttk.Button(parent, text="Copy", style="Secondary.TButton", width=8, command=lambda v=var: self._copy(v.get())).grid(
            row=self._row, column=2, sticky="e", padx=(8, 0), pady=4,
        )
        self._row += 1
        return var

    def _row_combo(self, parent: ttk.Frame, label: str, var: tk.StringVar, values: List[str]) -> ttk.Combobox:
        ttk.Label(parent, text=label, style="Field.TLabel").grid(row=self._row, column=0, sticky="w", padx=(0, 12), pady=4)
        combo = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
        combo.grid(row=self._row, column=1, sticky="ew", pady=4)
        ttk.Button(parent, text="Copy", style="Secondary.TButton", width=8, command=lambda v=var: self._copy(v.get())).grid(
            row=self._row, column=2, sticky="e", padx=(8, 0), pady=4,
        )
        self._row += 1
        return combo

    def _row_secret(
        self,
        parent: ttk.Frame,
        label: str,
        value: str,
        show_var: tk.BooleanVar,
    ) -> tk.StringVar:
        ttk.Label(parent, text=label, style="Field.TLabel").grid(row=self._row, column=0, sticky="w", padx=(0, 12), pady=4)
        actual = tk.StringVar(value=value)
        display = tk.StringVar(value=self._mask(value))
        entry = ttk.Entry(parent, textvariable=display, state="readonly")
        entry.grid(row=self._row, column=1, sticky="ew", pady=4)
        button_box = tk.Frame(parent, bg=self.PALETTE["card"])
        button_box.grid(row=self._row, column=2, sticky="e", padx=(8, 0), pady=4)

        def toggle() -> None:
            show_var.set(not show_var.get())
            display.set(actual.get() if show_var.get() else self._mask(actual.get()))
            show_btn.configure(text="Hide" if show_var.get() else "Show")

        show_btn = ttk.Button(button_box, text="Show", style="Secondary.TButton", width=6, command=toggle)
        show_btn.pack(side="left")
        ttk.Button(
            button_box,
            text="Copy",
            style="Secondary.TButton",
            width=6,
            command=lambda v=actual: self._copy(v.get()),
        ).pack(side="left", padx=(6, 0))
        self._row += 1
        return actual

    @staticmethod
    def _mask(value: str) -> str:
        if not value:
            return ""
        if len(value) <= 6:
            return "•" * len(value)
        return value[:3] + "•" * 8 + value[-3:]

    # ---- helpers ---------------------------------------------------

    def _compute_base_url(self) -> str:
        host = self._host_var.get() or "127.0.0.1"
        return f"http://{host}:{self.settings.port}"

    def _copy(self, value: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(value or "")
            # Tk requires a tick for the clipboard to be persisted.
            self.update()
            self._flash_status("Disalin ke clipboard.")
        except tk.TclError:
            messagebox.showerror("Copy", "Gagal menyalin ke clipboard.")

    def _copy_all(self) -> None:
        info = (
            f"Host: {self._host_var.get()}\n"
            f"Port: {self.settings.port}\n"
            f"Username: {self.settings.default_admin_username}\n"
            f"Password: {self.settings.default_admin_password}\n"
            f"API Token: {self.settings.api_token}\n"
            f"Base URL: {self._compute_base_url()}\n"
        )
        self._copy(info)

    def _flash_status(self, message: str, ms: int = 1800) -> None:
        prev = self.status_dot.cget("text")
        prev_fg = self.status_dot.cget("fg")
        self.status_dot.configure(text=message, fg=self.PALETTE["ok"])
        self.after(ms, lambda: self.status_dot.configure(text=prev, fg=prev_fg))

    def _refresh_ips(self) -> None:
        self._available_ips = _detect_local_ips()
        self.host_combo.configure(values=self._available_ips)
        if self._host_var.get() not in self._available_ips and self._available_ips:
            self._host_var.set(self._available_ips[0])
        self.base_url_var.set(self._compute_base_url())

    def _refresh_ffmpeg_label(self) -> None:
        from app.services.ffmpeg_installer import detect_ffmpeg  # local import

        installed, path, version = detect_ffmpeg(self.settings)
        if installed:
            short = (version or "")[:60]
            self.ffmpeg_label.configure(
                text=f"FFmpeg: Installed ✓  {short}",
                foreground=self.PALETTE["ok"],
            )
        else:
            self.ffmpeg_label.configure(
                text="FFmpeg: belum terpasang — buka Installer di controller",
                foreground=self.PALETTE["err"],
            )

    # ---- server lifecycle -----------------------------------------

    def _wire_logging(self) -> None:
        # Attach a single handler to root, and ensure noisy uvicorn loggers
        # propagate to root so their records reach the GUI without duplicates.
        if getattr(self, "_log_handler", None) is not None:
            return
        handler = _LogBuffer(self._log_buffer, self.log_text)
        self._log_handler = handler
        root = logging.getLogger()
        if root.level == logging.NOTSET or root.level > logging.INFO:
            root.setLevel(logging.INFO)
        root.addHandler(handler)
        for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "livestream", "stream_manager"):
            lg = logging.getLogger(logger_name)
            lg.setLevel(logging.INFO)
            lg.propagate = True

    def _set_status(self, label: str, color: str) -> None:
        self.status_dot.configure(text=label, fg=color)

    def _start_server(self) -> None:
        if self._server_thread and self._server_thread.is_alive():
            return
        self._wire_logging()
        thread = _ServerThread(host="0.0.0.0", port=self.settings.port)
        thread.start()
        self._server_thread = thread
        self._set_status("● starting...", self.PALETTE["muted"])

        def watcher() -> None:
            time.sleep(1.0)
            if thread.is_alive():
                self.after(0, lambda: self._set_status(f"● running on :{self.settings.port}", self.PALETTE["ok"]))
                self.after(0, self._refresh_ffmpeg_label)
            else:
                self.after(0, lambda: self._set_status("● gagal start", self.PALETTE["err"]))

        threading.Thread(target=watcher, daemon=True).start()

    def _stop_server(self) -> None:
        thread = self._server_thread
        if thread is None or not thread.is_alive():
            self._set_status("● stopped", self.PALETTE["muted"])
            return
        self._set_status("● stopping...", self.PALETTE["muted"])

        def stopper() -> None:
            thread.stop()
            self.after(0, lambda: self._set_status("● stopped", self.PALETTE["muted"]))

        threading.Thread(target=stopper, daemon=True).start()

    def _open_docs(self) -> None:
        url = self._url_for_docs()
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            messagebox.showerror("Open /docs", f"Tidak bisa membuka browser. URL: {url}")

    def _url_for_docs(self) -> str:
        # Prefer the public tunnel URL when active; falls back to base URL.
        try:
            from app.services.tunnel import get_tunnel  # noqa: WPS433

            t = get_tunnel()
            if t.is_running and t.url:
                return f"{t.url}/docs"
        except Exception:  # noqa: BLE001
            pass
        return f"{self._compute_base_url()}/docs"

    # ---- tunnel ---------------------------------------------------

    def _toggle_tunnel(self) -> None:
        try:
            from app.services.tunnel import get_tunnel  # noqa: WPS433
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Tunnel Internet", f"Modul tunnel gagal di-load: {exc}")
            return
        t = get_tunnel()
        if t.is_running:
            self._stop_tunnel(t)
            return
        self._start_tunnel(t)

    def _start_tunnel(self, tunnel) -> None:  # noqa: ANN001
        # Make sure the local API server is running first so cloudflared has
        # something to forward to.
        if not (self._server_thread and self._server_thread.is_alive()):
            self._start_server()

        def url_cb(url: str) -> None:
            def apply() -> None:
                self.tunnel_url_var.set(url)
                self.tunnel_btn.configure(text="Stop Tunnel")
            try:
                self.after(0, apply)
            except RuntimeError:
                pass

        def log_cb(line: str) -> None:
            try:
                self.after(0, self._append_text_log, f"[cloudflared] {line}")
            except RuntimeError:
                pass

        def exit_cb(rc: int) -> None:
            def apply() -> None:
                self.tunnel_url_var.set("(berhenti)")
                self.tunnel_btn.configure(text="Aktifkan Tunnel Internet")
            try:
                self.after(0, apply)
            except RuntimeError:
                pass

        tunnel.on_url(url_cb)
        tunnel.on_log(log_cb)
        tunnel.on_exit(exit_cb)
        self.tunnel_url_var.set("(menghubungkan ke Cloudflare...)")
        self.tunnel_btn.configure(text="Stop Tunnel")

        def runner() -> None:
            try:
                tunnel.start()
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: messagebox.showerror("Tunnel Internet", str(exc)))
                self.after(0, lambda: self.tunnel_btn.configure(text="Aktifkan Tunnel Internet"))
                self.after(0, lambda: self.tunnel_url_var.set("(gagal)"))

        threading.Thread(target=runner, daemon=True).start()

    def _stop_tunnel(self, tunnel) -> None:  # noqa: ANN001
        self.tunnel_btn.configure(text="Aktifkan Tunnel Internet")
        self.tunnel_url_var.set("(belum aktif)")
        threading.Thread(target=tunnel.stop, daemon=True).start()

    def _copy_tunnel_url(self) -> None:
        url = (self.tunnel_url_var.get() or "").strip()
        if url.startswith("https://") and ".trycloudflare.com" in url:
            self._copy(url)
        else:
            messagebox.showwarning(
                "Copy URL Tunnel",
                "Tunnel belum aktif. Klik 'Aktifkan Tunnel Internet' dulu, "
                "tunggu sampai URL muncul.",
            )

    def _append_text_log(self, line: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _open_firewall(self) -> None:
        if os.name != "nt":
            messagebox.showinfo(
                "Buka Port Firewall",
                "Tombol ini hanya jalan di Windows. Di OS lain, buka port "
                f"{self.settings.port}/TCP secara manual di firewall-mu.",
            )
            return
        if not messagebox.askyesno(
            "Buka Port Firewall",
            (
                f"Akan menambah aturan inbound TCP {self.settings.port} di Windows Firewall.\n\n"
                "Akan muncul prompt UAC (klik Yes untuk approve).\n\nLanjut?"
            ),
        ):
            return
        bat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "open-firewall.bat")
        try:
            if os.path.isfile(bat_path):
                # Run the .bat which already self-elevates via UAC.
                import ctypes  # local import

                ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
                    None, "runas", bat_path, None, os.path.dirname(bat_path), 1,
                )
            else:
                # Fallback: run netsh directly with elevation.
                import ctypes  # local import

                rule_name = "LiveStream API"
                params = (
                    f'advfirewall firewall add rule name="{rule_name}" '
                    f'dir=in protocol=TCP localport={self.settings.port} action=allow profile=any'
                )
                ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
                    None, "runas", "netsh", params, None, 1,
                )
            messagebox.showinfo(
                "Buka Port Firewall",
                "Aturan firewall berhasil dibuat (atau sedang dibuat). "
                "Coba hubungkan controller dari laptop sekarang.",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                "Buka Port Firewall",
                f"Gagal menambah aturan firewall: {exc}\n\n"
                "Buka PowerShell sebagai Administrator dan jalankan:\n"
                f'New-NetFirewallRule -DisplayName "LiveStream API" -Direction Inbound -Protocol TCP -LocalPort {self.settings.port} -Action Allow',
            )

    def _on_close(self) -> None:
        self._stop_server()
        # Give the stop a beat before tearing down Tk.
        self.after(300, self.destroy)


def main() -> int:
    try:
        app = ServerWindow()
    except tk.TclError as exc:
        print(f"GUI tidak bisa dijalankan ({exc}). Jalankan headless dengan: python server_app.py --console")
        return 1
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
