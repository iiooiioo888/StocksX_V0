# 回測頁面與報告 — Streamlit (v2 UI)
"""
啟動方式：在專案根目錄執行
  streamlit run app.py
"""
from datetime import datetime, timezone
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.backtest import BacktestResult, find_optimal, find_optimal_global, run_backtest
from src.backtest.engine import _run_backtest_on_rows
from src.backtest.optimizer import DEFAULT_STRATEGIES_GLOBAL, DEFAULT_TIMEFRAMES_GLOBAL, OBJECTIVES
from src.backtest import strategies as backtest_strategies
from src.data.crypto import CryptoDataFetcher

st.set_page_config(page_title="StocksX — 通用回測", page_icon="📊", layout="wide")

st.markdown("""<style>
[data-testid="stMetric"] {background:#f8f9fb;border:1px solid #e0e3e8;border-radius:10px;padding:12px 16px;}
[data-testid="stMetric"] [data-testid="stMetricValue"] {font-size:1.3rem;}
div[data-testid="stExpander"] {border:1px solid #e0e3e8;border-radius:8px;}
</style>""", unsafe_allow_html=True)


def to_ms(d):
    dt = d if hasattr(d, "tzinfo") and d.tzinfo else d.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


ALL_STRATEGIES = list(backtest_strategies.STRATEGY_CONFIG.keys())
STRATEGY_LABELS = {
    "sma_cross": "雙均線交叉",
    "buy_and_hold": "買入持有",
    "rsi_signal": "RSI",
    "macd_cross": "MACD 交叉",
    "bollinger_signal": "布林帶",
}
STRATEGY_COLORS = {
    "sma_cross": "#636EFA",
    "buy_and_hold": "#00CC96",
    "rsi_signal": "#EF553B",
    "macd_cross": "#AB63FA",
    "bollinger_signal": "#FFA15A",
}

SYMBOL_OPTIONS = [
    "BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT", "SOL/USDT:USDT",
    "XRP/USDT:USDT", "DOGE/USDT:USDT", "ADA/USDT:USDT", "AVAX/USDT:USDT",
    "LINK/USDT:USDT", "DOT/USDT:USDT", "LTC/USDT:USDT", "UNI/USDT:USDT",
    "ATOM/USDT:USDT", "NEAR/USDT:USDT", "APT/USDT:USDT", "ARB/USDT:USDT",
    "OP/USDT:USDT", "SUI/USDT:USDT", "INJ/USDT:USDT", "TIA/USDT:USDT",
    "其他（自填）",
]

# ────────────────────────── 側邊欄 ──────────────────────────
with st.sidebar:
    st.markdown("## 📊 StocksX 回測")

    with st.expander("🔧 基本設定", expanded=True):
        exchange_id = st.selectbox("交易所", ["binance", "bybit", "okx"], index=0)
        symbol_choice = st.selectbox("標的（永續合約）", SYMBOL_OPTIONS, index=0)
        if symbol_choice == "其他（自填）":
            symbol = st.text_input("自訂交易對", value="BTC/USDT:USDT", key="symbol_custom")
        else:
            symbol = symbol_choice
        timeframe = st.selectbox("K 線週期", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3)

    with st.expander("📅 時間範圍", expanded=True):
        today = datetime.now(timezone.utc)
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("開始", value=today.replace(day=max(1, today.day - 30)))
        with col2:
            end = st.date_input("結束", value=today)

    with st.expander("💰 資金與風控", expanded=False):
        initial_equity = st.number_input("初始資金", min_value=100.0, value=10000.0, step=500.0)
        leverage = st.number_input("杠杆倍數", min_value=1.0, value=1.0, step=1.0, max_value=125.0)
        col_tp, col_sl = st.columns(2)
        with col_tp:
            take_profit_pct = st.number_input("止盈 %", min_value=0.0, value=0.0, step=0.5)
        with col_sl:
            stop_loss_pct = st.number_input("止損 %", min_value=0.0, value=0.0, step=0.5)
        exclude_outliers = st.checkbox("排除插針資料", value=False)

    run_btn = st.button("🚀 執行回測", type="primary", use_container_width=True)

    st.divider()

    with st.expander("🏆 最優策略搜尋", expanded=False):
        objective = st.selectbox(
            "優化目標", list(OBJECTIVES.keys()), index=0,
            format_func=lambda x: OBJECTIVES[x][0],
        )
        optimize_btn = st.button("🔍 找出最優策略", type="primary", use_container_width=True)
        st.caption("窮舉 策略 × K線週期 × 參數，找出全局最優。")

