#!/usr/bin/env python3
"""
StocksX V0 — 周度回測引擎
每週自動回測所有策略，使用真實市場數據，結果提交到 GitHub。

用法: python scripts/weekly_backtest.py [--symbols BTC,ETH,AAPL] [--period 1y]
"""

import sys
import os
import json
import time
import argparse
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
import importlib.util
import types

import numpy as np
import pandas as pd
import yfinance as yf

# ── 添加項目路徑 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── 使用 importlib 直接加載，避免 __init__.py 循環依賴 ──
def _load_module(name: str, filepath: str):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_strategies_mod = _load_module("strategies", str(PROJECT_ROOT / "src/backtest/strategies.py"))

sma_cross = _strategies_mod.sma_cross
ema_cross = _strategies_mod.ema_cross
buy_and_hold = _strategies_mod.buy_and_hold
rsi_signal = _strategies_mod.rsi_signal
macd_cross = _strategies_mod.macd_cross
bollinger_signal = _strategies_mod.bollinger_signal
donchian_channel = _strategies_mod.donchian_channel
supertrend = _strategies_mod.supertrend
dual_thrust = _strategies_mod.dual_thrust
vwap_reversion = _strategies_mod.vwap_reversion
ichimoku = _strategies_mod.ichimoku
stochastic = _strategies_mod.stochastic
williams_r = _strategies_mod.williams_r
adx_trend = _strategies_mod.adx_trend
parabolic_sar = _strategies_mod.parabolic_sar
mean_reversion_zscore = _strategies_mod.mean_reversion_zscore
momentum_roc = _strategies_mod.momentum_roc
keltner_channel = _strategies_mod.keltner_channel


# ════════════════════════════════════════════════════════════
# 獨立回測引擎（避免 import 依賴）
# ════════════════════════════════════════════════════════════

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_equity: float = 10_000.0
    leverage: float = 1.0
    fee_rate_pct: float = 0.1
    slippage_pct: float = 0.05
    take_profit_pct: float | None = 10.0
    stop_loss_pct: float | None = 5.0


@dataclass(slots=True)
class TradeRecord:
    entry_ts: int
    exit_ts: int
    side: int
    entry_price: float
    exit_price: float
    pnl_pct: float
    profit: float
    fee: float
    liquidation: bool = False
    exit_reason: str = "signal"

    def to_dict(self) -> dict:
        return {
            "entry_ts": self.entry_ts, "exit_ts": self.exit_ts, "side": self.side,
            "entry_price": self.entry_price, "exit_price": self.exit_price,
            "pnl_pct": round(self.pnl_pct, 4), "profit": round(self.profit, 2),
            "fee": round(self.fee, 2), "liquidation": self.liquidation,
            "exit_reason": self.exit_reason,
        }


def compute_performance_metrics(equity_curve, trades, initial_equity, since_ms, until_ms, leverage=1.0):
    if not equity_curve:
        return {}
    equity = equity_curve[-1]["equity"]
    total_return = (equity - initial_equity) / initial_equity if initial_equity else 0
    equities = [e["equity"] for e in equity_curve]

    peak = equities[0]
    max_dd = 0.0
    for e in equities:
        if e > peak: peak = e
        dd = (peak - e) / peak if peak else 0
        if dd > max_dd: max_dd = dd

    period_years = (until_ms - since_ms) / (1000 * 86400 * 365.25) if since_ms < until_ms else 0
    if period_years <= 0 or (1 + total_return) <= 0:
        annual_return = 0.0
    else:
        try:
            exponent = 1 / period_years
            if exponent > 100:
                annual_return = total_return / period_years
            else:
                ar = (1 + total_return) ** exponent - 1
                annual_return = float(ar.real) if isinstance(ar, complex) else ar
        except (ValueError, ZeroDivisionError, OverflowError):
            annual_return = 0.0

    bar_returns = []
    for j in range(1, len(equities)):
        r = (equities[j] - equities[j-1]) / equities[j-1] if equities[j-1] else 0
        bar_returns.append(r)

    if bar_returns:
        mean_r = sum(bar_returns) / len(bar_returns)
        var_r = sum((x - mean_r)**2 for x in bar_returns) / len(bar_returns)
        std_r = math.sqrt(var_r) if var_r > 0 else 0
        sharpe = (mean_r / std_r * math.sqrt(252)) if std_r else 0.0
        neg_returns = [x for x in bar_returns if x < 0]
        std_neg = math.sqrt(sum(x*x for x in neg_returns) / len(neg_returns)) if neg_returns else 0
        sortino = (mean_r / std_neg * math.sqrt(252)) if std_neg else 0.0
        calmar = (annual_return / max_dd) if max_dd > 0 else 0.0
    else:
        sharpe = sortino = calmar = 0.0

    win_trades = [t for t in trades if t.pnl_pct > 0]
    loss_trades = [t for t in trades if t.pnl_pct < 0]
    gross_profit = sum(t.profit for t in win_trades)
    gross_loss = abs(sum(t.profit for t in loss_trades))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0.0

    pos_returns = [r for r in bar_returns if r > 0] if bar_returns else []
    neg_abs = [abs(r) for r in bar_returns if r < 0] if bar_returns else []
    omega = round(sum(pos_returns) / sum(neg_abs), 2) if neg_abs and sum(neg_abs) > 0 else 0.0

    return {
        "leverage": leverage, "initial_equity": initial_equity,
        "final_equity": round(equity, 2), "total_return_pct": round(total_return * 100, 2),
        "annual_return_pct": round(annual_return * 100, 2), "max_drawdown_pct": round(max_dd * 100, 2),
        "sharpe_ratio": round(sharpe, 2), "sortino_ratio": round(sortino, 2),
        "calmar_ratio": round(calmar, 2), "profit_factor": profit_factor, "omega_ratio": omega,
        "num_trades": len(trades),
        "win_rate_pct": round(100 * len(win_trades) / len(trades), 1) if trades else 0,
        "avg_win": round(sum(t.profit for t in win_trades) / len(win_trades), 2) if win_trades else 0,
        "avg_loss": round(sum(t.profit for t in loss_trades) / len(loss_trades), 2) if loss_trades else 0,
        "period_bars": len(equity_curve),
    }


