"""
向量化回測引擎 — v2.0

此模塊已合併至 engine.py（統一高性能版）。
保留此文件向後兼容。

使用方式不變：
    from src.backtest.engine_vec import _run_backtest_vectorized
"""

from __future__ import annotations

from typing import Any

from .engine import BacktestResult, _run_backtest_on_rows


def _run_backtest_vectorized(
    rows: list[dict[str, Any]],
    exchange_id: str,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int,
    strategy: str,
    strategy_params: dict[str, Any],
    initial_equity: float,
    leverage: float,
    take_profit_pct: float | None,
    stop_loss_pct: float | None,
    fee_rate: float = 0.0,
    slippage: float = 0.0,
) -> BacktestResult:
    """向向量化回測（已統一至 engine.py）。"""
    return _run_backtest_on_rows(
        rows=rows,
        exchange_id=exchange_id,
        symbol=symbol,
        timeframe=timeframe,
        since_ms=since_ms,
        until_ms=until_ms,
        strategy=strategy,
        strategy_params=strategy_params,
        initial_equity=initial_equity,
        leverage=leverage,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        fee_rate=fee_rate,
        slippage=slippage,
    )