since_ms = to_ms(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc))
until_ms = to_ms(datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc))

# ────────────────────────── 執行回測 ──────────────────────────
if run_btn:
    if since_ms >= until_ms:
        st.error("請選擇「開始日期」早於「結束日期」。")
    else:
        with st.spinner("回測中…（拉取數據一次，全部策略共用）"):
            results = {}
            try:
                fetcher = CryptoDataFetcher(exchange_id)
                rows = fetcher.get_ohlcv(symbol, timeframe, since_ms, until_ms, fill_gaps=True, exclude_outliers=exclude_outliers)
            except Exception as e:
                st.error(f"數據拉取失敗：{e}")
                rows = None
            if rows is not None:
                st.session_state["ohlcv_rows"] = rows
                for strategy in ALL_STRATEGIES:
                    params = (backtest_strategies.STRATEGY_CONFIG.get(strategy, {}).get("defaults") or {}).copy()
                    res = _run_backtest_on_rows(
                        rows=rows, exchange_id=exchange_id, symbol=symbol, timeframe=timeframe,
                        since_ms=since_ms, until_ms=until_ms, strategy=strategy, strategy_params=params,
                        initial_equity=initial_equity, leverage=leverage,
                        take_profit_pct=take_profit_pct or None, stop_loss_pct=stop_loss_pct or None,
                    )
                    results[strategy] = res
        st.session_state["backtest_results"] = results
        for key in ("optimal_global_result", "optimal_global_strategy", "optimal_global_timeframe",
                     "optimal_global_params", "optimal_global_table", "optimal_global_objective"):
            st.session_state.pop(key, None)

# ────────────────────────── 最優搜尋 ──────────────────────────
if optimize_btn and since_ms < until_ms:
    st.subheader("🔍 窮舉搜尋中…")
    global_progress = st.progress(0.0, text="0 / ? 組合")
    global_status = st.empty()
    global_detail = st.empty()
    try:
        def on_global_progress(s, tf, done, total, best_so_far, best_params):
            try:
                global_progress.progress(done / total if total else 0, text=f"{done} / {total} 組合")
                global_status.caption(f"當前: {STRATEGY_LABELS.get(s, s)} × {tf}")
                lines = [f"掃描：{done}/{total}　正在處理：{STRATEGY_LABELS.get(s, s)} × {tf}"]
                if best_so_far is not None:
                    score = best_so_far.metrics.get(objective)
                    lines.append(f"全局最佳（{OBJECTIVES.get(objective, (objective,True))[0]}）：{score}　參數：{best_params}")
                global_detail.markdown("  \n".join(lines))
            except Exception:
                pass
        best_res, best_s, best_tf, best_par, results_by_combo = find_optimal_global(
            exchange_id=exchange_id, symbol=symbol, since_ms=since_ms, until_ms=until_ms,
            strategies=DEFAULT_STRATEGIES_GLOBAL, timeframes=DEFAULT_TIMEFRAMES_GLOBAL,
            objective=objective, initial_equity=initial_equity, leverage=leverage,
            take_profit_pct=take_profit_pct or None, stop_loss_pct=stop_loss_pct or None,
            exclude_outliers=exclude_outliers, max_combos_per_strategy=999,
            use_async=False, on_global_progress=on_global_progress,
        )
        global_progress.progress(1.0, text="✅ 已完成")
        global_status.caption("窮舉搜尋完成。")
        st.session_state["optimal_global_result"] = best_res
        st.session_state["optimal_global_strategy"] = best_s
        st.session_state["optimal_global_timeframe"] = best_tf
        st.session_state["optimal_global_params"] = best_par
        st.session_state["optimal_global_table"] = results_by_combo
        st.session_state["optimal_global_objective"] = objective
        if best_res:
            st.session_state["backtest_results"] = {best_s: best_res}
    except Exception as e:
        st.error(str(e))

