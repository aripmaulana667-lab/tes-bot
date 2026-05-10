"""In-memory registry of running FFmpeg processes."""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import session_scope
from app.models import Account, Stream, StreamLog, Video
from app.services.ffmpeg_installer import detect_ffmpeg
from app.services.ffmpeg_runner import FfmpegOptions, build_command, join_rtmp
from app.utils.logging import get_logger, stream_log_path


_logger = get_logger("stream_manager")


@dataclass
class _RunningStream:
    stream_id: int
    process: subprocess.Popen
    log_lines: Deque[str] = field(default_factory=lambda: deque(maxlen=500))
    log_file_path: Optional[str] = None
    reader_thread: Optional[threading.Thread] = None
    auto_restart: bool = False


class StreamManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._running: Dict[int, _RunningStream] = {}
        self._monitor: Optional[threading.Thread] = None
        self._monitor_stop = threading.Event()

    # ---- lifecycle -------------------------------------------------

    def start_monitor(self) -> None:
        with self._lock:
            if self._monitor and self._monitor.is_alive():
                return
            self._monitor_stop.clear()
            self._monitor = threading.Thread(
                target=self._monitor_loop, name="stream-monitor", daemon=True
            )
            self._monitor.start()

    def shutdown(self) -> None:
        self._monitor_stop.set()
        with self._lock:
            for sid in list(self._running.keys()):
                try:
                    self._terminate(sid)
                except Exception:  # noqa: BLE001
                    pass

    # ---- public API ------------------------------------------------

    def start(
        self,
        db: Session,
        account_id: int,
        video_id: int,
        bitrate: Optional[str] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None,
        audio_bitrate: Optional[str] = None,
        preset: Optional[str] = None,
        loop: Optional[bool] = None,
        auto_restart: Optional[bool] = None,
    ) -> Stream:
        settings = get_settings()
        installed, ffmpeg_path, _ = detect_ffmpeg(settings)
        if not installed or not ffmpeg_path:
            raise RuntimeError("FFmpeg belum terpasang. Jalankan installer terlebih dahulu.")

        account = db.query(Account).get(account_id)
        if account is None:
            raise ValueError("akun tidak ditemukan")
        if not account.is_active:
            raise ValueError("akun nonaktif")

        video = db.query(Video).get(video_id)
        if video is None:
            raise ValueError("video tidak ditemukan")
        if not os.path.isfile(video.path):
            raise FileNotFoundError(f"file video tidak ada: {video.path}")

        stream = Stream(
            account_id=account.id,
            video_id=video.id,
            status="starting",
            bitrate=bitrate or account.default_bitrate or "2500k",
            resolution=resolution or account.default_resolution or "1280x720",
            fps=fps or 30,
            audio_bitrate=audio_bitrate or "128k",
            preset=preset or "veryfast",
            loop=settings.stream_loop_default if loop is None else bool(loop),
            auto_restart=settings.auto_restart_default if auto_restart is None else bool(auto_restart),
            started_at=_dt.datetime.utcnow(),
        )
        db.add(stream)
        db.flush()
        stream.log_path = stream_log_path(stream.id, settings.logs_dir)

        rtmp_target = join_rtmp(account.rtmp_url, account.stream_key)
        options = FfmpegOptions(
            video_path=video.path,
            rtmp_target=rtmp_target,
            bitrate=stream.bitrate,
            resolution=stream.resolution,
            fps=stream.fps,
            audio_bitrate=stream.audio_bitrate,
            preset=stream.preset,
            loop=stream.loop,
        )
        cmd = build_command(ffmpeg_path, options)
        _logger.info("Starting stream %s: %s", stream.id, " ".join(cmd))

        try:
            log_handle = open(stream.log_path, "ab", buffering=0)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
                creationflags=_creation_flags(),
            )
        except OSError as exc:
            stream.status = "error"
            stream.last_error = str(exc)
            stream.stopped_at = _dt.datetime.utcnow()
            db.flush()
            raise

        stream.pid = process.pid
        stream.status = "running"
        db.flush()

        running = _RunningStream(
            stream_id=stream.id,
            process=process,
            log_file_path=stream.log_path,
            auto_restart=stream.auto_restart,
        )
        running.reader_thread = threading.Thread(
            target=self._reader_loop,
            args=(running, log_handle),
            name=f"stream-{stream.id}-reader",
            daemon=True,
        )
        with self._lock:
            self._running[stream.id] = running
        running.reader_thread.start()
        self.start_monitor()
        return stream

    def stop(self, db: Session, stream_id: int) -> Stream:
        stream = db.query(Stream).get(stream_id)
        if stream is None:
            raise ValueError("stream tidak ditemukan")
        self._terminate(stream_id)
        stream.status = "stopped"
        stream.pid = None
        stream.stopped_at = _dt.datetime.utcnow()
        db.flush()
        return stream

    def restart(self, db: Session, stream_id: int) -> Stream:
        stream = db.query(Stream).get(stream_id)
        if stream is None:
            raise ValueError("stream tidak ditemukan")
        # Terminate the existing FFmpeg if alive.
        self._terminate(stream_id)
        stream.status = "starting"
        stream.stopped_at = None
        stream.last_error = None
        db.flush()
        return self.start(
            db,
            account_id=stream.account_id,
            video_id=stream.video_id,
            bitrate=stream.bitrate,
            resolution=stream.resolution,
            fps=stream.fps,
            audio_bitrate=stream.audio_bitrate,
            preset=stream.preset,
            loop=stream.loop,
            auto_restart=stream.auto_restart,
        )

    def is_running(self, stream_id: int) -> bool:
        with self._lock:
            running = self._running.get(stream_id)
        if running is None:
            return False
        return running.process.poll() is None

    def tail_logs(self, stream_id: int, limit: int = 200) -> List[str]:
        with self._lock:
            running = self._running.get(stream_id)
        if running is not None and running.log_lines:
            return list(running.log_lines)[-limit:]
        # Fallback to disk log.
        path = stream_log_path(stream_id)
        if not os.path.isfile(path):
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.readlines()[-limit:]
        except OSError:
            return []

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for r in self._running.values() if r.process.poll() is None)

    # ---- internals -------------------------------------------------

    def _terminate(self, stream_id: int) -> None:
        with self._lock:
            running = self._running.pop(stream_id, None)
        if running is None:
            return
        proc = running.process
        if proc.poll() is None:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except OSError:
                pass

    def _reader_loop(self, running: _RunningStream, log_handle) -> None:
        try:
            assert running.process.stdout is not None
            for raw in iter(running.process.stdout.readline, b""):
                line = raw.decode("utf-8", errors="replace").rstrip()
                if not line:
                    continue
                running.log_lines.append(line)
                try:
                    log_handle.write((line + "\n").encode("utf-8"))
                except OSError:
                    pass
        except Exception as exc:  # noqa: BLE001
            _logger.warning("reader for stream %s ended: %s", running.stream_id, exc)
        finally:
            try:
                log_handle.close()
            except OSError:
                pass

    def _monitor_loop(self) -> None:
        while not self._monitor_stop.is_set():
            self._monitor_stop.wait(timeout=3)
            with self._lock:
                snapshot = list(self._running.items())
            for stream_id, running in snapshot:
                rc = running.process.poll()
                if rc is None:
                    continue
                # Process has exited.
                with self._lock:
                    self._running.pop(stream_id, None)
                tail = "\n".join(list(running.log_lines)[-15:])
                _logger.info("stream %s exited rc=%s", stream_id, rc)
                with session_scope() as db:
                    stream = db.query(Stream).get(stream_id)
                    if stream is None:
                        continue
                    if rc == 0:
                        stream.status = "stopped"
                    else:
                        stream.status = "error"
                        stream.last_error = f"exit code {rc}\n{tail}"[-2000:]
                    stream.pid = None
                    stream.stopped_at = _dt.datetime.utcnow()
                    db.add(StreamLog(
                        stream_id=stream.id,
                        message=f"FFmpeg exited rc={rc}",
                        level="error" if rc else "info",
                    ))
                    should_restart = running.auto_restart and rc != 0
                    if should_restart:
                        try:
                            self.start(
                                db,
                                account_id=stream.account_id,
                                video_id=stream.video_id,
                                bitrate=stream.bitrate,
                                resolution=stream.resolution,
                                fps=stream.fps,
                                audio_bitrate=stream.audio_bitrate,
                                preset=stream.preset,
                                loop=stream.loop,
                                auto_restart=stream.auto_restart,
                            )
                        except Exception as exc:  # noqa: BLE001
                            _logger.warning("auto-restart failed for stream %s: %s", stream_id, exc)


def _creation_flags() -> int:
    if os.name == "nt":
        # CREATE_NO_WINDOW = 0x08000000 keeps the FFmpeg console hidden on Windows.
        return 0x08000000
    return 0


_manager_lock = threading.Lock()
_manager: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = StreamManager()
            _manager.start_monitor()
        return _manager
