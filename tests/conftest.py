"""
Pytest 共用 fixtures
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def test_env():
    """設定測試環境變數。"""
    os.environ.setdefault("ADMIN_PASSWORD", "TestPassword123!")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
    os.environ.setdefault("LOG_LEVEL", "WARNING")
    return os.environ