# ────────────────────────── 主畫面 ──────────────────────────
if "backtest_results" not in st.session_state or not st.session_state["backtest_results"]:
    if st.session_state.get("optimal_global_result") is not None:
        best_s = st.session_state.get("optimal_global_strategy", "")
        st.session_state["backtest_results"] = {best_s: st.session_state["optimal_global_result"]}
    else:
        st.markdown("## 📊 StocksX — 通用回測平台")
        st.info("👈 請在左側設定參數後點擊「🚀 執行回測」或「🔍 找出最優策略」開始。")
        col_a, col_b, col_c = st.columns(3)
        col_a.markdown("#### 🎯 五大策略\n雙均線、買入持有、RSI、MACD、布林帶一鍵回測")
        col_b.markdown("#### 📈 互動圖表\nK 線圖、權益曲線、回撤分析")
        col_c.markdown("#### 🏆 最優搜尋\n窮舉策略×週期×參數找全局最優")
        st.stop()

backtest_results: dict[str, BacktestResult] = st.session_state["backtest_results"]

# ─── 頂部績效指標卡片 ───
st.markdown("## 📊 回測報告")
valid_results = {s: r for s, r in backtest_results.items() if not r.error}
if valid_results:
    best_strategy = max(valid_results.items(), key=lambda x: x[1].metrics.get("total_return_pct", -999))
    bm = best_strategy[1].metrics
    cols = st.columns(6)
    cols[0].metric("🏆 最佳策略", STRATEGY_LABELS.get(best_strategy[0], best_strategy[0]))
    cols[1].metric("💰 總報酬率", f"{bm.get('total_return_pct', 0)}%")
    cols[2].metric("📅 年化報酬", f"{bm.get('annual_return_pct', 0)}%")
    cols[3].metric("📉 最大回撤", f"{bm.get('max_drawdown_pct', 0)}%")
    cols[4].metric("📐 夏普比率", f"{bm.get('sharpe_ratio', 0)}")
    cols[5].metric("🔄 交易次數", f"{bm.get('num_trades', 0)}")

# ─── K 線圖 + 買賣點 ───
ohlcv_rows = st.session_state.get("ohlcv_rows")
if ohlcv_rows and len(ohlcv_rows) > 1:
    real_bars = [r for r in ohlcv_rows if not r.get("filled")]
    if real_bars:
        with st.expander("🕯️ K 線走勢圖", expanded=True):
            df_k = pd.DataFrame(real_bars)
            df_k["time"] = pd.to_datetime(df_k["timestamp"], unit="ms", utc=True)
            fig_k = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25],
                                  vertical_spacing=0.03)
            fig_k.add_trace(go.Candlestick(
                x=df_k["time"], open=df_k["open"], high=df_k["high"],
                low=df_k["low"], close=df_k["close"], name="K 線",
                increasing_line_color="#26A69A", decreasing_line_color="#EF5350",
            ), row=1, col=1)
            fig_k.add_trace(go.Bar(
                x=df_k["time"], y=df_k["volume"], name="成交量",
                marker_color="rgba(100,149,237,0.4)",
            ), row=2, col=1)

            # 在 K 線上疊加最佳策略的買賣點
            if valid_results:
                best_s_name, best_r = best_strategy
                for t in best_r.trades:
                    entry_t = pd.to_datetime(t["entry_ts"], unit="ms", utc=True)
                    exit_t = pd.to_datetime(t["exit_ts"], unit="ms", utc=True)
                    side_label = "多" if t["side"] == 1 else "空"
                    fig_k.add_trace(go.Scatter(
                        x=[entry_t], y=[t["entry_price"]], mode="markers",
                        marker=dict(symbol="triangle-up" if t["side"] == 1 else "triangle-down",
                                    size=10, color="#26A69A" if t["side"] == 1 else "#EF5350"),
                        name=f"進場({side_label})", showlegend=False,
                        hovertemplate=f"進場 {side_label}<br>價格: {t['entry_price']:.2f}<br>%{{x}}<extra></extra>"
                    ), row=1, col=1)
                    fig_k.add_trace(go.Scatter(
                        x=[exit_t], y=[t["exit_price"]], mode="markers",
                        marker=dict(symbol="x", size=9, color="#FF9800"),
                        name="出場", showlegend=False,
                        hovertemplate=f"出場<br>價格: {t['exit_price']:.2f}<br>P&L: {t['pnl_pct']:.2f}%<extra></extra>"
                    ), row=1, col=1)

            fig_k.update_layout(
                height=500, xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=30, b=0),
                legend=dict(orientation="h", y=1.02),
            )
            fig_k.update_yaxes(title_text="價格", row=1, col=1)
            fig_k.update_yaxes(title_text="量", row=2, col=1)
            st.plotly_chart(fig_k, use_container_width=True)

