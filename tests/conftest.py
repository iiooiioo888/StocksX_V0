"""
Pytest 共用 fixtures
"""

from __future__ import annotations

import os
import sys

import pytest

# 確保可以 import 專案模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def test_env():
    """設定測試環境變數。"""
    os.environ.setdefault("ADMIN_PASSWORD", "TestPassword123!")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
    os.environ.setdefault("LOG_LEVEL", "WARNING")
    return os.environ
