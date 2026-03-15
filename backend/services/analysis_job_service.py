from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from backend.services.analysis_service import analysis_service


TERMINAL_STATUSES = {"completed", "failed"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AnalysisJob:
    job_id: str
    filename: str
    status: str = "queued"
    progress: float = 0.0
    message: str = "Waiting to start."
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    history: list[dict[str, Any]] = field(default_factory=list)
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None
    task: asyncio.Task | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class AnalysisJobService:
    def __init__(self) -> None:
        self._jobs: dict[str, AnalysisJob] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, filename: str, file_bytes: bytes) -> dict[str, Any]:
        job = AnalysisJob(job_id=uuid4().hex, filename=filename)
        self._append_event(
            job,
            "job.queued",
            {
                "job_id": job.job_id,
                "status": job.status,
                "progress": job.progress,
                "message": job.message,
                "filename": filename,
            },
        )

        async with self._lock:
            self._jobs[job.job_id] = job

        job.task = asyncio.create_task(self._run_job(job.job_id, filename, file_bytes))
        return {"job_id": job.job_id, "status": job.status}

    async def get_job(self, job_id: str) -> dict[str, Any]:
        job = await self._require_job(job_id)
        return job.snapshot()

    async def stream_events(self, job_id: str):
        job = await self._require_job(job_id)
        queue: asyncio.Queue = asyncio.Queue()

        async with self._lock:
            history = list(job.history)
            terminal = job.status in TERMINAL_STATUSES
            if not terminal:
                job.subscribers.append(queue)

        async def event_generator():
            try:
                for event in history:
                    yield self._format_sse(event["event"], event["data"])

                if terminal:
                    return

                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=15)
                    except asyncio.TimeoutError:
                        yield ": keep-alive\n\n"
                        continue

                    yield self._format_sse(event["event"], event["data"])
                    if event["data"].get("status") in TERMINAL_STATUSES:
                        break
            finally:
                async with self._lock:
                    if queue in job.subscribers:
                        job.subscribers.remove(queue)

        return event_generator()

    async def _run_job(self, job_id: str, filename: str, file_bytes: bytes) -> None:
        job = await self._require_job(job_id)
        self._append_event(
            job,
            "job.started",
            {
                "job_id": job_id,
                "status": "running",
                "progress": 0.02,
                "message": "Analysis job started.",
            },
        )

        try:
            response = await analysis_service.process_uploaded_bytes(
                filename,
                file_bytes,
                progress_callback=lambda payload: self._append_event(job, "analysis.progress", payload),
            )
            encoded = jsonable_encoder(response)
            job.result = encoded
            self._append_event(
                job,
                "job.completed",
                {
                    "job_id": job_id,
                    "status": "completed",
                    "progress": 1.0,
                    "message": "Analysis completed.",
                    "result": encoded,
                },
            )
        except Exception as exc:
            job.error = str(exc)
            self._append_event(
                job,
                "job.failed",
                {
                    "job_id": job_id,
                    "status": "failed",
                    "progress": job.progress,
                    "message": "Analysis failed.",
                    "error": str(exc),
                },
            )

    async def _require_job(self, job_id: str) -> AnalysisJob:
        async with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return job

    def _append_event(self, job: AnalysisJob, event_name: str, payload: dict[str, Any]) -> None:
        status = str(payload.get("status", job.status))
        progress = float(payload.get("progress", job.progress))
        message = str(payload.get("message", job.message))
        job.status = status
        job.progress = progress
        job.message = message
        job.updated_at = _utc_now()

        event = {
            "event": event_name,
            "data": {
                **payload,
                "job_id": job.job_id,
                "status": status,
                "progress": progress,
                "message": message,
                "updated_at": job.updated_at,
            },
        }
        job.history.append(event)
        for subscriber in list(job.subscribers):
            subscriber.put_nowait(event)

    def _format_sse(self, event_name: str, payload: dict[str, Any]) -> str:
        return f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"


analysis_job_service = AnalysisJobService()