class BacktestEngine:
    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()

    def _close_position(self, position, entry_price, exit_price, equity, entry_ts, exit_ts, exit_reason="signal"):
        cfg = self.config
        cost_pct = (cfg.fee_rate_pct + cfg.slippage_pct) / 100
        price_return = (exit_price - entry_price) / entry_price * position
        rt_cost = cost_pct * 2
        pnl_pct = price_return * cfg.leverage - rt_cost
        fee_amount = equity * rt_cost
        equity_before = equity
        equity *= 1 + pnl_pct
        profit = equity_before * pnl_pct
        liquidated = equity <= 0
        if liquidated:
            equity = 0.0; profit = -equity_before; pnl_pct = -1.0
        trade = TradeRecord(
            entry_ts=int(entry_ts), exit_ts=int(exit_ts), side=position,
            entry_price=entry_price, exit_price=exit_price,
            pnl_pct=pnl_pct * 100, profit=profit, fee=fee_amount,
            liquidation=liquidated, exit_reason=exit_reason,
        )
        return equity, trade

    def run(self, rows, signals, since_ms, until_ms):
        cfg = self.config
        equity = cfg.initial_equity
        position = 0; entry_price = 0.0; entry_ts = since_ms
        equity_curve = []; trades = []; liquidated = False

        for i, r in enumerate(rows):
            ts = r["timestamp"]; h = r["high"]; l = r["low"]; close = r["close"]
            target = signals[i] if i < len(signals) else 0

            if liquidated:
                equity_curve.append({"timestamp": ts, "equity": 0.0, "position": 0}); continue

            # TP/SL
            if position != 0 and entry_price and (cfg.take_profit_pct or cfg.stop_loss_pct):
                tp_price = sl_price = None
                if cfg.take_profit_pct and cfg.take_profit_pct > 0:
                    tp_price = entry_price * (1 + cfg.take_profit_pct/100) if position == 1 else entry_price * (1 - cfg.take_profit_pct/100)
                if cfg.stop_loss_pct and cfg.stop_loss_pct > 0:
                    sl_price = entry_price * (1 - cfg.stop_loss_pct/100) if position == 1 else entry_price * (1 + cfg.stop_loss_pct/100)
                touched_sl = sl_price is not None and l <= sl_price <= h
                touched_tp = tp_price is not None and l <= tp_price <= h
                exit_price = exit_reason = None
                if touched_sl: exit_price = sl_price; exit_reason = "sl"
                elif touched_tp: exit_price = tp_price; exit_reason = "tp"
                if exit_price is not None:
                    equity, trade = self._close_position(position, entry_price, exit_price, equity, entry_ts, ts, exit_reason)
                    trades.append(trade); liquidated = trade.liquidation
                    position = 0; entry_price = 0.0
                    equity_curve.append({"timestamp": ts, "equity": round(equity, 2), "position": 0}); continue

            # Signal close
            if position != 0 and target != position and entry_price:
                equity, trade = self._close_position(position, entry_price, close, equity, entry_ts, ts, "signal")
                trades.append(trade); liquidated = trade.liquidation
                position = 0; entry_price = 0.0

            # Open
            if not liquidated and target != 0 and position == 0:
                position = target; entry_price = close; entry_ts = ts

            # Mark-to-market
            if position != 0 and entry_price:
                unrealized = (close - entry_price) / entry_price * position * cfg.leverage
                mtm_equity = equity * (1 + unrealized)
            else:
                mtm_equity = equity
            equity_curve.append({"timestamp": ts, "equity": round(mtm_equity, 2), "position": position})

        # Force close at end
        if not liquidated and position != 0 and entry_price and rows:
            last_close = rows[-1]["close"]
            equity, trade = self._close_position(position, entry_price, last_close, equity, entry_ts, rows[-1]["timestamp"], "end")
            trades.append(trade)
            if equity_curve:
                equity_curve[-1]["equity"] = round(equity, 2); equity_curve[-1]["position"] = 0

        metrics = compute_performance_metrics(equity_curve, trades, cfg.initial_equity, since_ms, until_ms, cfg.leverage)
        total_fees = sum(t.fee for t in trades)
        metrics["total_fees"] = round(total_fees, 2)
        return type("R", (), {"equity_curve": equity_curve, "trades": trades, "metrics": metrics, "error": None})()


