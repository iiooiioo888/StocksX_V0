"""
Compatibility Bridge — 新舊架構橋接

讓新的 BacktestReport 可被舊的 UI 渲染函數使用。
同時提供 run_all_strategies 的新實現。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.backtest import BacktestEngine, BacktestConfig, BacktestReport
from src.core.registry import registry


# 定義本地 BacktestResult，避免導入舊 engine.py 的循環依賴
@dataclass
class BacktestResult:
    """回測結果（UI 兼容格式）."""

    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    raw_ohlcv: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


def report_to_result(report: BacktestReport) -> BacktestResult:
    """將新的 BacktestReport 轉換為舊的 BacktestResult（UI 兼容）."""
    result = BacktestResult()
    result.equity_curve = report.equity_curve
    result.trades = [t.to_dict() for t in report.trades]
    result.metrics = report.metrics
    result.raw_ohlcv = report.raw_ohlcv
    result.error = report.error
    return result


def run_all_strategies_new(
    rows: list[dict[str, Any]],
    since_ms: int,
    until_ms: int,
    initial_equity: float = 10000,
    leverage: float = 1.0,
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    fee_rate: float = 0.05,
    slippage: float = 0.01,
) -> dict[str, BacktestResult]:
    """
    使用新架構執行所有策略回測。

    替代舊的 ui_backtest.run_all_strategies。
    使用 Registry + BacktestEngine。
    """
    results: dict[str, BacktestResult] = {}
    config = BacktestConfig(
        initial_equity=initial_equity,
        leverage=leverage,
        fee_rate_pct=fee_rate,
        slippage_pct=slippage,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
    )
    engine = BacktestEngine(config=config)

    for meta in registry.list_all():
        strategy = meta.name
        try:
            # 用 Registry 計算信號
            signals = registry.get_signal(strategy, rows, **meta.defaults)
            # 用新引擎執行回測
            report = engine.run(rows, signals, since_ms, until_ms)
            results[strategy] = report_to_result(report)
        except Exception as e:
            err_result = BacktestResult()
            err_result.error = str(e)
            results[strategy] = err_result

    return results


def run_single_strategy_new(
    rows: list[dict[str, Any]],
    strategy: str,
    strategy_params: dict[str, Any],
    since_ms: int,
    until_ms: int,
    initial_equity: float = 10000,
    leverage: float = 1.0,
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    fee_rate: float = 0.05,
    slippage: float = 0.01,
) -> BacktestResult:
    """
    使用新架構執行單一策略回測。

    替代舊的 engine.run_backtest。
    """
    config = BacktestConfig(
        initial_equity=initial_equity,
        leverage=leverage,
        fee_rate_pct=fee_rate,
        slippage_pct=slippage,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
    )
    engine = BacktestEngine(config=config)

    try:
        signals = registry.get_signal(strategy, rows, **strategy_params)
        report = engine.run(rows, signals, since_ms, until_ms)
        return report_to_result(report)
    except Exception as e:
        err_result = BacktestResult()
        err_result.error = str(e)
        return err_result
