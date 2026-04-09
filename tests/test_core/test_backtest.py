"""backtest.py 單元測試 — BacktestEngine, TradeRecord, compute_performance_metrics."""

import os
import pytest

from src.core.backtest import (
    BacktestConfig,
    BacktestEngine,
    BacktestReport,
    TradeRecord,
    compute_performance_metrics,
)
from src.core.pipeline import Pipeline

# ─── TradeRecord 測試 ───

class TestTradeRecord:
    """測試 TradeRecord 資料類別."""

    def test_to_dict(self):
        """to_dict 應返回正確字典."""
        t = TradeRecord(
            entry_ts=1000,
            exit_ts=2000,
            side=1,
            entry_price=100.0,
            exit_price=110.0,
            pnl_pct=10.0,
            profit=100.0,
            fee=5.0,
            liquidation=False,
            exit_reason="signal",
        )
        d = t.to_dict()
        assert d["entry_ts"] == 1000
        assert d["exit_ts"] == 2000
        assert d["side"] == 1
        assert d["entry_price"] == pytest.approx(100.0)
        assert d["exit_price"] == pytest.approx(110.0)
        assert d["pnl_pct"] == pytest.approx(10.0)
        assert d["profit"] == pytest.approx(100.0)
        assert d["fee"] == pytest.approx(5.0)
        assert d["liquidation"] is False
        assert d["exit_reason"] == "signal"

    def test_to_dict_rounds(self):
        """to_dict 應對 pnl_pct、profit、fee 做四捨五入."""
        t = TradeRecord(
            entry_ts=0,
            exit_ts=0,
            side=1,
            entry_price=1,
            exit_price=1,
            pnl_pct=10.12345,
            profit=99.999,
            fee=0.001,
        )
        d = t.to_dict()
        assert d["pnl_pct"] == pytest.approx(10.1235)
        assert d["profit"] == pytest.approx(100.0)
        assert d["fee"] == pytest.approx(0.0)

# ─── BacktestReport 測試 ───

class TestBacktestReport:
    """測試 BacktestReport 資料類別."""

    def test_default_values(self):
        """驗證預設值."""
        r = BacktestReport()
        assert r.equity_curve == []
        assert r.trades == []
        assert r.metrics == {}
        assert r.error is None

    def test_to_dict(self):
        """to_dict 應序列化 trades."""
        t = TradeRecord(
            entry_ts=0,
            exit_ts=1,
            side=1,
            entry_price=100,
            exit_price=110,
            pnl_pct=10,
            profit=10,
            fee=0,
        )
        r = BacktestReport(trades=[t], metrics={"total_return_pct": 10})
        d = r.to_dict()
        assert len(d["trades"]) == 1
        assert d["trades"][0]["entry_price"] == pytest.approx(100.0)
        assert d["metrics"]["total_return_pct"] == 10

# ─── BacktestEngine.run 測試 ───

class TestBacktestEngine:
    """測試 BacktestEngine 回測引擎."""

    def _make_rows(self, n=10, start_price=100.0, step=1.0):
        """生成模擬 OHLCV 資料."""
        rows = []
        for i in range(n):
            p = start_price + i * step
            rows.append(
                {
                    "timestamp": 1000 + i * 60000,
                    "open": p,
                    "high": p + 0.5,
                    "low": p - 0.5,
                    "close": p,
                    "volume": 1000,
                }
            )
        return rows

    def test_empty_rows(self):
        """空資料應返回帶 error 的 report."""
        engine = BacktestEngine()
        report = engine.run([], [], 0, 1000)
        assert report.error is not None
        assert report.equity_curve == []

    def test_no_signals(self):
        """全零信號（不開倉）equity 不變."""
        engine = BacktestEngine(BacktestConfig(initial_equity=10000))
        rows = self._make_rows(5)
        signals = [0] * len(rows)
        report = engine.run(rows, signals, rows[0]["timestamp"], rows[-1]["timestamp"])
        assert report.error is None
        assert len(report.trades) == 0
        # equity 應維持 10000
        assert report.equity_curve[-1]["equity"] == pytest.approx(10000.0)

    def test_long_trade_profitable(self):
        """做多且價格上漲應產生正收益."""
        config = BacktestConfig(
            initial_equity=10000,
            leverage=1.0,
            fee_rate_pct=0.0,  # 零手續費方便測試
            slippage_pct=0.0,
        )
        engine = BacktestEngine(config)
        rows = self._make_rows(10, start_price=100, step=10)
        # 前 5 根做多，第 6 根開始平倉
        signals = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
        report = engine.run(rows, signals, rows[0]["timestamp"], rows[-1]["timestamp"])
        assert len(report.trades) >= 1
        # 應該有正利潤
        assert report.metrics.get("total_return_pct", 0) > 0

    def test_with_preprocess_pipeline(self):
        """preprocess 管道應在回測前執行."""
        p = Pipeline()
        p.add(lambda rows: rows)  # 空操作
        engine = BacktestEngine(preprocess=p)
        rows = self._make_rows(5)
        signals = [0] * 5
        report = engine.run(rows, signals, rows[0]["timestamp"], rows[-1]["timestamp"])
        assert report.error is None

    def test_forced_close_at_end(self):
        """回測結束時未平倉的倉位應被強制平倉."""
        config = BacktestConfig(initial_equity=10000, fee_rate_pct=0.0, slippage_pct=0.0)
        engine = BacktestEngine(config)
        rows = self._make_rows(5)
        # 全部做多，從不平倉
        signals = [1] * 5
        report = engine.run(rows, signals, rows[0]["timestamp"], rows[-1]["timestamp"])
        # 應有一筆強制平倉的交易
        assert len(report.trades) == 1

    def test_metrics_computed(self):
        """report.metrics 應包含績效指標."""
        config = BacktestConfig(initial_equity=10000, fee_rate_pct=0.0, slippage_pct=0.0)
        engine = BacktestEngine(config)
        rows = self._make_rows(10)
        signals = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
        report = engine.run(rows, signals, rows[0]["timestamp"], rows[-1]["timestamp"])
        assert "total_return_pct" in report.metrics
        assert "max_drawdown_pct" in report.metrics
        assert "num_trades" in report.metrics

