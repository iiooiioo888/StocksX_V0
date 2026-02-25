# SQLiteMarketDataStorage：SQLite 儲存實作
from __future__ import annotations

import os
import sqlite3
from typing import Any

_DEFAULT_DB_PATH = os.path.join("cache", "crypto_cache.sqlite")

_CREATE_OHLCV = """
CREATE TABLE IF NOT EXISTS ohlcv (
    exchange   TEXT NOT NULL,
    symbol     TEXT NOT NULL,
    timeframe  TEXT NOT NULL,
    timestamp  INTEGER NOT NULL,
    open       REAL,
    high       REAL,
    low        REAL,
    close      REAL,
    volume     REAL,
    filled     INTEGER DEFAULT 0,
    is_outlier INTEGER DEFAULT 0,
    PRIMARY KEY (exchange, symbol, timeframe, timestamp)
)
"""

_CREATE_FUNDING = """
CREATE TABLE IF NOT EXISTS funding_rates (
    exchange      TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    timestamp     INTEGER NOT NULL,
    funding_rate  REAL,
    open_interest REAL,
    mark_price    REAL,
    PRIMARY KEY (exchange, symbol, timestamp)
)
"""


class SQLiteMarketDataStorage:
    """基於 SQLite 的本地緩存儲存。"""

    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_OHLCV)
        self._conn.execute(_CREATE_FUNDING)
        self._conn.commit()

    def save_ohlcv(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self._conn.executemany(
            """INSERT OR REPLACE INTO ohlcv
               (exchange, symbol, timeframe, timestamp, open, high, low, close, volume, filled, is_outlier)
               VALUES (:exchange, :symbol, :timeframe, :timestamp, :open, :high, :low, :close, :volume, :filled, :is_outlier)""",
            rows,
        )
        self._conn.commit()

    def load_ohlcv(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
    ) -> list[dict[str, Any]]:
        cur = self._conn.execute(
            """SELECT * FROM ohlcv
               WHERE exchange=? AND symbol=? AND timeframe=? AND timestamp>=? AND timestamp<=?
               ORDER BY timestamp""",
            (exchange, symbol, timeframe, since, until),
        )
        return [dict(r) for r in cur.fetchall()]

    def save_funding_rates(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self._conn.executemany(
            """INSERT OR REPLACE INTO funding_rates
               (exchange, symbol, timestamp, funding_rate, open_interest, mark_price)
               VALUES (:exchange, :symbol, :timestamp, :funding_rate, :open_interest, :mark_price)""",
            rows,
        )
        self._conn.commit()

    def load_funding_rates(
        self,
        exchange: str,
        symbol: str,
        since: int,
        until: int,
    ) -> list[dict[str, Any]]:
        cur = self._conn.execute(
            """SELECT * FROM funding_rates
               WHERE exchange=? AND symbol=? AND timestamp>=? AND timestamp<=?
               ORDER BY timestamp""",
            (exchange, symbol, since, until),
        )
        return [dict(r) for r in cur.fetchall()]