# ════════════════════════════════════════════════════════════
# 策略分類目錄
# ════════════════════════════════════════════════════════════

STRATEGY_CATEGORIES = {
    "趨勢跟隨與動量": {
        "sma_cross": {"fn": sma_cross, "kwargs": {}},
        "ema_cross": {"fn": ema_cross, "kwargs": {}},
        "macd_cross": {"fn": macd_cross, "kwargs": {}},
        "adx_trend": {"fn": adx_trend, "kwargs": {}},
        "supertrend": {"fn": supertrend, "kwargs": {}},
        "parabolic_sar": {"fn": parabolic_sar, "kwargs": {}},
        "keltner_channel": {"fn": keltner_channel, "kwargs": {}},
        "momentum_roc": {"fn": momentum_roc, "kwargs": {}},
    },
    "超買超賣振盪": {
        "rsi_signal": {"fn": rsi_signal, "kwargs": {}},
        "stochastic": {"fn": stochastic, "kwargs": {}},
        "williams_r": {"fn": williams_r, "kwargs": {}},
        "bollinger_signal": {"fn": bollinger_signal, "kwargs": {}},
        "ichimoku": {"fn": ichimoku, "kwargs": {}},
    },
    "突破與均值回歸": {
        "donchian_channel": {"fn": donchian_channel, "kwargs": {}},
        "dual_thrust": {"fn": dual_thrust, "kwargs": {}},
        "vwap_reversion": {"fn": vwap_reversion, "kwargs": {}},
        "mean_reversion_zscore": {"fn": mean_reversion_zscore, "kwargs": {}},
    },
    "基準": {
        "buy_and_hold": {"fn": buy_and_hold, "kwargs": {}},
    },
}

# ── 預設回測標的 ──
DEFAULT_SYMBOLS = [
    "BTC-USD",    # 比特幣
    "ETH-USD",    # 以太幣
    "AAPL",       # Apple
    "TSLA",       # Tesla
    "SPY",        # S&P 500 ETF
    "QQQ",        # Nasdaq 100 ETF
    "TSM",        # 台積電 ADR
]


# ════════════════════════════════════════════════════════════
# 數據下載
# ════════════════════════════════════════════════════════════

