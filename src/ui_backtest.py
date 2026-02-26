# 回測結果渲染共用邏輯
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from io import BytesIO
from typing import Any

from src.backtest import BacktestResult
from src.backtest.engine import _run_backtest_on_rows
from src.backtest import strategies as backtest_strategies
from src.config import STRATEGY_LABELS, STRATEGY_COLORS
from src.chart_theme import apply_dark_theme

ALL_STRATEGIES = list(backtest_strategies.STRATEGY_CONFIG.keys())


def run_all_strategies(rows, exchange_id, symbol, timeframe, since_ms, until_ms,
                       initial_equity, leverage, take_profit_pct, stop_loss_pct,
                       fee_rate, slippage, custom_params=None):
    """對所有策略執行回測"""
    results = {}
    for strategy in ALL_STRATEGIES:
        params = (custom_params or {}).get(strategy) or \
                 (backtest_strategies.STRATEGY_CONFIG.get(strategy, {}).get("defaults") or {}).copy()
        res = _run_backtest_on_rows(
            rows=rows, exchange_id=exchange_id, symbol=symbol, timeframe=timeframe,
            since_ms=since_ms, until_ms=until_ms, strategy=strategy, strategy_params=params,
            initial_equity=initial_equity, leverage=leverage,
            take_profit_pct=take_profit_pct or None, stop_loss_pct=stop_loss_pct or None,
            fee_rate=fee_rate, slippage=slippage,
        )
        results[strategy] = res
    return results


def render_summary_line(results: dict[str, BacktestResult]):
    """渲染一行式回測摘要"""
    valid = {s: r for s, r in results.items() if not r.error}
    if not valid:
        st.warning("所有策略均回測失敗")
        return None, valid
    best = max(valid.items(), key=lambda x: x[1].metrics.get("total_return_pct", -999))
    bm = best[1].metrics
    _ret = bm.get("total_return_pct", 0)
    _fee_total = sum(r.metrics.get("total_fees", 0) for r in valid.values())
    _icon = "🟢" if _ret > 0 else "🔴"
    st.markdown(
        f"#### {_icon} 最佳：**{STRATEGY_LABELS.get(best[0], best[0])}**　"
        f"淨報酬 **{_ret:+.2f}%**　|　夏普 {bm.get('sharpe_ratio', 0)}　|　"
        f"回撤 {bm.get('max_drawdown_pct', 0)}%　|　{bm.get('num_trades', 0)} 筆　|　"
        f"手續費 ${_fee_total:,.0f}")
    return best, valid


