"""test_repository.py — SqliteBacktestRepository CRUD 單元測試."""

import os

import pytest

from src.core.repository import BacktestRecord, SqliteBacktestRepository

def _make_record(**overrides) -> BacktestRecord:
    """建立測試用 BacktestRecord."""
    defaults = dict(
        id=None,
        user_id=1,
        symbol="BTC/USDT:USDT",
        strategy="sma_cross",
        timeframe="1h",
        initial_equity=10000.0,
        final_equity=12000.0,
        total_return_pct=20.0,
        max_drawdown_pct=5.0,
        sharpe_ratio=1.5,
        num_trades=10,
        win_rate_pct=60.0,
        metrics_json='{"profit_factor": 1.8}',
    )
    defaults.update(overrides)
    return BacktestRecord(**defaults)

# ─── Save / Create 測試 ───

class TestSave:
    """測試 save (建立記錄)."""

    def test_save_returns_id(self, tmp_db):
        """save 應返回新的記錄 ID."""
        repo = SqliteBacktestRepository(tmp_db)
        rid = repo.save(_make_record())
        assert rid > 0

    def test_save_sets_created_at(self, tmp_db):
        """save 後 created_at 應有值."""
        repo = SqliteBacktestRepository(tmp_db)
        rid = repo.save(_make_record())
        record = repo.find_by_id(rid)
        assert record is not None
        assert record.created_at != ""

# ─── Read / Find 測試 ───

class TestFind:
    """測試查詢方法."""

    def test_find_by_id(self, tmp_db):
        """find_by_id 應返回正確記錄."""
        repo = SqliteBacktestRepository(tmp_db)
        rid = repo.save(_make_record(symbol="ETH/USDT:USDT"))
        record = repo.find_by_id(rid)
        assert record is not None
        assert record.symbol == "ETH/USDT:USDT"
        assert record.strategy == "sma_cross"

    def test_find_by_id_not_found(self, tmp_db):
        """不存在的 ID 應返回 None."""
        repo = SqliteBacktestRepository(tmp_db)
        assert repo.find_by_id(99999) is None

    def test_find_by_user(self, tmp_db):
        """find_by_user 應返回該使用者的記錄."""
        repo = SqliteBacktestRepository(tmp_db)
        repo.save(_make_record(user_id=1))
        repo.save(_make_record(user_id=1, symbol="ETH/USDT:USDT"))
        repo.save(_make_record(user_id=2, symbol="SOL/USDT:USDT"))

        records = repo.find_by_user(1)
        assert len(records) == 2
        assert all(r.user_id == 1 for r in records)

    def test_find_by_user_limit(self, tmp_db):
        """find_by_user 應遵守 limit."""
        repo = SqliteBacktestRepository(tmp_db)
        for i in range(5):
            repo.save(_make_record(user_id=1, symbol=f"SYM{i}"))

        records = repo.find_by_user(1, limit=2)
        assert len(records) == 2

    def test_find_by_symbol(self, tmp_db):
        """find_by_symbol 應返回該交易對的記錄."""
        repo = SqliteBacktestRepository(tmp_db)
        repo.save(_make_record(symbol="BTC/USDT:USDT"))
        repo.save(_make_record(symbol="BTC/USDT:USDT"))
        repo.save(_make_record(symbol="ETH/USDT:USDT"))

        records = repo.find_by_symbol("BTC/USDT:USDT")
        assert len(records) == 2

# ─── Delete 測試 ───

class TestDelete:
    """測試刪除方法."""

    def test_delete_existing(self, tmp_db):
        """刪除存在的記錄應返回 True."""
        repo = SqliteBacktestRepository(tmp_db)
        rid = repo.save(_make_record())
        assert repo.delete(rid) is True
        assert repo.find_by_id(rid) is None

    def test_delete_nonexistent(self, tmp_db):
        """刪除不存在的記錄應返回 False."""
        repo = SqliteBacktestRepository(tmp_db)
        assert repo.delete(99999) is False

# ─── Count 測試 ───

class TestCount:
    """測試 count 方法."""

    def test_count_all(self, tmp_db):
        """count() 應返回總數."""
        repo = SqliteBacktestRepository(tmp_db)
        repo.save(_make_record(user_id=1))
        repo.save(_make_record(user_id=2))
        assert repo.count() == 2

    def test_count_by_user(self, tmp_db):
        """count(user_id=) 應返回該用戶的記錄數."""
        repo = SqliteBacktestRepository(tmp_db)
        repo.save(_make_record(user_id=1))
        repo.save(_make_record(user_id=1))
        repo.save(_make_record(user_id=2))
        assert repo.count(user_id=1) == 2

# ─── BacktestRecord 測試 ───

class TestBacktestRecord:
    """測試 BacktestRecord 資料類別."""

    def test_to_dict(self):
        """to_dict 應返回正確字典."""
        r = _make_record(id=1)
        d = r.to_dict()
        assert d["id"] == 1
        assert d["symbol"] == "BTC/USDT:USDT"
        assert d["strategy"] == "sma_cross"
        assert "metrics" in d
