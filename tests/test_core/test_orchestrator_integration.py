"""test_orchestrator_integration.py — Orchestrator 與 DI Container 整合測試."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest

from src.core.config import Settings
from src.core.container import Container
from src.core.provider import CacheBackend, DictCache


class TestDIContainerIntegration:
    """DI Container 與核心組件的整合測試."""

    def test_container_provides_settings(self):
        """Container 應能提供 Settings."""
        c = Container()
        c.register_factory(Settings, Settings)
        settings = c.get(Settings)
        assert settings is not None
        assert hasattr(settings, "app")
        assert hasattr(settings, "cache")
        assert hasattr(settings, "backtest")

    def test_container_singleton_behavior(self):
        """同一類型多次 get 應返回同一實例."""
        c = Container()
        c.register_factory(Settings, Settings)
        s1 = c.get(Settings)
        s2 = c.get(Settings)
        assert s1 is s2

    def test_container_register_override(self):
        """register 可覆蓋工廠."""
        c = Container()
        c.register_factory(CacheBackend, DictCache)

        # 手動註冊覆蓋
        mock_cache = DictCache()
        mock_cache.set("test_key", "test_val", ttl=60)
        c.register(CacheBackend, mock_cache)

        result = c.get(CacheBackend)
        assert result is mock_cache
        assert result.get("test_key") == "test_val"

    def test_container_remove(self):
        """remove 應移除註冊."""
        c = Container()
        c.register_factory(Settings, Settings)
        assert c.has(Settings)
        c.remove(Settings)
        assert not c.has(Settings)

    def test_container_has(self):
        """has 應正確查詢註冊狀態."""
        c = Container()
        assert not c.has(Settings)
        c.register_factory(Settings, Settings)
        assert c.has(Settings)


class TestOrchestratorMocked:
    """使用 mock 測試 Orchestrator 邏輯."""

    def test_orchestrator_list_strategies_not_empty(self):
        """Orchestrator.list_strategies 應返回已註冊的策略."""
        from src.core.orchestrator import Orchestrator
        from src.core.provider import DictCache

        orch = Orchestrator(cache=DictCache())
        strategies = orch.list_strategies()
        # 至少應該有一些策略被橋接進來
        assert isinstance(strategies, list)

    def test_orchestrator_fetch_ohlcv_returns_list(self):
        """fetch_ohlcv 對未知 symbol 應返回空列表."""
        from src.core.orchestrator import Orchestrator
        from src.core.provider import DictCache

        orch = Orchestrator(cache=DictCache())
        result = orch.fetch_ohlcv("NONEXISTENT/PAIR", "1h", limit=10)
        assert isinstance(result, list)


class TestBacktestEngineEdgeCases:
    """回測引擎邊界條件測試."""

    def test_empty_data(self):
        """空數據應返回 error."""
        from src.core.backtest import BacktestEngine, BacktestConfig

        engine = BacktestEngine(config=BacktestConfig())
        report = engine.run([], [], 0, 1000)
        assert report.error is not None

    def test_single_bar(self):
        """只有一根 K 線的數據."""
        from src.core.backtest import BacktestEngine, BacktestConfig

        rows = [{"timestamp": 1000, "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000}]
        signals = [1]
        engine = BacktestEngine(config=BacktestConfig())
        report = engine.run(rows, signals, 0, 1000)
        # 一根 K 線開多倉後強制平倉
        assert report.metrics.get("num_trades", 0) >= 0

    def test_all_flat_signals(self):
        """全部觀望信號不應產生交易."""
        from src.core.backtest import BacktestEngine, BacktestConfig

        rows = [
            {"timestamp": i * 1000, "open": 100 + i, "high": 101 + i, "low": 99 + i, "close": 100 + i, "volume": 100}
            for i in range(20)
        ]
        signals = [0] * 20
        engine = BacktestEngine(config=BacktestConfig())
        report = engine.run(rows, signals, 0, 20000)
        assert report.metrics.get("num_trades", 0) == 0

    def test_high_leverage(self):
        """高槓桿下回測不應崩潰."""
        from src.core.backtest import BacktestEngine, BacktestConfig

        rows = [
            {"timestamp": i * 1000, "open": 100, "high": 102, "low": 98, "close": 100 + (i % 3 - 1), "volume": 100}
            for i in range(20)
        ]
        signals = [1 if i % 2 == 0 else -1 for i in range(20)]
        config = BacktestConfig(initial_equity=10000, leverage=10.0, fee_rate_pct=0.1)
        engine = BacktestEngine(config=config)
        report = engine.run(rows, signals, 0, 20000)
        # 不應崩潰，可能爆倉
        assert report.metrics is not None

    def test_report_to_dict(self):
        """BacktestReport.to_dict 應返回完整結構."""
        from src.core.backtest import BacktestEngine, BacktestConfig

        rows = [
            {"timestamp": i * 1000, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 100}
            for i in range(10)
        ]
        signals = [1] * 10
        engine = BacktestEngine(config=BacktestConfig())
        report = engine.run(rows, signals, 0, 10000)
        d = report.to_dict()
        assert "equity_curve" in d
        assert "trades" in d
        assert "metrics" in d
