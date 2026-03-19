"""test_orchestrator.py — Orchestrator 整合測試."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.orchestrator import Orchestrator, get_orchestrator
from src.core.registry import StrategyRegistry, registry
from src.core.backtest import BacktestConfig


# ─── Orchestrator 初始化測試 ───


class TestOrchestratorInit:
    """測試 Orchestrator 初始化."""

    def test_default_init(self):
        """默認初始化不應拋出異常."""
        orch = Orchestrator()
        assert orch is not None

    def test_list_strategies(self):
        """list_strategies 應返回策略列表."""
        orch = Orchestrator()
        strategies = orch.list_strategies()
        assert isinstance(strategies, list)
        # 至少有一些策略被註冊
        if strategies:
            s = strategies[0]
            assert "name" in s
            assert "label" in s

    def test_get_orchestrator_singleton(self):
        """get_orchestrator 應返回同一實例."""
        a = get_orchestrator()
        b = get_orchestrator()
        assert a is b


# ─── Orchestrator 信號計算測試 ───


class TestOrchestratorSignals:
    """測試信號計算."""

    def test_compute_signals_empty_for_unknown_symbol(self):
        """未知交易對可能返回空列表（無網路時）."""
        orch = Orchestrator()
        signals = orch.compute_signals("UNKNOWN/PAIR", "sma_cross")
        # 無網路時可能為空，但不應拋出異常
        assert isinstance(signals, list)


# ─── BacktestConfig 測試 ───


class TestBacktestConfig:
    """測試 BacktestConfig."""

    def test_default_config(self):
        """默認配置應有合理的值."""
        config = BacktestConfig()
        assert config.initial_equity > 0
        assert config.leverage >= 1
        assert config.fee_rate_pct >= 0