# ─── compute_performance_metrics 測試 ───

class TestComputePerformanceMetrics:
    """測試 compute_performance_metrics 函式."""

    def test_empty_equity_curve(self):
        """空 equity_curve 應返回空字典."""
        result = compute_performance_metrics([], [], 10000, 0, 1000)
        assert result == {}

    def test_no_trades(self):
        """無交易時 win_rate 為 0."""
        curve = [
            {"timestamp": 0, "equity": 10000},
            {"timestamp": 1, "equity": 10000},
            {"timestamp": 2, "equity": 10000},
        ]
        result = compute_performance_metrics(curve, [], 10000, 0, 2)
        assert result["num_trades"] == 0
        assert result["win_rate_pct"] == 0
        assert result["final_equity"] == pytest.approx(10000.0)

    def test_total_return(self):
        """總報酬率計算."""
        curve = [
            {"timestamp": 0, "equity": 10000},
            {"timestamp": 1, "equity": 11000},
        ]
        result = compute_performance_metrics(curve, [], 10000, 0, 1)
        assert result["total_return_pct"] == pytest.approx(10.0)

    def test_max_drawdown(self):
        """最大回撤計算."""
        curve = [
            {"timestamp": 0, "equity": 10000},
            {"timestamp": 1, "equity": 12000},
            {"timestamp": 2, "equity": 9000},
            {"timestamp": 3, "equity": 11000},
        ]
        result = compute_performance_metrics(curve, [], 10000, 0, 3)
        # peak=12000, trough=9000 → dd=25%
        assert result["max_drawdown_pct"] == pytest.approx(25.0)

    def test_win_rate(self):
        """勝率計算."""
        trades = [
            TradeRecord(0, 1, 1, 100, 110, 10, 100, 0),
            TradeRecord(1, 2, 1, 110, 105, -4.5, -50, 0),
            TradeRecord(2, 3, 1, 105, 115, 9.5, 95, 0),
        ]
        curve = [{"timestamp": i, "equity": 10000 + i} for i in range(4)]
        result = compute_performance_metrics(curve, trades, 10000, 0, 3)
        assert result["win_rate_pct"] == pytest.approx(66.7, abs=0.1)
        assert result["num_trades"] == 3

    def test_max_consecutive_loss(self):
        """最大連續虧損計算."""
        trades = [
            TradeRecord(0, 1, 1, 100, 110, 10, 100, 0),  # win
            TradeRecord(1, 2, 1, 100, 90, -10, -100, 0),  # loss
            TradeRecord(2, 3, 1, 100, 95, -5, -50, 0),  # loss
            TradeRecord(3, 4, 1, 100, 90, -10, -100, 0),  # loss
            TradeRecord(4, 5, 1, 100, 110, 10, 100, 0),  # win
        ]
        curve = [{"timestamp": i, "equity": 10000} for i in range(6)]
        result = compute_performance_metrics(curve, trades, 10000, 0, 5)
        assert result["max_consec_loss"] == 3

    def test_period_with_equal_since_until(self):
        """since == until 時年化報酬應為 0."""
        curve = [{"timestamp": 0, "equity": 10000}, {"timestamp": 1, "equity": 11000}]
        result = compute_performance_metrics(curve, [], 10000, 100, 100)
        assert result["annual_return_pct"] == pytest.approx(0.0)

# ─── BacktestEngine._close_position 測試 ───

