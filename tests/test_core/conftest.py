"""conftest.py — 共用 fixtures."""

import os
import sys
import tempfile

import pytest

# 確保 src 在路徑中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def tmp_db():
    """建立臨時 SQLite 資料庫，測試後自動清理."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)
