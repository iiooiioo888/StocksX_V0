# 回測結果渲染 — 專業級圖表
from __future__ import annotations

from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.backtest import BacktestResult
from src.backtest import strategies as backtest_strategies
from src.backtest.engine import _run_backtest_on_rows
from src.chart_theme import apply_dark_theme
from src.config import STRATEGY_COLORS, STRATEGY_LABELS

ALL_STRATEGIES = list(backtest_strategies.STRATEGY_CONFIG.keys())

# 專業配色
_UP = "#26A69A"
_DOWN = "#EF5350"
_GRID = "rgba(50,50,90,0.2)"
_VOL_UP = "rgba(38,166,154,0.35)"
_VOL_DOWN = "rgba(239,83,80,0.35)"


def run_all_strategies(
    rows,
    exchange_id,
    symbol,
    timeframe,
    since_ms,
    until_ms,
    initial_equity,
    leverage,
    take_profit_pct,
    stop_loss_pct,
    fee_rate,
    slippage,
    custom_params=None,
):
    """對所有策略執行回測"""
    results = {}
    for strategy in ALL_STRATEGIES:
        params = (custom_params or {}).get(strategy) or (
            backtest_strategies.STRATEGY_CONFIG.get(strategy, {}).get("defaults") or {}
        ).copy()
        res = _run_backtest_on_rows(
            rows=rows,
            exchange_id=exchange_id,
            symbol=symbol,
            timeframe=timeframe,
            since_ms=since_ms,
            until_ms=until_ms,
            strategy=strategy,
            strategy_params=params,
            initial_equity=initial_equity,
            leverage=leverage,
            take_profit_pct=take_profit_pct or None,
            stop_loss_pct=stop_loss_pct or None,
            fee_rate=fee_rate,
            slippage=slippage,
        )
        results[strategy] = res
    return results


def render_summary_line(results: dict[str, BacktestResult]):
    """渲染回測摘要"""
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
        f"手續費 ${_fee_total:,.0f}"
    )
    return best, valid


def render_kline_chart(ohlcv_rows, best_strategy_result=None):
    """專業 K 線圖：漲跌色成交量 + MA + 買賣標記"""
    real_bars = [r for r in ohlcv_rows if not r.get("filled")]
    if not real_bars:
        return
    df = pd.DataFrame(real_bars)
    df["time"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df["color"] = df.apply(lambda r: _VOL_UP if r["close"] >= r["open"] else _VOL_DOWN, axis=1)

    # 計算 MA
    for p in [20, 60]:
        if len(df) >= p:
            df[f"MA{p}"] = df["close"].rolling(p).mean()

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.02,
        subplot_titles=("", "成交量", ""),
    )

    # K 線
    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="",
            increasing=dict(line=dict(color=_UP, width=1), fillcolor=_UP),
            decreasing=dict(line=dict(color=_DOWN, width=1), fillcolor=_DOWN),
            whiskerwidth=0.5,
        ),
        row=1,
        col=1,
    )

    # MA
    for p, color in [(20, "#FFD700"), (60, "#FF69B4")]:
        col = f"MA{p}"
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["time"],
                    y=df[col],
                    mode="lines",
                    name=f"MA{p}",
                    line=dict(color=color, width=1.2, dash="dot"),
                ),
                row=1,
                col=1,
            )

    # 成交量（漲跌色）
    fig.add_trace(
        go.Bar(
            x=df["time"],
            y=df["volume"],
            name="成交量",
            marker_color=df["color"].tolist(),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    # 買賣標記
    if best_strategy_result and best_strategy_result[1].trades:
        entries_long, entries_short, exits = [], [], []
        for t in best_strategy_result[1].trades:
            et = pd.to_datetime(t["entry_ts"], unit="ms", utc=True)
            xt = pd.to_datetime(t["exit_ts"], unit="ms", utc=True)
            if t["side"] == 1:
                entries_long.append((et, t["entry_price"]))
            else:
                entries_short.append((et, t["entry_price"]))
            exits.append((xt, t["exit_price"], t.get("pnl_pct", 0)))

        if entries_long:
            fig.add_trace(
                go.Scatter(
                    x=[e[0] for e in entries_long],
                    y=[e[1] for e in entries_long],
                    mode="markers",
                    name="做多進場",
                    showlegend=True,
                    marker=dict(symbol="triangle-up", size=11, color=_UP, line=dict(width=1, color="white")),
                    hovertemplate="做多進場<br>%{y:,.2f}<extra></extra>",
                ),
                row=1,
                col=1,
            )
        if entries_short:
            fig.add_trace(
                go.Scatter(
                    x=[e[0] for e in entries_short],
                    y=[e[1] for e in entries_short],
                    mode="markers",
                    name="做空進場",
                    showlegend=True,
                    marker=dict(symbol="triangle-down", size=11, color=_DOWN, line=dict(width=1, color="white")),
                    hovertemplate="做空進場<br>%{y:,.2f}<extra></extra>",
                ),
                row=1,
                col=1,
            )
        if exits:
            fig.add_trace(
                go.Scatter(
                    x=[e[0] for e in exits],
                    y=[e[1] for e in exits],
                    mode="markers",
                    name="出場",
                    showlegend=True,
                    marker=dict(symbol="x", size=8, color="#FFB74D", line=dict(width=1.5, color="#FFB74D")),
                    hovertemplate="出場 %{y:,.2f}<extra></extra>",
                ),
                row=1,
                col=1,
            )

    # RSI 副圖（簡化）
    if len(df) > 14:
        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        fig.add_trace(
            go.Scatter(x=df["time"], y=rsi, mode="lines", name="RSI(14)", line=dict(color="#7B68EE", width=1.2)),
            row=3,
            col=1,
        )
        fig.add_hline(y=70, line=dict(color="rgba(239,83,80,0.3)", width=1, dash="dash"), row=3, col=1)
        fig.add_hline(y=30, line=dict(color="rgba(38,166,154,0.3)", width=1, dash="dash"), row=3, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)

    # 鎖定 X 軸範圍到實際數據區間，避免被標記拉開
    _t_min = df["time"].min()
    _t_max = df["time"].max()
    fig.update_xaxes(range=[_t_min, _t_max])

    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, x=0, xanchor="left"),
        annotations=[dict(text="", showarrow=False)] * 3,
    )
    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text="", row=2, col=1)
    st.plotly_chart(apply_dark_theme(fig), use_container_width=True)