# ─── 權益曲線（Plotly 互動圖）───
curves_ok = [(s, r) for s, r in backtest_results.items() if r.equity_curve and not r.error]
if curves_ok:
    with st.expander("📈 權益曲線（全部策略）", expanded=True):
        fig_eq = go.Figure()
        for strategy in ALL_STRATEGIES:
            if strategy not in backtest_results:
                continue
            res = backtest_results[strategy]
            if res.error or not res.equity_curve:
                continue
            curve = res.equity_curve
            idx = pd.to_datetime([e["timestamp"] for e in curve], unit="ms", utc=True)
            eq = [e["equity"] for e in curve]
            label = STRATEGY_LABELS.get(strategy, strategy)
            color = STRATEGY_COLORS.get(strategy, "#888")
            fig_eq.add_trace(go.Scatter(
                x=idx, y=eq, mode="lines", name=label,
                line=dict(color=color, width=2),
                hovertemplate=f"{label}<br>權益: %{{y:,.0f}}<br>%{{x}}<extra></extra>"
            ))
        fig_eq.add_hline(y=initial_equity, line_dash="dash", line_color="gray",
                         annotation_text="初始資金", annotation_position="top left")
        fig_eq.update_layout(
            height=420, margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", y=1.05),
            yaxis_title="權益", xaxis_title="",
            hovermode="x unified",
        )
        st.plotly_chart(fig_eq, use_container_width=True)

# ─── 回撤曲線 ───
if curves_ok:
    with st.expander("📉 回撤分析", expanded=False):
        fig_dd = go.Figure()
        for strategy in ALL_STRATEGIES:
            if strategy not in backtest_results:
                continue
            res = backtest_results[strategy]
            if res.error or not res.equity_curve:
                continue
            equities = [e["equity"] for e in res.equity_curve]
            timestamps = pd.to_datetime([e["timestamp"] for e in res.equity_curve], unit="ms", utc=True)
            peak = equities[0]
            drawdowns = []
            for e in equities:
                if e > peak:
                    peak = e
                dd = (peak - e) / peak * 100 if peak else 0
                drawdowns.append(-dd)
            label = STRATEGY_LABELS.get(strategy, strategy)
            color = STRATEGY_COLORS.get(strategy, "#888")
            fig_dd.add_trace(go.Scatter(
                x=timestamps, y=drawdowns, mode="lines", name=label,
                line=dict(color=color, width=1.5), fill="tozeroy",
                hovertemplate=f"{label}<br>回撤: %{{y:.2f}}%<br>%{{x}}<extra></extra>"
            ))
        fig_dd.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=0),
            yaxis_title="回撤 %", legend=dict(orientation="h", y=1.08),
            hovermode="x unified",
        )
        st.plotly_chart(fig_dd, use_container_width=True)

