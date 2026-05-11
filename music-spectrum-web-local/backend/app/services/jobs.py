"""In-memory job tracking with async pub/sub for WebSocket consumers."""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from ..models.render import JobInfo, JobKind, JobStatus


@dataclass
class Job:
    id: str
    kind: JobKind
    status: JobStatus = "pending"
    progress: float = 0.0
    message: str = ""
    output_file: Optional[str] = None
    music_file: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    duration: float = 0.0
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    process: Optional[asyncio.subprocess.Process] = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    log_lines: List[str] = field(default_factory=list)

    def to_info(self) -> JobInfo:
        return JobInfo(
            id=self.id,
            kind=self.kind,
            status=self.status,
            progress=self.progress,
            message=self.message,
            output_file=self.output_file,
            music_file=self.music_file,
            error=self.error,
            created_at=self.created_at,
            updated_at=self.updated_at,
            duration=self.duration,
            parent_id=self.parent_id,
            children=list(self.children),
        )


class JobStore:
    def __init__(self) -> None:
        self.jobs: Dict[str, Job] = {}
        self.subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    def create(self, kind: JobKind, parent_id: Optional[str] = None) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], kind=kind, parent_id=parent_id)
        self.jobs[job.id] = job
        if parent_id and parent_id in self.jobs:
            self.jobs[parent_id].children.append(job.id)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    def list(self) -> List[Job]:
        return list(self.jobs.values())

    async def update(
        self,
        job: Job,
        *,
        status: Optional[JobStatus] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        output_file: Optional[str] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None,
        music_file: Optional[str] = None,
        log_line: Optional[str] = None,
    ) -> None:
        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = max(0.0, min(1.0, progress))
        if message is not None:
            job.message = message
        if output_file is not None:
            job.output_file = output_file
        if error is not None:
            job.error = error
        if duration is not None:
            job.duration = duration
        if music_file is not None:
            job.music_file = music_file
        if log_line is not None:
            job.log_lines.append(log_line)
            if len(job.log_lines) > 2000:
                job.log_lines = job.log_lines[-1500:]
        job.updated_at = time.time()
        await self._broadcast(job, log_line=log_line)

    async def _broadcast(self, job: Job, log_line: Optional[str] = None) -> None:
        payload = {"type": "job", "job": job.to_info().model_dump()}
        if log_line is not None:
            payload["log"] = log_line
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    async def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self.subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self.subscribers.discard(queue)

    def request_cancel(self, job: Job) -> None:
        job.cancel_event.set()
        if job.process and job.process.returncode is None:
            try:
                job.process.terminate()
            except ProcessLookupError:
                pass


store = JobStore()
