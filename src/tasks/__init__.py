# Tasks 模組 - Celery 任務隊列
from __future__ import annotations

from .backtest_tasks import (
    run_backtest,
    run_param_optimizer,
    run_walk_forward_analysis,
)
from .celery_app import app


class TaskStatus:
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"


class TaskInfo:
    """任務資訊封裝"""

    def __init__(self, task_id: str, name: str = "", status: str = TaskStatus.PENDING, result=None):
        self.task_id = task_id
        self.name = name
        self.status = status
        self.result = result


class ThreadTaskQueue:
    """簡易任務隊列（非 Celery 時的 fallback）"""

    def __init__(self):
        self._tasks: dict[str, TaskInfo] = {}

    def enqueue(self, name: str, func, *args, **kwargs) -> str:
        import threading
        import uuid

        task_id = str(uuid.uuid4())[:8]
        info = TaskInfo(task_id=task_id, name=name, status=TaskStatus.STARTED)
        self._tasks[task_id] = info

        def _run():
            try:
                info.result = func(*args, **kwargs)
                info.status = TaskStatus.SUCCESS
            except Exception as e:
                info.result = str(e)
                info.status = TaskStatus.FAILURE

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return task_id

    def get_status(self, task_id: str) -> TaskInfo | None:
        return self._tasks.get(task_id)


_queue: ThreadTaskQueue | None = None


def get_task_queue() -> ThreadTaskQueue:
    global _queue
    if _queue is None:
        _queue = ThreadTaskQueue()
    return _queue


__all__ = [
    "TaskInfo",
    "TaskStatus",
    "ThreadTaskQueue",
    "app",
    "get_task_queue",
    "run_backtest",
    "run_param_optimizer",
    "run_walk_forward_analysis",
]
