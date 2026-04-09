"""
StocksX 基礎測試
使用 pytest 執行：pytest tests/ -v
"""

from __future__ import annotations

import os

import pytest

# 確保可以 import 專案模組
# ════════════════════════════════════════════════════════════
# 快取測試
# ════════════════════════════════════════════════════════════
class TestCache:
    def test_cached_decorator(self):
        from src.utils.cache import cached, cache_clear, cache_stats

        call_count = 0

        @cached(ttl=60)
        def expensive_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # 第一次呼叫
        result1 = expensive_func(5)
        assert result1 == 10
        assert call_count == 1

        # 第二次呼叫應該命中快取
        result2 = expensive_func(5)
        assert result2 == 10
        assert call_count == 1  # 沒有增加

        # 不同參數應該重新執行
        result3 = expensive_func(10)
        assert result3 == 20
        assert call_count == 2

        # 清除快取
        cleared = cache_clear()
        assert cleared >= 2

        stats = cache_stats()
        assert stats["total_entries"] == 0

# ════════════════════════════════════════════════════════════
# 用戶資料庫測試
# ════════════════════════════════════════════════════════════
class TestUserDB:
    @pytest.fixture
    def db(self, tmp_path):
        from src.auth.user_db import UserDB

        db_path = str(tmp_path / "test.sqlite")
        return UserDB(db_path=db_path)

    def test_register_and_login(self, db):
        # 註冊
        result = db.register("testuser", "Password123", display_name="Test User")
        assert isinstance(result, dict)
        assert result["username"] == "testuser"

        # 登入
        login_result = db.login("testuser", "Password123")
        assert isinstance(login_result, dict)
        assert login_result["username"] == "testuser"

        # 錯誤密碼
        bad_login = db.login("testuser", "WrongPassword")
        assert isinstance(bad_login, str)  # 錯誤訊息

    def test_duplicate_register(self, db):
        db.register("dupuser", "Password123")
        result = db.register("dupuser", "Password456")
        assert result == "帳號已存在"

    def test_password_validation(self, db):
        # 密碼太短
        result = db.register("weak", "abc")
        assert "至少" in result

        # 純數字
        result = db.register("weak2", "12345678")
        assert "數字" in result

    def test_backtest_history(self, db):
        db.register("histuser", "Password123")
        user = db.get_user("histuser")

        # 儲存回測
        record_id = db.save_backtest(
            user_id=user["id"],
            symbol="BTC/USDT",
            exchange="binance",
            timeframe="1h",
            strategy="sma_cross",
            params={"fast": 10, "slow": 30},
            metrics={"total_return_pct": 15.5},
        )
        assert record_id > 0

        # 查詢歷史
        history = db.get_history(user["id"])
        assert len(history) == 1
        assert history[0]["symbol"] == "BTC/USDT"

    def test_watchlist(self, db):
        db.register("watchuser", "Password123")
        user = db.get_user("watchuser")

        # 新增訂閱
        watch_id = db.add_watch(
            user_id=user["id"],
            symbol="ETH/USDT",
            exchange="okx",
            timeframe="1h",
            strategy="rsi_signal",
            strategy_params={"period": 14},
        )
        assert watch_id > 0

        # 查詢訂閱
        watchlist = db.get_watchlist(user["id"])
        assert len(watchlist) == 1
        assert watchlist[0]["symbol"] == "ETH/USDT"
        assert "account_id" in watchlist[0]

# ════════════════════════════════════════════════════════════
# 回測策略測試
# ════════════════════════════════════════════════════════════
class TestStrategies:
    @pytest.fixture
    def sample_rows(self):
        import numpy as np

        prices = [100 + i * 0.5 + np.random.randn() * 2 for i in range(100)]
        return [
            {
                "timestamp": 1700000000000 + i * 3600000,
                "open": p - 0.5,
                "high": p + 1,
                "low": p - 1,
                "close": p,
                "volume": 1000 + np.random.randint(0, 500),
            }
            for i, p in enumerate(prices)
        ]

    def test_sma_cross(self, sample_rows):
        from src.backtest.strategies import sma_cross

        signals = sma_cross(sample_rows, fast=5, slow=20)
        assert len(signals) == len(sample_rows)
        assert all(s in (-1, 0, 1) for s in signals)

    def test_rsi_signal(self, sample_rows):
        from src.backtest.strategies import rsi_signal

        signals = rsi_signal(sample_rows, period=14)
        assert len(signals) == len(sample_rows)

    def test_buy_and_hold(self, sample_rows):
        from src.backtest.strategies import buy_and_hold

        signals = buy_and_hold(sample_rows)
        assert all(s == 1 for s in signals)

# ════════════════════════════════════════════════════════════
# 工具函數測試
# ════════════════════════════════════════════════════════════
class TestUtils:
    def test_format_price(self):
        from src.config import format_price

        assert format_price(15000) == "15,000.00"
        assert format_price(1.5) == "1.50"
        assert format_price(0.001) == "0.0010"

    def test_sanitize(self):
        from src.auth.user_db import _sanitize

        assert _sanitize("hello<script>") == "helloscript"
        assert _sanitize("a" * 300, max_len=100) == "a" * 100
        assert _sanitize(123) == ""  # type: ignore