# ─── 績效彙總表（色彩化）───
st.subheader("📋 各策略績效彙總")
perf_rows = []
for strategy, res in backtest_results.items():
    if res.error:
        perf_rows.append({"策略": STRATEGY_LABELS.get(strategy, strategy), "總報酬率%": None, "年化報酬%": None,
                          "最大回撤%": None, "夏普": None, "Sortino": None, "Calmar": None,
                          "交易次數": None, "勝率%": None, "備註": res.error})
    else:
        m = res.metrics
        perf_rows.append({
            "策略": STRATEGY_LABELS.get(strategy, strategy),
            "總報酬率%": m.get("total_return_pct"),
            "年化報酬%": m.get("annual_return_pct"),
            "最大回撤%": m.get("max_drawdown_pct"),
            "夏普": m.get("sharpe_ratio"),
            "Sortino": m.get("sortino_ratio"),
            "Calmar": m.get("calmar_ratio"),
            "交易次數": m.get("num_trades"),
            "勝率%": m.get("win_rate_pct"),
            "備註": "",
        })

df_perf = pd.DataFrame(perf_rows)


def _highlight_perf(val):
    if val is None or val == "" or val == "-":
        return ""
    try:
        v = float(val)
        if v > 0:
            return "color: #0d7a0d; font-weight: bold"
        elif v < 0:
            return "color: #c00; font-weight: bold"
    except (TypeError, ValueError):
        pass
    return ""


num_cols = ["總報酬率%", "年化報酬%", "夏普", "Sortino", "Calmar"]
existing_num_cols = [c for c in num_cols if c in df_perf.columns]
if existing_num_cols:
    styled_perf = df_perf.style.map(_highlight_perf, subset=existing_num_cols)
    st.dataframe(styled_perf, use_container_width=True, hide_index=True)
else:
    st.dataframe(df_perf, use_container_width=True, hide_index=True)

# ─── CSV 下載 ───
csv_buf = BytesIO()
df_perf.to_csv(csv_buf, index=False, encoding="utf-8-sig")
st.download_button("📥 下載績效摘要 CSV", csv_buf.getvalue(), "backtest_summary.csv", "text/csv")

# ─── 交易明細 ───
with st.expander("📝 交易明細（各策略）", expanded=False):
    any_trades = False
    for strategy in ALL_STRATEGIES:
        if strategy not in backtest_results:
            continue
        res = backtest_results[strategy]
        label = STRATEGY_LABELS.get(strategy, strategy)
        if res.error:
            st.warning(f"{label}：{res.error}")
            continue
        if not res.trades:
            continue

        any_trades = True
        st.markdown(f"**{label}**")

        df_trades = pd.DataFrame(res.trades)
        df_trades["序號"] = range(1, len(df_trades) + 1)
        df_trades["進場時間"] = pd.to_datetime(df_trades["entry_ts"], unit="ms", utc=True)
        df_trades["出場時間"] = pd.to_datetime(df_trades["exit_ts"], unit="ms", utc=True)
        duration_ms = df_trades["exit_ts"] - df_trades["entry_ts"]
        duration_h = duration_ms / (1000 * 3600)
        df_trades["持倉時長"] = duration_h.apply(
            lambda h: f"{int(h)//24}d {int(h)%24}h" if h >= 24 else f"{int(h)}h" if h >= 1 else f"{int(h * 60)}m"
        )
        df_trades["方向"] = df_trades["side"].map({1: "🟢 多", -1: "🔴 空"}).fillna(df_trades["side"].astype(str))
        df_trades["盈虧"] = df_trades["profit"].apply(
            lambda x: "✅ 盈" if (x or 0) > 0 else ("❌ 虧" if (x or 0) < 0 else "➖ 平")
        )
        if "liquidation" in df_trades.columns:
            df_trades["爆倉"] = df_trades["liquidation"].map(lambda x: "💥 是" if x else "否")
            if df_trades["爆倉"].str.contains("是").any():
                st.error("⚠️ 本策略曾發生爆倉")

        show_cols = ["序號", "進場時間", "出場時間", "方向", "entry_price", "exit_price",
                     "持倉時長", "pnl_pct", "盈虧", "profit"]
        if "爆倉" in df_trades.columns:
            show_cols.append("爆倉")
        show_cols = [c for c in show_cols if c in df_trades.columns]
        disp = df_trades[show_cols].rename(
            columns={"entry_price": "進場價", "exit_price": "出場價", "pnl_pct": "報酬率%", "profit": "獲利"}
        )
        st.dataframe(disp, use_container_width=True, hide_index=True)

        # 單策略交易明細 CSV
        csv_t = BytesIO()
        disp.to_csv(csv_t, index=False, encoding="utf-8-sig")
        st.download_button(f"📥 下載 {label} 交易明細", csv_t.getvalue(), f"trades_{strategy}.csv", "text/csv",
                           key=f"dl_trades_{strategy}")

    if not any_trades:
        st.write("無交易記錄。")

