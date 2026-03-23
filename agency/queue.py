"""asyncio.Queue-based worker pool for processing 100 clients concurrently."""

import asyncio
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine

from agency.config import MAX_WORKERS

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CampaignJob:
    client_name: str
    brief: dict
    status: JobStatus = JobStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AgencyQueue:
    """Processes campaign jobs across a configurable worker pool.

    Usage:
        queue = AgencyQueue(run_campaign_fn, max_workers=20)
        await queue.start()
        job = await queue.enqueue("brand_name", brief_dict)
        await queue.wait_all()
        await queue.stop()
    """

    def __init__(
        self,
        worker_fn: Callable[[CampaignJob], Coroutine],
        max_workers: int = MAX_WORKERS,
    ):
        self._worker_fn = worker_fn
        self._max_workers = max_workers
        self._queue: asyncio.Queue[CampaignJob | None] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._jobs: list[CampaignJob] = []
        self._running = False

    async def start(self) -> None:
        """Spin up worker coroutines."""
        self._running = True
        for i in range(self._max_workers):
            task = asyncio.create_task(self._worker_loop(i), name=f"worker-{i}")
            self._workers.append(task)
        logger.info("AgencyQueue started with %d workers", self._max_workers)

    async def stop(self) -> None:
        """Drain queue then shut down workers."""
        for _ in range(self._max_workers):
            await self._queue.put(None)  # sentinel
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._running = False
        logger.info("AgencyQueue stopped")

    async def enqueue(self, client_name: str, brief: dict) -> CampaignJob:
        """Add a campaign job to the queue. Returns the job object for tracking."""
        job = CampaignJob(client_name=client_name, brief=brief)
        self._jobs.append(job)
        await self._queue.put(job)
        logger.info("Enqueued campaign for client '%s' (queue size: %d)", client_name, self._queue.qsize())
        return job

    async def wait_all(self) -> None:
        """Wait until all enqueued jobs have been processed."""
        await self._queue.join()

    async def _worker_loop(self, worker_id: int) -> None:
        while True:
            job = await self._queue.get()
            if job is None:  # sentinel — shut down
                self._queue.task_done()
                break
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            logger.info("[worker-%d] Starting campaign for '%s'", worker_id, job.client_name)
            try:
                job.result = await self._worker_fn(job)
                job.status = JobStatus.COMPLETED
                logger.info(
                    "[worker-%d] Completed '%s' in %.1fs",
                    worker_id,
                    job.client_name,
                    job.duration_seconds or 0,
                )
            except Exception as exc:
                job.status = JobStatus.FAILED
                job.error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
                logger.error(
                    "[worker-%d] Failed '%s': %s",
                    worker_id,
                    job.client_name,
                    exc,
                )
            finally:
                job.completed_at = datetime.now()
                self._queue.task_done()

    def status(self) -> dict:
        counts = {s: 0 for s in JobStatus}
        for job in self._jobs:
            counts[job.status] += 1
        return {
            "workers": self._max_workers,
            "queue_size": self._queue.qsize(),
            "total_jobs": len(self._jobs),
            "pending": counts[JobStatus.PENDING],
            "running": counts[JobStatus.RUNNING],
            "completed": counts[JobStatus.COMPLETED],
            "failed": counts[JobStatus.FAILED],
        }

    def get_job(self, client_name: str) -> CampaignJob | None:
        for job in reversed(self._jobs):
            if job.client_name == client_name:
                return job
        return None
