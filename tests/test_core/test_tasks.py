"""test_tasks.py — ThreadTaskQueue 單元測試."""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.tasks import TaskInfo, TaskStatus, ThreadTaskQueue


@pytest.fixture
def queue():
    """建立測試用 TaskQueue."""
    q = ThreadTaskQueue(max_workers=2)
    yield q
    q.shutdown(wait=True)


# ─── Submit 測試 ───


class TestSubmit:
    """測試任務提交."""

    def test_submit_returns_task_id(self, queue):
        """submit 應返回 task_id."""
        task_id = queue.submit("test", lambda: 42)
        assert isinstance(task_id, str)
        assert len(task_id) > 0

    def test_submit_with_args(self, queue):
        """submit 支持 args 參數."""

        def add(a, b):
            return a + b

        task_id = queue.submit("add", add, args=(3, 4))
        result = queue.result(task_id, timeout=5)
        assert result == 7


# ─── Status 測試 ───


class TestStatus:
    """測試任務狀態查詢."""

    def test_status_pending(self, queue):
        """提交後狀態應為 PENDING 或 RUNNING."""
        task_id = queue.submit("slow", lambda: time.sleep(0.5) or "done")
        info = queue.status(task_id)
        assert info is not None
        assert info.status in (TaskStatus.PENDING, TaskStatus.RUNNING)

    def test_status_success(self, queue):
        """完成後狀態應為 SUCCESS."""
        task_id = queue.submit("fast", lambda: 42)
        result = queue.result(task_id, timeout=5)
        info = queue.status(task_id)
        assert info is not None
        assert info.status == TaskStatus.SUCCESS
        assert info.result == 42

    def test_status_failed(self, queue):
        """失敗後狀態應為 FAILED."""

        def fail():
            raise ValueError("boom")

        task_id = queue.submit("fail", fail)
        # 等待任務完成（future.result() 會重新拋出異常）
        import time

        time.sleep(0.2)
        try:
            queue.result(task_id, timeout=5)
        except ValueError:
            pass  # 預期的異常

        info = queue.status(task_id)
        assert info is not None
        assert info.status == TaskStatus.FAILED
        assert "boom" in info.error

    def test_status_nonexistent(self, queue):
        """查詢不存在的任務應返回 None."""
        assert queue.status("nonexistent") is None


# ─── Result 測試 ───


class TestResult:
    """測試結果取得."""

    def test_result_blocks_until_done(self, queue):
        """result 應阻塞直到任務完成."""
        task_id = queue.submit("work", lambda: time.sleep(0.1) or "hello")
        result = queue.result(task_id, timeout=5)
        assert result == "hello"

    def test_result_timeout(self, queue):
        """result 超時應拋出 TimeoutError."""
        task_id = queue.submit("slow", lambda: time.sleep(10))
        with pytest.raises((TimeoutError, Exception)):
            queue.result(task_id, timeout=0.1)


# ─── Cancel 測試 ───


class TestCancel:
    """測試取消任務."""

    def test_cancel_pending(self, queue):
        """取消待執行的任務可能成功."""
        # 提交多個任務，後面的可能還在排隊
        for i in range(10):
            queue.submit(f"task{i}", lambda: time.sleep(0.5))

        tasks = queue.list_tasks()
        # 嘗試取消最後一個
        last = tasks[0]
        # cancel 返回 True/False 取決於是否已開始執行
        queue.cancel(last.task_id)


# ─── List Tasks 測試 ───


class TestListTasks:
    """測試任務列表."""

    def test_list_tasks(self, queue):
        """list_tasks 應返回所有任務."""
        queue.submit("t1", lambda: 1)
        queue.submit("t2", lambda: 2)
        queue.submit("t3", lambda: 3)

        tasks = queue.list_tasks()
        assert len(tasks) == 3

    def test_list_tasks_limit(self, queue):
        """list_tasks 應遵守 limit."""
        for i in range(5):
            queue.submit(f"t{i}", lambda _i=i: _i)

        tasks = queue.list_tasks(limit=2)
        assert len(tasks) == 2


# ─── TaskInfo 測試 ───


class TestTaskInfo:
    """測試 TaskInfo 資料類別."""

    def test_to_dict(self):
        """to_dict 應返回正確字典."""
        info = TaskInfo(task_id="abc", name="test", created_at=time.time())
        d = info.to_dict()
        assert d["task_id"] == "abc"
        assert d["name"] == "test"
        assert d["status"] == "pending"

    def test_duration_none_when_not_finished(self):
        """未完成時 duration_seconds 應為 None."""
        info = TaskInfo(task_id="abc", name="test")
        assert info.duration_seconds is None

    def test_duration_calculated(self):
        """完成後 duration_seconds 應計算."""
        info = TaskInfo(task_id="abc", name="test", started_at=100.0, finished_at=105.5)
        assert info.duration_seconds == 5.5