class TestClosePosition:
    """測試 _close_position 輔助方法."""

    def test_profitable_close(self):
        """盈利平倉."""
        engine = BacktestEngine(BacktestConfig(initial_equity=10000, fee_rate_pct=0.0, slippage_pct=0.0))
        equity, trade = engine._close_position(
            position=1,
            entry_price=100,
            exit_price=110,
            equity=10000,
            entry_ts=0,
            exit_ts=1,
        )
        assert equity > 10000
        assert trade.pnl_pct > 0
        assert trade.profit > 0
        assert trade.liquidation is False

    def test_loss_close(self):
        """虧損平倉."""
        engine = BacktestEngine(BacktestConfig(initial_equity=10000, fee_rate_pct=0.0, slippage_pct=0.0))
        equity, trade = engine._close_position(
            position=1,
            entry_price=100,
            exit_price=90,
            equity=10000,
            entry_ts=0,
            exit_ts=1,
        )
        assert equity < 10000
        assert trade.pnl_pct < 0
        assert trade.profit < 0

    def test_short_profitable(self):
        """做空盈利."""
        engine = BacktestEngine(BacktestConfig(initial_equity=10000, fee_rate_pct=0.0, slippage_pct=0.0))
        equity, trade = engine._close_position(
            position=-1,
            entry_price=100,
            exit_price=90,
            equity=10000,
            entry_ts=0,
            exit_ts=1,
        )
        assert equity > 10000
        assert trade.side == -1
        assert trade.pnl_pct > 0

    def test_liquidation(self):
        """虧損到歸零應標記為 liquidation."""
        engine = BacktestEngine(
            BacktestConfig(
                initial_equity=10000,
                leverage=10.0,
                fee_rate_pct=0.0,
                slippage_pct=0.0,
            )
        )
        equity, trade = engine._close_position(
            position=1,
            entry_price=100,
            exit_price=90,
            equity=10000,
            entry_ts=0,
            exit_ts=1,
        )
        # 10x leverage, 10% drop → 100% loss → liquidation
        assert equity == 0.0
        assert trade.liquidation is True

    def test_with_fees(self):
        """手續費應減少最終權益."""
        engine_no_fee = BacktestEngine(BacktestConfig(initial_equity=10000, fee_rate_pct=0.0, slippage_pct=0.0))
        engine_with_fee = BacktestEngine(BacktestConfig(initial_equity=10000, fee_rate_pct=0.1, slippage_pct=0.0))
        equity_no_fee, _ = engine_no_fee._close_position(
            1,
            100,
            100,
            10000,
            0,
            1,
            "test",
        )
        equity_with_fee, _ = engine_with_fee._close_position(
            1,
            100,
            100,
            10000,
            0,
            1,
            "test",
        )
        assert equity_with_fee < equity_no_fee

    def test_exit_reason_preserved(self):
        """exit_reason 應被正確傳遞."""
        engine = BacktestEngine(BacktestConfig(initial_equity=10000, fee_rate_pct=0.0, slippage_pct=0.0))
        _, trade = engine._close_position(
            1,
            100,
            110,
            10000,
            0,
            1,
            "tp",
        )
        assert trade.exit_reason == "tp"

# ─── BacktestEngine TP/SL 測試 ───

class TestBacktestTPSL:
    """測試止盈止損邏輯."""

    def _make_rising_rows(self, n=10, start=100.0, step=5.0):
        return [
            {
                "timestamp": i * 1000,
                "open": start + i * step,
                "high": start + i * step + 2,
                "low": start + i * step - 2,
                "close": start + i * step,
                "volume": 1000,
            }
            for i in range(n)
        ]

    def test_take_profit_triggers(self):
        """止盈應在觸及目標價時平倉."""
        config = BacktestConfig(
            initial_equity=10000,
            take_profit_pct=10.0,
            fee_rate_pct=0.0,
            slippage_pct=0.0,
        )
        engine = BacktestEngine(config)
        rows = self._make_rising_rows(20, start=100, step=10)
        signals = [1] * 20  # 一直做多
        report = engine.run(rows, signals, 0, 19000)
        # 應有至少一筆 TP 平倉
        tp_trades = [t for t in report.trades if t.exit_reason == "tp"]
        assert len(tp_trades) >= 1

    def test_stop_loss_triggers(self):
        """止損應在觸及止損價時平倉."""
        config = BacktestConfig(
            initial_equity=10000,
            stop_loss_pct=5.0,
            fee_rate_pct=0.0,
            slippage_pct=0.0,
        )
        engine = BacktestEngine(config)
        rows = [
            {
                "timestamp": i * 1000,
                "open": 100,
                "high": 100,
                "low": 100 - i * 2,  # 不斷下跌
                "close": 100 - i * 2,
                "volume": 1000,
            }
            for i in range(20)
        ]
        signals = [1] * 20
        report = engine.run(rows, signals, 0, 19000)
        sl_trades = [t for t in report.trades if t.exit_reason == "sl"]
        assert len(sl_trades) >= 1

    def test_short_stop_loss(self):
        """做空止損."""
        config = BacktestConfig(
            initial_equity=10000,
            stop_loss_pct=5.0,
            fee_rate_pct=0.0,
            slippage_pct=0.0,
        )
        engine = BacktestEngine(config)
        rows = [
            {
                "timestamp": i * 1000,
                "open": 100,
                "high": 100 + i * 2,  # 不斷上漲（做空虧損）
                "low": 100,
                "close": 100 + i * 2,
                "volume": 1000,
            }
            for i in range(20)
        ]
        signals = [-1] * 20  # 做空
        report = engine.run(rows, signals, 0, 19000)
        sl_trades = [t for t in report.trades if t.exit_reason == "sl"]
        assert len(sl_trades) >= 1
