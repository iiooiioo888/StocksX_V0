"""
Backtest Engine — 現代化回測引擎

Pipeline 架構：
  OHLCV → Clean Pipeline → Strategy Signals → Risk Management → Portfolio Simulation → Report

取代舊版分散在 engine.py / engine_vec.py 的重複邏輯。
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from .pipeline import Pipeline

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# 配置
# ════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    """回測配置（不可變）."""

    initial_equity: float = 10_000.0
    leverage: float = 1.0
    fee_rate_pct: float = 0.05  # 單邊手續費 %
    slippage_pct: float = 0.01
    take_profit_pct: float | None = None
    stop_loss_pct: float | None = None


# ════════════════════════════════════════════════════════════
# 報告
# ════════════════════════════════════════════════════════════


@dataclass(slots=True)
class TradeRecord:
    """交易記錄."""

    entry_ts: int
    exit_ts: int
    side: int  # 1=多, -1=空
    entry_price: float
    exit_price: float
    pnl_pct: float
    profit: float
    fee: float
    liquidation: bool = False
    exit_reason: str = "signal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_ts": self.entry_ts,
            "exit_ts": self.exit_ts,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl_pct": round(self.pnl_pct, 4),
            "profit": round(self.profit, 2),
            "fee": round(self.fee, 2),
            "liquidation": self.liquidation,
            "exit_reason": self.exit_reason,
        }


@dataclass(slots=True)
class BacktestReport:
    """回測報告（統一輸出格式）."""

    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    trades: list[TradeRecord] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    raw_ohlcv: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "equity_curve": self.equity_curve,
            "trades": [t.to_dict() for t in self.trades],
            "metrics": self.metrics,
            "error": self.error,
        }


# ════════════════════════════════════════════════════════════
# 指標計算
# ════════════════════════════════════════════════════════════


def compute_performance_metrics(
    equity_curve: list[dict[str, Any]],
    trades: list[TradeRecord],
    initial_equity: float,
    since_ms: int,
    until_ms: int,
    leverage: float = 1.0,
) -> dict[str, Any]:
    """計算績效指標."""
    if not equity_curve:
        return {}

    equity = equity_curve[-1]["equity"]
    total_return = (equity - initial_equity) / initial_equity if initial_equity else 0
    equities = [e["equity"] for e in equity_curve]

    # Max Drawdown
    peak = equities[0]
    max_dd = 0.0
    for e in equities:
        if e > peak:
            peak = e
        dd = (peak - e) / peak if peak else 0
        if dd > max_dd:
            max_dd = dd

    # Annualized Return
    period_years = (until_ms - since_ms) / (1000 * 86400 * 365.25) if since_ms < until_ms else 0
    if period_years <= 0 or (1 + total_return) <= 0:
        annual_return = 0.0
    else:
        try:
            exponent = 1 / period_years
            if exponent > 100:
                # 避免極端指數溢出
                annual_return = total_return / period_years
            else:
                ar = (1 + total_return) ** exponent - 1
                annual_return = float(ar.real) if isinstance(ar, complex) else ar
        except (ValueError, ZeroDivisionError, OverflowError):
            annual_return = 0.0

    # Bar Returns
    bar_returns = []
    for j in range(1, len(equities)):
        r = (equities[j] - equities[j - 1]) / equities[j - 1] if equities[j - 1] else 0
        bar_returns.append(r)

    if bar_returns:
        mean_r = sum(bar_returns) / len(bar_returns)
        var_r = sum((x - mean_r) ** 2 for x in bar_returns) / len(bar_returns)
        std_r = math.sqrt(var_r) if var_r > 0 else 0
        sharpe = (mean_r / std_r * math.sqrt(252)) if std_r else 0.0
        neg_returns = [x for x in bar_returns if x < 0]
        std_neg = math.sqrt(sum(x * x for x in neg_returns) / len(neg_returns)) if neg_returns else 0
        sortino = (mean_r / std_neg * math.sqrt(252)) if std_neg else 0.0
        calmar = (annual_return / max_dd) if max_dd > 0 else 0.0
    else:
        sharpe = sortino = calmar = 0.0

    # Trade Stats
    win_trades = [t for t in trades if t.pnl_pct > 0]
    loss_trades = [t for t in trades if t.pnl_pct < 0]
    gross_profit = sum(t.profit for t in win_trades)
    gross_loss = abs(sum(t.profit for t in loss_trades))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0.0

    # Omega Ratio
    pos_returns = [r for r in bar_returns if r > 0] if bar_returns else []
    neg_abs = [abs(r) for r in bar_returns if r < 0] if bar_returns else []
    omega = round(sum(pos_returns) / sum(neg_abs), 2) if neg_abs and sum(neg_abs) > 0 else 0.0

    # Tail Ratio
    if bar_returns and len(bar_returns) >= 20:
        sorted_r = sorted(bar_returns)
        p95 = sorted_r[int(len(sorted_r) * 0.95)]
        p5 = sorted_r[int(len(sorted_r) * 0.05)]
        tail_ratio = round(p95 / abs(p5), 2) if p5 != 0 else 0.0
    else:
        tail_ratio = 0.0

    avg_win = round(sum(t.profit for t in win_trades) / len(win_trades), 2) if win_trades else 0
    avg_loss = round(sum(t.profit for t in loss_trades) / len(loss_trades), 2) if loss_trades else 0

    max_consec_loss = 0
    cur_consec = 0
    for t in trades:
        if t.profit < 0:
            cur_consec += 1
            max_consec_loss = max(max_consec_loss, cur_consec)
        else:
            cur_consec = 0

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
        "win_rate_pct": round(100 * len(win_trades) / len(trades), 1) if trades else 0,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "max_consec_loss": max_consec_loss,
        "period_bars": len(equity_curve),
    }


# ════════════════════════════════════════════════════════════
# 回測引擎
# ════════════════════════════════════════════════════════════


class BacktestEngine:
    """
    現代化回測引擎。

    特點：
    - Pipeline 驅動：可插入自定義清洗、風控步驟
    - 信號驅動：接受 list[int] 信號
    - 統一輸出：BacktestReport
    """

    def __init__(
        self,
        config: BacktestConfig | None = None,
        preprocess: Pipeline[list[dict[str, Any]]] | None = None,
    ) -> None:
        self.config = config or BacktestConfig()
        self.preprocess = preprocess

    def _close_position(
        self,
        position: int,
        entry_price: float,
        exit_price: float,
        equity: float,
        entry_ts: int,
        exit_ts: int,
        exit_reason: str = "signal",
    ) -> tuple[float, TradeRecord]:
        """平倉計算：返回 (新權益, TradeRecord)."""
        cfg = self.config
        cost_pct = (cfg.fee_rate_pct + cfg.slippage_pct) / 100
        direction = position
        price_return = (exit_price - entry_price) / entry_price * direction
        rt_cost = cost_pct * 2
        pnl_pct = price_return * cfg.leverage - rt_cost
        fee_amount = equity * rt_cost
        equity_before = equity
        equity *= 1 + pnl_pct
        profit = equity_before * pnl_pct
        liquidated = equity <= 0

        if liquidated:
            equity = 0.0
            profit = -equity_before
            pnl_pct = -1.0

        trade = TradeRecord(
            entry_ts=int(entry_ts),
            exit_ts=int(exit_ts),
            side=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl_pct=pnl_pct * 100,
            profit=profit,
            fee=fee_amount,
            liquidation=liquidated,
            exit_reason=exit_reason,
        )
        return equity, trade

    def run(
        self,
        rows: list[dict[str, Any]],
        signals: list[int],
        since_ms: int,
        until_ms: int,
    ) -> BacktestReport:
        """執行回測."""
        report = BacktestReport()

        # 預處理
        if self.preprocess:
            rows = self.preprocess.run(rows)

        if not rows:
            report.error = "無 K 線資料"
            return report

        report.raw_ohlcv = rows
        cfg = self.config

        equity = cfg.initial_equity
        position = 0
        entry_price = 0.0
        entry_ts = since_ms
        equity_curve: list[dict[str, Any]] = []
        trades: list[TradeRecord] = []
        liquidated = False

        for i, r in enumerate(rows):
            ts = r["timestamp"]
            h = r["high"]
            l = r["low"]
            close = r["close"]
            target = signals[i] if i < len(signals) else 0

            if liquidated:
                equity_curve.append({"timestamp": ts, "equity": 0.0, "position": 0})
                continue

            # ── TP/SL 檢查 ──
            if position != 0 and entry_price and (cfg.take_profit_pct or cfg.stop_loss_pct):
                tp_price = sl_price = None
                if cfg.take_profit_pct and cfg.take_profit_pct > 0:
                    tp_price = (
                        entry_price * (1 + cfg.take_profit_pct / 100)
                        if position == 1
                        else entry_price * (1 - cfg.take_profit_pct / 100)
                    )
                if cfg.stop_loss_pct and cfg.stop_loss_pct > 0:
                    sl_price = (
                        entry_price * (1 - cfg.stop_loss_pct / 100)
                        if position == 1
                        else entry_price * (1 + cfg.stop_loss_pct / 100)
                    )

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
                    equity, trade = self._close_position(
                        position, entry_price, exit_price, equity,
                        entry_ts, ts, exit_reason,
                    )
                    trades.append(trade)
                    liquidated = trade.liquidation
                    position = 0
                    entry_price = 0.0
                    equity_curve.append({"timestamp": ts, "equity": round(equity, 2), "position": 0})
                    continue

            # ── 信號平倉 ──
            if position != 0 and target != position and entry_price:
                equity, trade = self._close_position(
                    position, entry_price, close, equity,
                    entry_ts, ts, "signal",
                )
                trades.append(trade)
                liquidated = trade.liquidation
                position = 0
                entry_price = 0.0

            # ── 開倉 ──
            if not liquidated and target != 0 and position == 0:
                position = target
                entry_price = close
                entry_ts = ts

            # ── Mark-to-market ──
            if position != 0 and entry_price:
                unrealized = (close - entry_price) / entry_price * position * cfg.leverage
                mtm_equity = equity * (1 + unrealized)
            else:
                mtm_equity = equity
            equity_curve.append({"timestamp": ts, "equity": round(mtm_equity, 2), "position": position})

        # ── 強制平倉 ──
        if not liquidated and position != 0 and entry_price and rows:
            last_close = rows[-1]["close"]
            equity, trade = self._close_position(
                position, entry_price, last_close, equity,
                entry_ts, rows[-1]["timestamp"], "end",
            )
            trades.append(trade)
            if equity_curve:
                equity_curve[-1]["equity"] = round(equity, 2)
                equity_curve[-1]["position"] = 0

        report.equity_curve = equity_curve
        report.trades = trades
        report.metrics = compute_performance_metrics(
            equity_curve, trades, cfg.initial_equity, since_ms, until_ms, cfg.leverage
        )
        total_fees = sum(t.fee for t in trades)
        report.metrics["total_fees"] = round(total_fees, 2)
        report.metrics["fee_rate_pct"] = cfg.fee_rate_pct
        report.metrics["slippage_pct"] = cfg.slippage_pct
        return report
