"""
Task Queue — 輕量後台任務系統

取代直接調用 Celery 的複雜配置。
兩種模式：
  1. ThreadTaskQueue：進程內線程池，無需 Redis
  2. CeleryTaskQueue：分佈式，需要 Redis + Celery Worker

用法：
    queue = get_task_queue()
    task_id = queue.submit("backtest", run_backtest, args=(symbol, strategy))
    status = queue.status(task_id)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class TaskInfo:
    """任務資訊."""

    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status.value,
            "error": self.error,
            "created_at": self.created_at,
            "duration": self.duration_seconds,
        }


class ThreadTaskQueue:
    """
    線程池任務隊列（進程內，無外部依賴）。

    適用：單機部署、開發環境。
    """

    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="task")
        self._tasks: dict[str, TaskInfo] = {}
        self._futures: dict[str, Future] = {}
        self._lock = threading.Lock()

    def submit(
        self,
        name: str,
        func: Callable[..., Any],
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
    ) -> str:
        """提交任務，返回 task_id."""
        task_id = uuid.uuid4().hex[:12]
        info = TaskInfo(
            task_id=task_id,
            name=name,
            created_at=time.time(),
        )

        with self._lock:
            self._tasks[task_id] = info

        def _wrapper() -> Any:
            info.status = TaskStatus.RUNNING
            info.started_at = time.time()
            try:
                result = func(*args, **(kwargs or {}))
                info.status = TaskStatus.SUCCESS
                info.result = result
            except Exception as e:
                info.status = TaskStatus.FAILED
                info.error = str(e)
                logger.exception("Task %s [%s] failed", task_id, name)
            finally:
                info.finished_at = time.time()
            return info.result

        future = self._executor.submit(_wrapper)
        with self._lock:
            self._futures[task_id] = future

        logger.info("Task submitted: %s [%s]", task_id, name)
        return task_id

    def status(self, task_id: str) -> TaskInfo | None:
        """查詢任務狀態."""
        return self._tasks.get(task_id)

    def result(self, task_id: str, timeout: float | None = None) -> Any:
        """等待任務結果."""
        future = self._futures.get(task_id)
        if future:
            return future.result(timeout=timeout)
        return None

    def cancel(self, task_id: str) -> bool:
        """取消待執行的任務."""
        future = self._futures.get(task_id)
        if future and future.cancel():
            info = self._tasks.get(task_id)
            if info:
                info.status = TaskStatus.CANCELLED
            return True
        return False

    def list_tasks(self, limit: int = 50) -> list[TaskInfo]:
        """列出最近任務."""
        tasks = sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)


# ─── 工廠 ───

_task_queue: ThreadTaskQueue | None = None


def get_task_queue(max_workers: int | None = None) -> ThreadTaskQueue:
    global _task_queue
    if _task_queue is None:
        workers = max_workers or int(os.getenv("TASK_WORKERS", "4"))
        _task_queue = ThreadTaskQueue(max_workers=workers)
    return _task_queue
