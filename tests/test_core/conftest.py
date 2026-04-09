"""conftest.py — 共用 fixtures."""

import os
import tempfile

import pytest


@pytest.fixture
def tmp_db():
    """建立臨時 SQLite 資料庫，測試後自動清理."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)
