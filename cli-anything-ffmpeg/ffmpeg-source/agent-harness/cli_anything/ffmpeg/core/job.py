"""Job queue and status tracking for FFmpeg CLI."""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """Result of a completed or failed job."""
    job_id: str
    status: JobStatus
    output_path: Optional[str] = None
    duration: Optional[float] = None
    size_bytes: Optional[int] = None
    video_info: Optional[Dict[str, Any]] = None
    audio_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: Optional[str] = None


class JobQueue:
    """Queue of transcode jobs with progress tracking."""

    def __init__(self):
        self.jobs: List[JobResult] = []
        self._callbacks: Dict[str, List[Callable]] = {
            "complete": [],
            "failed": [],
            "progress": [],
        }

    def enqueue(self, input_path: str, output_path: str, preset: str = "default") -> str:
        job_id = str(uuid.uuid4())[:8]
        job = JobResult(
            job_id=job_id,
            status=JobStatus.PENDING,
        )
        self.jobs.append(job)
        return job_id

    def start(self, job_id: str) -> None:
        for j in self.jobs:
            if j.job_id == job_id:
                j.status = JobStatus.RUNNING
                return

    def complete(self, job_id: str, result: JobResult) -> None:
        for i, j in enumerate(self.jobs):
            if j.job_id == job_id:
                # Always set status to COMPLETE; override with result fields
                j.status = JobStatus.COMPLETE
                j.output_path = result.output_path
                j.duration = result.duration
                j.size_bytes = result.size_bytes
                j.video_info = result.video_info
                j.audio_info = result.audio_info
                j.error = result.error
                j.completed_at = result.completed_at or datetime.now().isoformat()
                for cb in self._callbacks["complete"]:
                    cb(j)
                return

    def fail(self, job_id: str, error: str) -> None:
        for i, j in enumerate(self.jobs):
            if j.job_id == job_id:
                j.status = JobStatus.FAILED
                j.error = error
                j.completed_at = datetime.now().isoformat()
                for cb in self._callbacks["failed"]:
                    cb(j)
                return

    def on_complete(self, cb: Callable) -> None:
        self._callbacks["complete"].append(cb)

    def on_fail(self, cb: Callable) -> None:
        self._callbacks["failed"].append(cb)

    def list_pending(self) -> List[JobResult]:
        return [j for j in self.jobs if j.status == JobStatus.PENDING]

    def list_running(self) -> List[JobResult]:
        return [j for j in self.jobs if j.status == JobStatus.RUNNING]

    def list_complete(self) -> List[JobResult]:
        return [j for j in self.jobs if j.status == JobStatus.COMPLETE]

    def get(self, job_id: str) -> Optional[JobResult]:
        for j in self.jobs:
            if j.job_id == job_id:
                return j
        return None

    def clear_completed(self) -> None:
        self.jobs = [j for j in self.jobs if j.status not in (JobStatus.COMPLETE, JobStatus.FAILED)]