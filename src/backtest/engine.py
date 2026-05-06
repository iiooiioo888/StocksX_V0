# 回測引擎 v2.0 — 統一高性能版
# 合併 engine.py 和 engine_vec.py，消除重複代碼
# 使用 OHLCVArrays 避免重複數組創建
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .np_utils import OHLCVArrays

from . import strategies


@dataclass
class BacktestResult:
    """回測結果：權益曲線、交易明細、績效指標."""

    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    raw_ohlcv: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


def _compute_metrics(
    equity_curve: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    initial_equity: float,
    since_ms: int,
    until_ms: int,
    leverage: float = 1.0,
) -> dict[str, Any]:
    """向量化績效指標計算（NumPy 加速）。"""
    if not equity_curve:
        return {}

    equities = np.array([e["equity"] for e in equity_curve], dtype=np.float64)
    equity = float(equities[-1])
    total_return = (equity - initial_equity) / initial_equity if initial_equity else 0

    # 向量化最大回撤
    peak = np.maximum.accumulate(equities)
    with np.errstate(divide="ignore", invalid="ignore"):
        drawdowns = np.where(peak > 0, (peak - equities) / peak, 0.0)
    max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

    n_bars = len(equity_curve)
    period_years = (until_ms - since_ms) / (1000 * 86400 * 365.25) if since_ms < until_ms else 0
    if period_years <= 0 or (1 + total_return) <= 0:
        annual_return = 0.0
    else:
        try:
            ar = (1 + total_return) ** (1 / period_years) - 1
            annual_return = float(ar.real) if isinstance(ar, complex) else ar
        except (ValueError, ZeroDivisionError):
            annual_return = 0.0

    # 向量化報酬率計算
    if len(equities) > 1:
        prev_eq = equities[:-1]
        with np.errstate(divide="ignore", invalid="ignore"):
            bar_returns = np.where(prev_eq > 0, (equities[1:] - prev_eq) / prev_eq, 0.0)
    else:
        bar_returns = np.array([], dtype=np.float64)

    if len(bar_returns) > 0:
        mean_r = float(np.mean(bar_returns))
        std_r = float(np.std(bar_returns))
        sharpe = (mean_r / std_r * math.sqrt(252)) if std_r > 0 else 0.0
        neg = bar_returns[bar_returns < 0]
        std_neg = float(np.sqrt(np.mean(neg ** 2))) if len(neg) > 0 else 0.0
        sortino = (mean_r / std_neg * math.sqrt(252)) if std_neg > 0 else 0.0
        calmar = (annual_return / max_dd) if max_dd > 0 else 0.0
    else:
        sharpe = sortino = calmar = 0.0

    # 交易統計
    pnl_arr = np.array([t.get("pnl_pct", 0) for t in trades], dtype=np.float64) if trades else np.array([])
    profit_arr = np.array([t.get("profit", 0) for t in trades], dtype=np.float64) if trades else np.array([])

    win_mask = pnl_arr > 0
    loss_mask = pnl_arr < 0
    win_trades_count = int(np.sum(win_mask))
    loss_trades_count = int(np.sum(loss_mask))

    gross_profit = float(np.sum(profit_arr[win_mask])) if win_trades_count > 0 else 0.0
    gross_loss = abs(float(np.sum(profit_arr[loss_mask]))) if loss_trades_count > 0 else 0.0
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0.0

    # Omega Ratio
    if len(bar_returns) > 0:
        pos_sum = float(np.sum(bar_returns[bar_returns > 0]))
        neg_sum = float(np.sum(np.abs(bar_returns[bar_returns < 0])))
        omega = round(pos_sum / neg_sum, 2) if neg_sum > 0 else 0.0
    else:
        omega = 0.0

    # Tail Ratio
    if len(bar_returns) >= 20:
        sorted_r = np.sort(bar_returns)
        p95 = sorted_r[int(len(sorted_r) * 0.95)]
        p5 = sorted_r[int(len(sorted_r) * 0.05)]
        tail_ratio = round(float(p95 / abs(p5)), 2) if p5 != 0 else 0.0
    else:
        tail_ratio = 0.0

    # 平均盈虧
    avg_win = round(float(np.mean(profit_arr[win_mask])), 2) if win_trades_count > 0 else 0
    avg_loss = round(float(np.mean(profit_arr[loss_mask])), 2) if loss_trades_count > 0 else 0

    # 最大連續虧損（向量化）
    if len(profit_arr) > 0:
        is_loss = (profit_arr < 0).astype(np.int32)
        if np.any(is_loss):
            padded = np.concatenate([[0], is_loss, [0]])
            diff = np.diff(padded)
            starts = np.where(diff == 1)[0]
            ends = np.where(diff == -1)[0]
            if len(starts) > 0 and len(ends) > 0:
                max_consec_loss = int(np.max(ends - starts))
            else:
                max_consec_loss = 0
        else:
            max_consec_loss = 0
    else:
        max_consec_loss = 0

    return {
        "leverage": leverage,
        "initial_equity": initial_equity,
        "final_equity": round(equity, 2),
        "total_return_pct": round(total_return * 100, 2),
        "annual_return_pct": round(annual_return * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "calmar_ratio": round(calmar, 2),
        "profit_factor": profit_factor,
        "omega_ratio": omega,
        "tail_ratio": tail_ratio,
        "num_trades": len(trades),
        "win_rate_pct": round(100 * win_trades_count / len(trades), 1) if trades else 0,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "max_consec_loss": max_consec_loss,
        "period_bars": n_bars,
    }


def _run_backtest_on_rows(
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
    """
    核心回測邏輯 — 高性能版。

    優化：
    1. 使用 OHLCVArrays 預提取所有數組，消除循環內 dict 查找
    2. 信號一次性計算
    3. 權益曲線最後批量構建
    """
    out = BacktestResult()
    if not rows:
        out.error = "無 K 線資料，請先拉取數據或調整時間範圍。"
        return out

    out.raw_ohlcv = rows

    # 預提取所有數組（一次性，避免循環內重複 dict 查找）
    arr = OHLCVArrays.from_rows(rows)
    timestamps = arr.timestamps
    highs = arr.highs
    lows = arr.lows
    closes = arr.closes
    n = arr.n

    # 一次性計算所有信號
    sig = strategies.get_signal(strategy, rows, **strategy_params)
    signals = np.array(sig, dtype=np.int32) if len(sig) == n else np.zeros(n, dtype=np.int32)

    cost_pct = (fee_rate + slippage) / 100
    total_fees = 0.0

    equity = initial_equity
    position = 0
    entry_price = 0.0
    entry_ts_prev = since_ms
    trades = []
    liquidated = False

    # 權益曲線用 numpy 構建，最後批量轉換
    equity_arr = np.empty(n, dtype=np.float64)
    position_arr = np.empty(n, dtype=np.int32)

    for i in range(n):
        ts = timestamps[i]
        h = highs[i]
        l = lows[i]
        close = closes[i]
        target = signals[i]

        if liquidated:
            equity_arr[i] = 0.0
            position_arr[i] = 0
            continue

        # TP/SL 檢查
        if position != 0 and entry_price and (take_profit_pct or stop_loss_pct):
            direction = position
            tp_price = None
            sl_price = None
            if take_profit_pct and take_profit_pct > 0:
                tp_price = entry_price * (1 + take_profit_pct / 100.0) if direction == 1 else entry_price * (1 - take_profit_pct / 100.0)
            if stop_loss_pct and stop_loss_pct > 0:
                sl_price = entry_price * (1 - stop_loss_pct / 100.0) if direction == 1 else entry_price * (1 + stop_loss_pct / 100.0)

            touched_sl = sl_price is not None and l <= sl_price <= h
            touched_tp = tp_price is not None and l <= tp_price <= h
            exit_price = None
            exit_reason = None
            if touched_sl:
                exit_price = sl_price
                exit_reason = "sl"
            elif touched_tp:
                exit_price = tp_price
                exit_reason = "tp"

            if exit_price is not None:
                price_return = (exit_price - entry_price) / entry_price * direction
                round_trip_cost = cost_pct * 2
                pnl_pct = price_return * leverage - round_trip_cost
                equity_before = equity
                fee_amount = equity_before * round_trip_cost
                total_fees += fee_amount
                equity *= 1 + pnl_pct
                profit = equity_before * pnl_pct
                if equity <= 0:
                    equity = 0.0
                    profit = -equity_before
                    pnl_pct = -1.0
                    liquidated = True
                trades.append({
                    "entry_ts": entry_ts_prev, "exit_ts": ts, "side": direction,
                    "entry_price": entry_price, "exit_price": exit_price,
                    "pnl_pct": round(pnl_pct * 100, 4), "profit": round(profit, 2),
                    "fee": round(fee_amount, 2), "liquidation": liquidated, "exit_reason": exit_reason,
                })
                position = 0
                entry_price = 0.0
                equity_arr[i] = equity
                position_arr[i] = 0
                continue

        # 信號變化平倉
        if position != 0 and target != position and entry_price:
            direction = position
            price_return = (close - entry_price) / entry_price * direction
            round_trip_cost = cost_pct * 2
            pnl_pct = price_return * leverage - round_trip_cost
            equity_before = equity
            fee_amount = equity_before * round_trip_cost
            total_fees += fee_amount
            equity *= 1 + pnl_pct
            profit = equity_before * pnl_pct
            if equity <= 0:
                equity = 0.0
                profit = -equity_before
                pnl_pct = -1.0
                liquidated = True
            trades.append({
                "entry_ts": entry_ts_prev, "exit_ts": ts, "side": direction,
                "entry_price": entry_price, "exit_price": close,
                "pnl_pct": round(pnl_pct * 100, 4), "profit": round(profit, 2),
                "fee": round(fee_amount, 2), "liquidation": liquidated,
            })
            position = 0
            entry_price = 0.0

        # 開倉
        if not liquidated and target != 0 and position == 0:
            position = target
            entry_price = close
            entry_ts_prev = ts

        # Mark-to-market
        if position != 0 and entry_price:
            unrealized_return = (close - entry_price) / entry_price * position
            mtm_equity = equity * (1 + unrealized_return * leverage)
        else:
            mtm_equity = equity

        equity_arr[i] = mtm_equity
        position_arr[i] = position

    # 強制平倉
    if not liquidated and position != 0 and entry_price and n > 0:
        last_close = closes[-1]
        direction = position
        price_return = (last_close - entry_price) / entry_price * direction
        round_trip_cost = cost_pct * 2
        pnl_pct = price_return * leverage - round_trip_cost
        equity_before = equity
        fee_amount = equity_before * round_trip_cost
        total_fees += fee_amount
        equity *= 1 + pnl_pct
        profit = equity_before * pnl_pct
        if equity <= 0:
            equity = 0.0
            profit = -equity_before
            pnl_pct = -1.0
        trades.append({
            "entry_ts": entry_ts_prev, "exit_ts": timestamps[-1], "side": direction,
            "entry_price": entry_price, "fee": round(fee_amount, 2),
            "exit_price": last_close, "pnl_pct": round(pnl_pct * 100, 4),
            "profit": round(profit, 2), "liquidation": equity == 0,
        })
        equity_arr[-1] = equity
        position_arr[-1] = 0

    # 批量構建權益曲線（避免逐條 dict 構建）
    out.equity_curve = [
        {"timestamp": int(timestamps[i]), "equity": round(float(equity_arr[i]), 2), "position": int(position_arr[i])}
        for i in range(n)
    ]
    out.trades = trades
    out.metrics = _compute_metrics(out.equity_curve, trades, initial_equity, since_ms, until_ms, leverage=leverage)
    out.metrics["total_fees"] = round(total_fees, 2)
    out.metrics["fee_rate_pct"] = fee_rate
    out.metrics["slippage_pct"] = slippage
    return out


def run_backtest(
    exchange_id: str,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int,
    strategy: str = "sma_cross",
    strategy_params: dict[str, Any] | None = None,
    initial_equity: float = 10000.0,
    leverage: float = 1.0,
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    exclude_outliers: bool = False,
) -> BacktestResult:
    """
    執行回測。策略可選：sma_cross, buy_and_hold, rsi_signal, macd_cross, bollinger_signal。
    對外仍會自動透過 CryptoDataFetcher 取得 K 線。
    """
    strategy_params = strategy_params or {}
    out = BacktestResult()
    try:
        from src.data.crypto import CryptoDataFetcher
        fetcher = CryptoDataFetcher(exchange_id)
        rows = fetcher.get_ohlcv(
            symbol, timeframe, since_ms, until_ms, fill_gaps=True, exclude_outliers=exclude_outliers
        )
    except Exception as e:
        out.error = str(e)
        return out

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
    )


# Public alias
compute_metrics = _compute_metrics