def render_equity_curves(results: dict[str, BacktestResult], initial_equity: float):
    """專業權益曲線 + 回撤副圖"""
    curves = [(s, r) for s, r in results.items() if r.equity_curve and not r.error]
    if not curves:
        return

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)

    for strategy, res in curves:
        curve = res.equity_curve
        idx = pd.to_datetime([e["timestamp"] for e in curve], unit="ms", utc=True)
        eq = [e["equity"] for e in curve]
        label = STRATEGY_LABELS.get(strategy, strategy)
        color = STRATEGY_COLORS.get(strategy, "#888")

        fig.add_trace(
            go.Scatter(
                x=idx,
                y=eq,
                mode="lines",
                name=label,
                line=dict(color=color, width=2),
                hovertemplate=f"{label}: $%{{y:,.0f}}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # 回撤
        peak = eq[0]
        dd = []
        for e in eq:
            if e > peak:
                peak = e
            dd.append(-(peak - e) / peak * 100 if peak else 0)
        fig.add_trace(
            go.Scatter(
                x=idx,
                y=dd,
                mode="lines",
                name=f"{label} DD",
                showlegend=False,
                line=dict(color=color, width=1),
                fill="tozeroy",
                fillcolor="rgba(100,100,150,0.08)",
            ),
            row=2,
            col=1,
        )

    fig.add_hline(
        y=initial_equity,
        line=dict(color="rgba(150,150,200,0.4)", width=1, dash="dash"),
        annotation_text="初始資金",
        annotation_font_color="#9090b0",
        row=1,
        col=1,
    )

    fig.update_layout(
        height=500,
        legend=dict(orientation="h", y=1.02, x=0, xanchor="left"),
    )
    fig.update_yaxes(title_text="權益", row=1, col=1)
    fig.update_yaxes(title_text="回撤%", row=2, col=1)

    # 修復回撤 fillcolor
    for trace in fig.data:
        if hasattr(trace, "fillcolor") and trace.fillcolor and "rgba" not in str(trace.fillcolor):
            trace.fillcolor = "rgba(100,100,150,0.08)"

    st.plotly_chart(apply_dark_theme(fig), use_container_width=True)


def render_performance_table(results: dict[str, BacktestResult]):
    """渲染績效彙總表"""

    def _hl(val):
        try:
            v = float(val)
            return "color:#26A69A;font-weight:bold" if v > 0 else "color:#EF5350;font-weight:bold" if v < 0 else ""
        except (TypeError, ValueError):
            return ""

    rows = []
    for strategy, res in results.items():
        if res.error:
            rows.append({"策略": STRATEGY_LABELS.get(strategy, strategy), "報酬%": "-", "備註": res.error})
        else:
            m = res.metrics
            rows.append(
                {
                    "策略": STRATEGY_LABELS.get(strategy, strategy),
                    "報酬%": m.get("total_return_pct"),
                    "年化%": m.get("annual_return_pct"),
                    "回撤%": m.get("max_drawdown_pct"),
                    "夏普": m.get("sharpe_ratio"),
                    "Sortino": m.get("sortino_ratio"),
                    "PF": m.get("profit_factor"),
                    "Omega": m.get("omega_ratio"),
                    "勝率%": m.get("win_rate_pct"),
                    "交易": m.get("num_trades"),
                    "連虧": m.get("max_consec_loss"),
                    "手續費": m.get("total_fees", 0),
                    "備註": "",
                }
            )
    df = pd.DataFrame(rows)
    hl_cols = [c for c in ["報酬%", "年化%", "夏普", "Sortino", "PF", "Omega"] if c in df.columns]
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
        disp = df[show].rename(
            columns={
                "entry_price": "進場價",
                "exit_price": "出場價",
                "pnl_pct": "報酬%",
                "fee": "手續費",
                "profit": "淨利潤",
            }
        )
        st.dataframe(disp, use_container_width=True, hide_index=True)