# ─── 最優策略結果 ───
if st.session_state.get("optimal_global_result") is not None:
    st.divider()
    st.markdown("## 🏆 最優策略結果")
    ob = st.session_state.get("optimal_global_objective", "sharpe_ratio")
    st.caption(f"依「{OBJECTIVES.get(ob, (ob, True))[0]}」窮舉搜尋後的全局最優")
    gbest = st.session_state["optimal_global_result"]
    gs = st.session_state.get("optimal_global_strategy", "")
    gtf = st.session_state.get("optimal_global_timeframe", "")
    gpar = st.session_state.get("optimal_global_params", {})

    st.info(f"**策略**: {STRATEGY_LABELS.get(gs, gs)}　|　**K 線週期**: {gtf}　|　**參數**: {gpar}")
    gm = gbest.metrics
    g_cols = st.columns(6)
    g_cols[0].metric("杠杆倍數", f"{int(gm.get('leverage', 1))}x")
    g_cols[1].metric("總報酬率", f"{gm.get('total_return_pct', 0)}%")
    g_cols[2].metric("年化報酬", f"{gm.get('annual_return_pct', 0)}%")
    g_cols[3].metric("最大回撤", f"{gm.get('max_drawdown_pct', 0)}%")
    g_cols[4].metric("夏普", gm.get("sharpe_ratio", 0))
    g_cols[5].metric("交易次數", gm.get("num_trades", 0))

    if gbest.equity_curve:
        curve = gbest.equity_curve
        eq = [e["equity"] for e in curve]
        idx = pd.to_datetime([e["timestamp"] for e in curve], unit="ms", utc=True)
        fig_opt = go.Figure()
        fig_opt.add_trace(go.Scatter(x=idx, y=eq, mode="lines", name="最優權益", line=dict(color="#636EFA", width=2)))
        fig_opt.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="權益")
        st.plotly_chart(fig_opt, use_container_width=True)

    tbl = st.session_state.get("optimal_global_table", [])
    if tbl:
        st.subheader("各策略×K線 最優分數")
        opt_rows = [{"策略": STRATEGY_LABELS.get(r["strategy"], r["strategy"]), "K線": r["timeframe"],
                     "參數": str(r.get("params", {})), "分數": r.get("score")} for r in tbl]
        df_opt = pd.DataFrame(opt_rows).sort_values("分數", ascending=False)
        st.dataframe(df_opt, use_container_width=True, hide_index=True)

    # Qwen AI
    st.subheader("🤖 Qwen AI 解讀")
    if st.button("讓 Qwen 分析這組最優策略", key="qwen_btn"):
        try:
            from src.ai import qwen_simple
            prompt_lines = [
                f"最優策略：{STRATEGY_LABELS.get(gs, gs)}", f"K 線週期：{gtf}", f"參數：{gpar}",
                f"總報酬率：{gm.get('total_return_pct', 0)}%", f"最大回撤：{gm.get('max_drawdown_pct', 0)}%",
                f"夏普：{gm.get('sharpe_ratio', 0)}", f"交易次數：{gm.get('num_trades', 0)}",
                "", "請用繁體中文，簡短分析優缺點與實盤注意事項。"
            ]
            st.markdown(qwen_simple("\n".join(prompt_lines)) or "（無回傳）")
        except Exception as e:
            st.warning(f"Qwen 調用失敗：{e}")

st.caption("⚠️ 免責聲明：本報告僅供學習與研究，不構成投資建議。最優參數為歷史回測結果，不代表未來表現。")
