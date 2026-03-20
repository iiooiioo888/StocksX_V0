"""
Repository Pattern — 數據存取抽象

取代直接操作 SQLite/sqlite3 的散落邏輯。
通過 Protocol 定義存取介面，可替換為 PostgreSQL/Redis/In-Memory。

架構：
  Repository (Protocol)
    ├── BacktestRepository    → 回測結果 CRUD
    ├── UserRepository        → 用戶 CRUD
    ├── WatchlistRepository   → 訂閱管理
    └── SqliteBacktestRepo    → SQLite 實現
"""

from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# Value Objects
# ════════════════════════════════════════════════════════════


@dataclass(slots=True)
class BacktestRecord:
    """回測記錄."""

    id: int | None
    user_id: int
    symbol: str
    strategy: str
    timeframe: str
    initial_equity: float
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    num_trades: int
    win_rate_pct: float
    metrics_json: str = "{}"
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "strategy": self.strategy,
            "timeframe": self.timeframe,
            "initial_equity": self.initial_equity,
            "final_equity": self.final_equity,
            "total_return_pct": self.total_return_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "num_trades": self.num_trades,
            "win_rate_pct": self.win_rate_pct,
            "metrics": self.metrics_json,
            "created_at": self.created_at,
        }


# ════════════════════════════════════════════════════════════
# Repository Protocol
# ════════════════════════════════════════════════════════════


@runtime_checkable
class BacktestRepository(Protocol):
    """回測結果存取介面."""

    def save(self, record: BacktestRecord) -> int: ...
    def find_by_id(self, record_id: int) -> BacktestRecord | None: ...
    def find_by_user(self, user_id: int, limit: int = 50) -> list[BacktestRecord]: ...
    def find_by_symbol(self, symbol: str, limit: int = 50) -> list[BacktestRecord]: ...
    def delete(self, record_id: int) -> bool: ...
    def count(self, user_id: int | None = None) -> int: ...


# ════════════════════════════════════════════════════════════
# SQLite 實現
# ════════════════════════════════════════════════════════════

_CREATE_BACKTEST_TABLE = """
CREATE TABLE IF NOT EXISTS backtest_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL DEFAULT 0,
    symbol          TEXT NOT NULL,
    strategy        TEXT NOT NULL,
    timeframe       TEXT NOT NULL DEFAULT '1h',
    initial_equity  REAL DEFAULT 0,
    final_equity    REAL DEFAULT 0,
    total_return_pct REAL DEFAULT 0,
    max_drawdown_pct REAL DEFAULT 0,
    sharpe_ratio    REAL DEFAULT 0,
    num_trades      INTEGER DEFAULT 0,
    win_rate_pct    REAL DEFAULT 0,
    metrics_json    TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now'))
)
"""

_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_backtest_user ON backtest_results(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_symbol ON backtest_results(symbol);
CREATE INDEX IF NOT EXISTS idx_backtest_created ON backtest_results(created_at);
"""


class SqliteBacktestRepository:
    """SQLite 回測結果存取."""

    def __init__(self, db_path: str = "data/stocksx.db") -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_BACKTEST_TABLE)
        self._conn.executescript(_INDEX_SQL)
        self._conn.commit()

    def save(self, record: BacktestRecord) -> int:
        cur = self._conn.execute(
            """INSERT INTO backtest_results
               (user_id, symbol, strategy, timeframe, initial_equity, final_equity,
                total_return_pct, max_drawdown_pct, sharpe_ratio, num_trades, win_rate_pct, metrics_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.user_id,
                record.symbol,
                record.strategy,
                record.timeframe,
                record.initial_equity,
                record.final_equity,
                record.total_return_pct,
                record.max_drawdown_pct,
                record.sharpe_ratio,
                record.num_trades,
                record.win_rate_pct,
                record.metrics_json,
            ),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def find_by_id(self, record_id: int) -> BacktestRecord | None:
        row = self._conn.execute("SELECT * FROM backtest_results WHERE id=?", (record_id,)).fetchone()
        return self._row_to_record(row) if row else None

    def find_by_user(self, user_id: int, limit: int = 50) -> list[BacktestRecord]:
        rows = self._conn.execute(
            "SELECT * FROM backtest_results WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def find_by_symbol(self, symbol: str, limit: int = 50) -> list[BacktestRecord]:
        rows = self._conn.execute(
            "SELECT * FROM backtest_results WHERE symbol=? ORDER BY created_at DESC LIMIT ?",
            (symbol, limit),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def delete(self, record_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM backtest_results WHERE id=?", (record_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def count(self, user_id: int | None = None) -> int:
        if user_id:
            row = self._conn.execute(
                "SELECT COUNT(*) as cnt FROM backtest_results WHERE user_id=?", (user_id,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) as cnt FROM backtest_results").fetchone()
        return row["cnt"] if row else 0

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> BacktestRecord:
        return BacktestRecord(
            id=row["id"],
            user_id=row["user_id"],
            symbol=row["symbol"],
            strategy=row["strategy"],
            timeframe=row["timeframe"],
            initial_equity=row["initial_equity"],
            final_equity=row["final_equity"],
            total_return_pct=row["total_return_pct"],
            max_drawdown_pct=row["max_drawdown_pct"],
            sharpe_ratio=row["sharpe_ratio"],
            num_trades=row["num_trades"],
            win_rate_pct=row["win_rate_pct"],
            metrics_json=row["metrics_json"],
            created_at=row["created_at"],
        )


# ─── 工廠 ───

_repo_instance: BacktestRepository | None = None


def get_backtest_repository(db_path: str = "data/stocksx.db") -> BacktestRepository:
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = SqliteBacktestRepository(db_path)
    return _repo_instance
