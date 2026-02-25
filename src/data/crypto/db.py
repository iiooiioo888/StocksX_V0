# SQLite schema 初始化
from __future__ import annotations

from src.data.storage.sqlite_storage import SQLiteMarketDataStorage


def get_storage(db_path: str | None = None) -> SQLiteMarketDataStorage:
    """取得 SQLiteMarketDataStorage 單例。"""
    if db_path:
        return SQLiteMarketDataStorage(db_path)
    return SQLiteMarketDataStorage()