def fetch_market_data(symbol: str, period: str = "1y") -> list[dict] | None:
    """從 Yahoo Finance 下載 OHLCV 數據，轉為引擎格式。"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval="1d")
        if df.empty or len(df) < 30:
            print(f"  ⚠️ {symbol}: 數據不足 ({len(df)} 條)，跳過")
            return None

        rows = []
        for idx, row in df.iterrows():
            ts = int(idx.timestamp() * 1000)
            rows.append({
                "timestamp": ts,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row.get("Volume", 0)),
            })
        return rows
    except Exception as e:
        print(f"  ❌ {symbol}: 下載失敗 — {e}")
        return None


# ════════════════════════════════════════════════════════════
# 回測執行
# ════════════════════════════════════════════════════════════

def run_single_backtest(
    rows: list[dict],
    strategy_fn,
    strategy_kwargs: dict,
    config: BacktestConfig | None = None,
) -> dict:
    """對一個策略執行一次完整回測。"""
    config = config or BacktestConfig(
        initial_equity=10_000.0,
        fee_rate_pct=0.1,
        slippage_pct=0.05,
        stop_loss_pct=5.0,
        take_profit_pct=10.0,
    )
    engine = BacktestEngine(config=config)

    signals = strategy_fn(rows, **strategy_kwargs)
    since_ms = rows[0]["timestamp"]
    until_ms = rows[-1]["timestamp"]

    report = engine.run(rows, signals, since_ms, until_ms)
    return report.metrics if report.metrics else {"error": report.error or "未知錯誤"}


def run_all_backtests(symbols: list[str], period: str = "1y") -> dict:
    """對所有策略 × 所有標的執行回測。"""
    all_results = {}
    total = sum(len(strats) for strats in STRATEGY_CATEGORIES.values())
    total_runs = len(symbols) * total
    run_count = 0

    print(f"\n{'='*60}")
    print(f"📊 StocksX 週度回測 — {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')} CST")
    print(f"{'='*60}")
    print(f"📌 標的: {', '.join(symbols)}")
    print(f"📌 策略數: {total} | 回測總數: {total_runs}")
    print(f"📌 回測週期: {period}")
    print(f"{'='*60}\n")

    for symbol in symbols:
        print(f"📥 下載 {symbol} 數據...")
        rows = fetch_market_data(symbol, period)
        if rows is None:
            continue

        print(f"  ✅ {len(rows)} 條 K 線\nn")
        symbol_results = {}

        for category, strategies in STRATEGY_CATEGORIES.items():
            print(f"  📂 {category}")
            category_results = {}

            for strat_name, strat_info in strategies.items():
                run_count += 1
                try:
                    start = time.time()
                    metrics = run_single_backtest(
                        rows,
                        strat_info["fn"],
                        strat_info["kwargs"],
                    )
                    elapsed = time.time() - start
                    metrics["backtest_seconds"] = round(elapsed, 3)
                    category_results[strat_name] = metrics

                    ret = metrics.get("total_return_pct", 0)
                    sharpe = metrics.get("sharpe_ratio", 0)
                    dd = metrics.get("max_drawdown_pct", 0)
                    wr = metrics.get("win_rate_pct", 0)
                    emoji = "🟢" if ret > 0 else "🔴"
                    print(f"    {emoji} {strat_name:25s} | 收益: {ret:+7.2f}% | Sharpe: {sharpe:+6.2f} | 最大回撤: {dd:6.2f}% | 勝率: {wr:5.1f}%")

                except Exception as e:
                    category_results[strat_name] = {"error": str(e)}
                    print(f"    ❌ {strat_name:25s} | 錯誤: {e}")

            symbol_results[category] = category_results

        all_results[symbol] = symbol_results
        print()

    return all_results


# ════════════════════════════════════════════════════════════
# 報告生成
# ════════════════════════════════════════════════════════════

def generate_report(results: dict, output_dir: Path) -> tuple[Path, Path]:
    """生成 JSON + Markdown 報告。"""
    now = datetime.now(timezone(timedelta(hours=8)))
    date_str = now.strftime("%Y-%m-%d")
    ts_str = now.strftime("%Y-%m-%d_%H%M")

    # ── JSON 報告 ──
    json_path = output_dir / f"weekly_backtest_{ts_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": now.isoformat(),
            "results": results,
        }, f, ensure_ascii=False, indent=2)

    # ── Markdown 報告 ──
    md_path = output_dir / f"weekly_backtest_{ts_str}.md"
    lines = [
        f"# 📊 StocksX 週度回測報告",
        f"",
        f"**生成時間**: {now.strftime('%Y-%m-%d %H:%M:%S')} CST",
        f"",
        "---",
        "",
    ]

    # 摘要表
    lines.append("## 🏆 策略排名 (按 Sharpe Ratio)")
    lines.append("")

    all_strategies = []
    for symbol, cats in results.items():
        for cat_name, strats in cats.items():
            for strat_name, metrics in strats.items():
                if isinstance(metrics, dict) and "sharpe_ratio" in metrics:
                    all_strategies.append({
                        "symbol": symbol,
                        "category": cat_name,
                        "strategy": strat_name,
                        "total_return_pct": metrics.get("total_return_pct", 0),
                        "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                        "max_drawdown_pct": metrics.get("max_drawdown_pct", 0),
                        "win_rate_pct": metrics.get("win_rate_pct", 0),
                        "num_trades": metrics.get("num_trades", 0),
                        "profit_factor": metrics.get("profit_factor", 0),
                    })

    all_strategies.sort(key=lambda x: x["sharpe_ratio"], reverse=True)

    lines.append("| # | 標的 | 策略 | 收益% | Sharpe | 最大回撤% | 勝率% | 交易數 | 利潤因子 |")
    lines.append("|---|------|------|-------|--------|-----------|-------|--------|----------|")
    for i, s in enumerate(all_strategies[:20], 1):
        lines.append(
            f"| {i} | {s['symbol']} | {s['strategy']} | "
            f"{s['total_return_pct']:+.2f} | {s['sharpe_ratio']:+.2f} | "
            f"{s['max_drawdown_pct']:.2f} | {s['win_rate_pct']:.1f} | "
            f"{s['num_trades']} | {s['profit_factor']:.2f} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # 按標的詳細
    for symbol, cats in results.items():
        lines.append(f"## {symbol}")
        lines.append("")
        for cat_name, strats in cats.items():
            lines.append(f"### {cat_name}")
            lines.append("")
            lines.append("| 策略 | 收益% | Sharpe | Sortino | Calmar | 最大回撤% | 勝率% | 交易數 | 利潤因子 |")
            lines.append("|------|-------|--------|---------|--------|-----------|-------|--------|----------|")
            for strat_name, metrics in strats.items():
                if isinstance(metrics, dict) and "total_return_pct" in metrics:
                    lines.append(
                        f"| {strat_name} | "
                        f"{metrics.get('total_return_pct', 0):+.2f} | "
                        f"{metrics.get('sharpe_ratio', 0):+.2f} | "
                        f"{metrics.get('sortino_ratio', 0):+.2f} | "
                        f"{metrics.get('calmar_ratio', 0):+.2f} | "
                        f"{metrics.get('max_drawdown_pct', 0):.2f} | "
                        f"{metrics.get('win_rate_pct', 0):.1f} | "
                        f"{metrics.get('num_trades', 0)} | "
                        f"{metrics.get('profit_factor', 0):.2f} |"
                    )
                else:
                    err = metrics.get("error", "未知") if isinstance(metrics, dict) else str(metrics)
                    lines.append(f"| {strat_name} | ❌ {err} | | | | | | |")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*報告由 StocksX V0 週度回測引擎自動生成*")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ── 最新報告連結 (latest) ──
    latest_json = output_dir / "latest_backtest.json"
    latest_md = output_dir / "latest_backtest.md"
    import shutil
    shutil.copy2(json_path, latest_json)
    shutil.copy2(md_path, latest_md)

    return json_path, md_path


# ════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="StocksX 週度回測")
    parser.add_argument("--symbols", type=str, default=",".join(DEFAULT_SYMBOLS),
                        help="回測標的，逗號分隔")
    parser.add_argument("--period", type=str, default="1y",
                        help="歷史數據週期 (1mo, 3mo, 6mo, 1y, 2y, 5y)")
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "backtest_reports"),
                        help="報告輸出目錄")
    parser.add_argument("--commit", action="store_true", default=True,
                        help="自動提交結果到 Git")
    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 執行回測
    results = run_all_backtests(symbols, args.period)

    # 生成報告
    json_path, md_path = generate_report(results, output_dir)
    print(f"\n📄 報告已生成:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")

    # Git 提交
    if args.commit:
        try:
            os.chdir(PROJECT_ROOT)
            os.system(f'git add backtest_reports/')
            now = datetime.now(timezone(timedelta(hours=8)))
            msg = f"📊 Weekly backtest report — {now.strftime('%Y-%m-%d')}"
            os.system(f'git commit -m "{msg}" --allow-empty')
            os.system(f'git push origin main 2>&1')
            print(f"\n✅ 已提交並推送至 GitHub")
        except Exception as e:
            print(f"\n⚠️ Git 提交失敗: {e}")

    # 摘要
    print(f"\n{'='*60}")
    print(f"📊 回測完成摘要")
    print(f"{'='*60}")
    for symbol, cats in results.items():
        best_strat = None
        best_sharpe = -999
        for cat_name, strats in cats.items():
            for strat_name, metrics in strats.items():
                if isinstance(metrics, dict) and "sharpe_ratio" in metrics:
                    if metrics["sharpe_ratio"] > best_sharpe:
                        best_sharpe = metrics["sharpe_ratio"]
                        best_strat = (strat_name, metrics)
        if best_strat:
            print(f"  {symbol:10s} → 最佳: {best_strat[0]} (Sharpe: {best_strat[1]['sharpe_ratio']:+.2f}, 收益: {best_strat[1]['total_return_pct']:+.2f}%)")

    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
