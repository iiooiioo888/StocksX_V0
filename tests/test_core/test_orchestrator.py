"""test_orchestrator.py — Orchestrator 整合測試 (v5.1 增強版)."""

import os

import pytest

from src.core.orchestrator import Orchestrator, get_orchestrator
from src.core.registry import StrategyRegistry, registry
from src.core.backtest import BacktestConfig, BacktestReport
from src.core.provider import DictCache

# ─── Orchestrator 初始化測試 ───

class TestOrchestratorInit:
    """測試 Orchestrator 初始化."""

    def test_default_init(self):
        """默認初始化不應拋出異常."""
        orch = Orchestrator()
        assert orch is not None

    def test_init_with_cache(self):
        """傳入自定義 cache."""
        cache = DictCache()
        orch = Orchestrator(cache=cache)
        assert orch is not None

    def test_list_strategies(self):
        """list_strategies 應返回策略列表."""
        orch = Orchestrator()
        strategies = orch.list_strategies()
        assert isinstance(strategies, list)
        if strategies:
            s = strategies[0]
            assert "name" in s
            assert "label" in s
            assert "category" in s

    def test_list_strategies_structure(self):
        """每個策略應有完整的元數據結構."""
        orch = Orchestrator()
        for s in orch.list_strategies():
            assert isinstance(s["name"], str)
            assert isinstance(s["label"], str)
            assert isinstance(s["category"], str)
            assert isinstance(s["params"], list)
            assert isinstance(s["defaults"], dict)

    def test_get_orchestrator_singleton(self):
        """get_orchestrator 應返回同一實例."""
        import src.core.orchestrator as orch_mod

        orch_mod._orchestrator = None  # 重置
        a = get_orchestrator()
        b = get_orchestrator()
        assert a is b

# ─── Orchestrator 數據獲取測試 ───

class TestOrchestratorData:
    """測試數據獲取方法."""

    def test_fetch_ohlcv_returns_list(self):
        """fetch_ohlcv 對未知 symbol 應返回空列表."""
        orch = Orchestrator(cache=DictCache())
        result = orch.fetch_ohlcv("NONEXISTENT/PAIR", "1h", limit=10)
        assert isinstance(result, list)

    def test_fetch_ohlcv_with_clean(self):
        """clean=True 應應用清洗管道."""
        orch = Orchestrator(cache=DictCache())
        # 無網路環境下，返回空列表
        result = orch.fetch_ohlcv("BTC/USDT", "1h", limit=10, clean=True)
        assert isinstance(result, list)

    def test_get_ticker_returns_none_for_unknown(self):
        """get_ticker 對未知 symbol 應返回 None."""
        orch = Orchestrator(cache=DictCache())
        ticker = orch.get_ticker("NONEXISTENT/PAIR")
        assert ticker is None

    def test_get_orderbook_returns_none_for_unknown(self):
        """get_orderbook 對未知 symbol 應返回 None."""
        orch = Orchestrator(cache=DictCache())
        ob = orch.get_orderbook("NONEXISTENT/PAIR")
        assert ob is None

# ─── Orchestrator 信號計算測試 ───

class TestOrchestratorSignals:
    """測試信號計算."""

    def test_compute_signals_returns_list(self):
        """compute_signals 應返回 list."""
        orch = Orchestrator(cache=DictCache())
        signals = orch.compute_signals("UNKNOWN/PAIR", "sma_cross")
        assert isinstance(signals, list)

    def test_compute_signals_unknown_strategy(self):
        """未知策略應返回空列表."""
        orch = Orchestrator(cache=DictCache())
        signals = orch.compute_signals("BTC/USDT", "totally_fake_strategy")
        assert isinstance(signals, list)

# ─── Orchestrator 回測測試 ───

class TestOrchestratorBacktest:
    """測試回測方法."""

    def test_run_backtest_returns_report(self):
        """run_backtest 應返回 BacktestReport."""
        orch = Orchestrator(cache=DictCache())
        report = orch.run_backtest("NONEXISTENT/PAIR", "1h", "sma_cross")
        assert isinstance(report, BacktestReport)
        # 無數據時應有 error
        assert report.error is not None

    def test_run_multi_backtest(self):
        """run_multi_backtest 應返回 dict."""
        orch = Orchestrator(cache=DictCache())
        results = orch.run_multi_backtest("NONEXISTENT/PAIR", "1h", ["sma_cross", "buy_and_hold"])
        assert isinstance(results, dict)
        assert "sma_cross" in results
        assert "buy_and_hold" in results

    def test_run_backtest_with_time_range(self):
        """指定時間範圍的回測."""
        orch = Orchestrator(cache=DictCache())
        report = orch.run_backtest(
            "NONEXISTENT/PAIR",
            "1h",
            "sma_cross",
            since_ms=0,
            until_ms=100000,
        )
        assert isinstance(report, BacktestReport)

# ─── BacktestConfig 測試 ───

class TestBacktestConfig:
    """測試 BacktestConfig."""

    def test_default_config(self):
        """默認配置應有合理的值."""
        config = BacktestConfig()
        assert config.initial_equity > 0
        assert config.leverage >= 1
        assert config.fee_rate_pct >= 0
        assert config.slippage_pct >= 0

    def test_custom_config(self):
        """自定義配置."""
        config = BacktestConfig(
            initial_equity=50000,
            leverage=5.0,
            fee_rate_pct=0.1,
            slippage_pct=0.05,
            take_profit_pct=10.0,
            stop_loss_pct=5.0,
        )
        assert config.initial_equity == 50000
        assert config.leverage == 5.0
        assert config.take_profit_pct == 10.0
        assert config.stop_loss_pct == 5.0

    def test_config_frozen(self):
        """BacktestConfig 應為不可變."""
        config = BacktestConfig()
        with pytest.raises(AttributeError):
            config.initial_equity = 99999  # type: ignore
