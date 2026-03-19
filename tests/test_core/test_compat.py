"""test_compat.py — compat 模組測試（新舊架構橋接）."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest

from src.compat import BacktestResult, report_to_result, run_single_strategy_new
from src.core.backtest import BacktestEngine, BacktestConfig, BacktestReport


class TestBacktestResult:
    """BacktestResult 數據類測試."""

    def test_default_values(self):
        result = BacktestResult()
        assert result.equity_curve == []
        assert result.trades == []
        assert result.metrics == {}
        assert result.error is None

    def test_with_data(self):
        result = BacktestResult(
            equity_curve=[{"timestamp": 1000, "equity": 10500}],
            metrics={"total_return_pct": 5.0},
        )
        assert len(result.equity_curve) == 1
        assert result.metrics["total_return_pct"] == 5.0


class TestReportToResult:
    """report_to_result 轉換測試."""

    def test_empty_report(self):
        report = BacktestReport()
        result = report_to_result(report)
        assert isinstance(result, BacktestResult)
        assert result.equity_curve == []
        assert result.trades == []
        assert result.error is None

    def test_report_with_trades(self):
        from src.core.backtest import TradeRecord

        trade = TradeRecord(
            entry_ts=1000,
            exit_ts=2000,
            side=1,
            entry_price=100,
            exit_price=110,
            pnl_pct=10.0,
            profit=1000,
            fee=10,
        )
        report = BacktestReport(
            equity_curve=[{"timestamp": 1000, "equity": 11000}],
            trades=[trade],
            metrics={"total_return_pct": 10.0},
        )
        result = report_to_result(report)
        assert len(result.trades) == 1
        assert result.trades[0]["side"] == 1
        assert result.metrics["total_return_pct"] == 10.0


class TestRunSingleStrategyNew:
    """run_single_strategy_new 整合測試."""

    @pytest.fixture
    def sample_rows(self):
        return [
            {
                "timestamp": i * 3600000,
                "open": 100 + i * 0.1,
                "high": 101 + i * 0.1,
                "low": 99 + i * 0.1,
                "close": 100 + i * 0.1,
                "volume": 1000,
            }
            for i in range(50)
        ]

    def test_run_buy_and_hold(self, sample_rows):
        result = run_single_strategy_new(
            rows=sample_rows,
            strategy="buy_and_hold",
            strategy_params={},
            since_ms=0,
            until_ms=50 * 3600000,
        )
        assert isinstance(result, BacktestResult)
        assert result.error is None
        assert "total_return_pct" in result.metrics

    def test_run_unknown_strategy(self, sample_rows):
        result = run_single_strategy_new(
            rows=sample_rows,
            strategy="nonexistent_strategy_xyz",
            strategy_params={},
            since_ms=0,
            until_ms=50 * 3600000,
        )
        # 未知策略返回全部 0 信號，不應報錯
        assert isinstance(result, BacktestResult)
        assert result.metrics.get("num_trades", 0) == 0

    def test_run_with_leverage(self, sample_rows):
        result = run_single_strategy_new(
            rows=sample_rows,
            strategy="buy_and_hold",
            strategy_params={},
            since_ms=0,
            until_ms=50 * 3600000,
            leverage=5.0,
            fee_rate=0.05,
        )
        assert result.metrics.get("leverage") == 5.0