def render_kline_chart(ohlcv_rows, best_strategy_result=None):
    """渲染 K 線圖"""
    real_bars = [r for r in ohlcv_rows if not r.get("filled")]
    if not real_bars:
        return
    df_k = pd.DataFrame(real_bars)
    df_k["time"] = pd.to_datetime(df_k["timestamp"], unit="ms", utc=True)
    fig_k = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
    fig_k.add_trace(go.Candlestick(
        x=df_k["time"], open=df_k["open"], high=df_k["high"], low=df_k["low"], close=df_k["close"],
        name="K 線", increasing_line_color="#26A69A", decreasing_line_color="#EF5350",
    ), row=1, col=1)
    fig_k.add_trace(go.Bar(x=df_k["time"], y=df_k["volume"], name="成交量",
                            marker_color="rgba(100,149,237,0.4)"), row=2, col=1)
    if best_strategy_result and best_strategy_result[1].trades:
        for t in best_strategy_result[1].trades:
            entry_t = pd.to_datetime(t["entry_ts"], unit="ms", utc=True)
            exit_t = pd.to_datetime(t["exit_ts"], unit="ms", utc=True)
            side_label = "多" if t["side"] == 1 else "空"
            fig_k.add_trace(go.Scatter(
                x=[entry_t], y=[t["entry_price"]], mode="markers",
                marker=dict(symbol="triangle-up" if t["side"] == 1 else "triangle-down",
                            size=10, color="#26A69A" if t["side"] == 1 else "#EF5350"),
                name=f"進場({side_label})", showlegend=False,
            ), row=1, col=1)
    fig_k.update_layout(height=450, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
    fig_k.update_yaxes(title_text="價格", row=1, col=1)
    fig_k.update_yaxes(title_text="量", row=2, col=1)
    st.plotly_chart(apply_dark_theme(fig_k), use_container_width=True)


def render_equity_curves(results: dict[str, BacktestResult], initial_equity: float):
    """渲染權益曲線"""
    fig_eq = go.Figure()
    for strategy in ALL_STRATEGIES:
        if strategy not in results:
            continue
        res = results[strategy]
        if res.error or not res.equity_curve:
            continue
        curve = res.equity_curve
        idx = pd.to_datetime([e["timestamp"] for e in curve], unit="ms", utc=True)
        eq = [e["equity"] for e in curve]
        label = STRATEGY_LABELS.get(strategy, strategy)
        color = STRATEGY_COLORS.get(strategy, "#888")
        fig_eq.add_trace(go.Scatter(x=idx, y=eq, mode="lines", name=label, line=dict(color=color, width=2)))
    fig_eq.add_hline(y=initial_equity, line_dash="dash", line_color="gray", annotation_text="初始資金")
    fig_eq.update_layout(height=380, margin=dict(l=0, r=0, t=30, b=0), yaxis_title="權益", hovermode="x unified",
                         legend=dict(orientation="h", y=1.05))
    st.plotly_chart(apply_dark_theme(fig_eq), use_container_width=True)


def render_performance_table(results: dict[str, BacktestResult]):
    """渲染績效彙總表"""
    def _hl(val):
        try:
            v = float(val)
            return "color:#0d7a0d;font-weight:bold" if v > 0 else "color:#c00;font-weight:bold" if v < 0 else ""
        except (TypeError, ValueError):
            return ""

    rows = []
    for strategy, res in results.items():
        if res.error:
            rows.append({"策略": STRATEGY_LABELS.get(strategy, strategy), "報酬%": "-", "備註": res.error})
        else:
            m = res.metrics
            rows.append({
                "策略": STRATEGY_LABELS.get(strategy, strategy),
                "報酬%": m.get("total_return_pct"), "年化%": m.get("annual_return_pct"),
                "回撤%": m.get("max_drawdown_pct"), "夏普": m.get("sharpe_ratio"),
                "Sortino": m.get("sortino_ratio"), "PF": m.get("profit_factor"),
                "交易": m.get("num_trades"), "勝率%": m.get("win_rate_pct"),
                "手續費": m.get("total_fees", 0), "備註": "",
            })
    df = pd.DataFrame(rows)
    hl_cols = [c for c in ["報酬%", "年化%", "夏普", "Sortino"] if c in df.columns]
    if hl_cols:
        st.dataframe(df.style.map(_hl, subset=hl_cols), use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
    csv = BytesIO()
    df.to_csv(csv, index=False, encoding="utf-8-sig")
    st.download_button("📥 下載績效 CSV", csv.getvalue(), "performance.csv", "text/csv")


def render_trade_details(results: dict[str, BacktestResult]):
    """渲染交易明細"""
    for strategy in ALL_STRATEGIES:
        if strategy not in results:
            continue
        res = results[strategy]
        label = STRATEGY_LABELS.get(strategy, strategy)
        if res.error or not res.trades:
            continue
        st.markdown(f"**{label}**")
        df = pd.DataFrame(res.trades)
        df["序號"] = range(1, len(df) + 1)
        df["進場"] = pd.to_datetime(df["entry_ts"], unit="ms", utc=True).dt.strftime("%m/%d %H:%M")
        df["出場"] = pd.to_datetime(df["exit_ts"], unit="ms", utc=True).dt.strftime("%m/%d %H:%M")
        df["方向"] = df["side"].map({1: "🟢多", -1: "🔴空"})
        show = ["序號", "進場", "出場", "方向", "entry_price", "exit_price", "pnl_pct", "fee", "profit"]
        show = [c for c in show if c in df.columns]
        disp = df[show].rename(columns={"entry_price": "進場價", "exit_price": "出場價",
                                         "pnl_pct": "報酬%", "fee": "手續費", "profit": "淨利潤"})
        st.dataframe(disp, use_container_width=True, hide_index=True)
