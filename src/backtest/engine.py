# 回測引擎：取得 K 線、跑策略、計算權益曲線與績效指標
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from src.data.crypto import CryptoDataFetcher

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
    if not equity_curve:
        return {}
    equity = equity_curve[-1]["equity"]
    total_return = (equity - initial_equity) / initial_equity if initial_equity else 0
    equities = [e["equity"] for e in equity_curve]
    peak = equities[0]
    max_dd = 0.0
    for e in equities:
        if e > peak:
            peak = e
        dd = (peak - e) / peak if peak else 0
        if dd > max_dd:
            max_dd = dd

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

    bar_returns = []
    for j in range(1, len(equities)):
        r = (equities[j] - equities[j - 1]) / equities[j - 1] if equities[j - 1] else 0
        bar_returns.append(r)
    if bar_returns:
        mean_r = sum(bar_returns) / len(bar_returns)
        var_r = sum((x - mean_r) ** 2 for x in bar_returns) / len(bar_returns)
        std_r = math.sqrt(var_r) if var_r > 0 else 0
        sharpe = (mean_r / std_r * math.sqrt(252)) if std_r else 0.0
        # Sortino: 只考慮負報酬的標準差
        neg_returns = [x for x in bar_returns if x < 0]
        std_neg = math.sqrt(sum(x * x for x in neg_returns) / len(neg_returns)) if neg_returns else 0
        sortino = (mean_r / std_neg * math.sqrt(252)) if std_neg else 0.0
        # Calmar = 年化報酬 / 最大回撤
        calmar = (annual_return / max_dd) if max_dd > 0 else 0.0
    else:
        sharpe = sortino = calmar = 0.0

    win_trades = [t for t in trades if t.get("pnl_pct", 0) > 0]
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
        "num_trades": len(trades),
        "win_rate_pct": round(100 * len(win_trades) / len(trades), 1) if trades else 0,
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
) -> BacktestResult:
    """核心回測邏輯：假設 K 線已經準備好，方便 optimizer 重複使用。"""
    out = BacktestResult()
    if not rows:
        out.error = "無 K 線資料，請先拉取數據或調整時間範圍。"
        return out

    out.raw_ohlcv = rows
    sig = strategies.get_signal(strategy, rows, **strategy_params)

    equity = initial_equity
    position = 0
    entry_price = 0.0
    entry_ts_prev = since_ms
    equity_curve = []
    trades = []
    liquidated = False

    for i, r in enumerate(rows):
        ts = r["timestamp"]
        o = r["open"]
        h = r["high"]
        l = r["low"]
        close = r["close"]
        target = sig[i] if i < len(sig) else 0

        if liquidated:
            equity_curve.append({"timestamp": ts, "equity": 0.0, "position": 0})
            continue

        # 先檢查本 bar 是否觸發止盈 / 止損（依 high/low 判斷是否觸價）
        if position != 0 and entry_price and (take_profit_pct or stop_loss_pct):
            direction = position  # 1 = 多，-1 = 空
            tp_price = None
            sl_price = None
            if take_profit_pct and take_profit_pct > 0:
                if direction == 1:
                    tp_price = entry_price * (1 + take_profit_pct / 100.0)
                else:
                    tp_price = entry_price * (1 - take_profit_pct / 100.0)
            if stop_loss_pct and stop_loss_pct > 0:
                if direction == 1:
                    sl_price = entry_price * (1 - stop_loss_pct / 100.0)
                else:
                    sl_price = entry_price * (1 + stop_loss_pct / 100.0)
            touched_sl = sl_price is not None and l <= sl_price <= h
            touched_tp = tp_price is not None and l <= tp_price <= h
            exit_price = None
            exit_reason = None
            # 保守假設：同一根同時觸達 TP 與 SL 時，先觸發止損
            if touched_sl:
                exit_price = sl_price
                exit_reason = "sl"
            elif touched_tp:
                exit_price = tp_price
                exit_reason = "tp"
            if exit_price is not None:
                price_return = (exit_price - entry_price) / entry_price * direction
                pnl_pct = price_return * leverage
                equity_before = equity
                equity *= 1 + pnl_pct
                profit = equity_before * pnl_pct
                if equity <= 0:
                    equity = 0.0
                    profit = -equity_before
                    pnl_pct = -1.0
                    liquidated = True
                trades.append({
                    "entry_ts": entry_ts_prev,
                    "exit_ts": ts,
                    "side": direction,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl_pct": round(pnl_pct * 100, 4),
                    "profit": round(profit, 2),
                    "liquidation": liquidated,
                    "exit_reason": exit_reason,
                })
                position = 0
                entry_price = 0.0
                equity_curve.append({"timestamp": ts, "equity": round(equity, 2), "position": position})
                # 爆倉或本 bar 已 TP/SL 平倉後，不再處理本 bar 其他訊號
                continue

        if position != 0 and target != position and entry_price:
            # 平倉：根據當前持倉方向（多=1 / 空=-1）計算報酬
            direction = position  # 1 = 多，-1 = 空
            price_return = (close - entry_price) / entry_price * direction
            pnl_pct = price_return * leverage
            equity_before = equity
            equity *= 1 + pnl_pct
            profit = equity_before * pnl_pct
            if equity <= 0:
                equity = 0.0
                profit = -equity_before
                pnl_pct = -1.0
                liquidated = True
            trades.append({
                "entry_ts": entry_ts_prev,
                "exit_ts": ts,
                "side": direction,
                "entry_price": entry_price,
                "exit_price": close,
                "pnl_pct": round(pnl_pct * 100, 4),
                "profit": round(profit, 2),
                "liquidation": liquidated,
            })
            position = 0
            entry_price = 0.0

        if not liquidated and target != 0 and position == 0:
            position = target
            entry_price = close
            entry_ts_prev = ts

        # Mark-to-market：持倉期間按當前收盤價計算未實現盈虧
        if position != 0 and entry_price:
            direction = position
            unrealized_return = (close - entry_price) / entry_price * direction
            mtm_equity = equity * (1 + unrealized_return * leverage)
        else:
            mtm_equity = equity
        equity_curve.append({"timestamp": ts, "equity": round(mtm_equity, 2), "position": position})

    if not liquidated and position != 0 and entry_price and rows:
        # 最後一根 K 線強制平倉（依方向支援多 / 空）
        last_close = rows[-1]["close"]
        direction = position
        price_return = (last_close - entry_price) / entry_price * direction
        pnl_pct = price_return * leverage
        equity_before = equity
        equity *= 1 + pnl_pct
        profit = equity_before * pnl_pct
        if equity <= 0:
            equity = 0.0
            profit = -equity_before
            pnl_pct = -1.0
        trades.append({
            "entry_ts": entry_ts_prev,
            "exit_ts": rows[-1]["timestamp"],
            "side": direction,
            "entry_price": entry_price,
            "exit_price": last_close,
            "pnl_pct": round(pnl_pct * 100, 4),
            "profit": round(profit, 2),
            "liquidation": equity == 0,
        })
        # 更新最後一筆權益曲線為平倉後的實際權益
        if equity_curve:
            equity_curve[-1]["equity"] = round(equity, 2)
            equity_curve[-1]["position"] = 0

    out.equity_curve = equity_curve
    out.trades = trades
    out.metrics = _compute_metrics(equity_curve, trades, initial_equity, since_ms, until_ms, leverage=leverage)
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
        fetcher = CryptoDataFetcher(exchange_id)
        rows = fetcher.get_ohlcv(symbol, timeframe, since_ms, until_ms, fill_gaps=True, exclude_outliers=exclude_outliers)
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
