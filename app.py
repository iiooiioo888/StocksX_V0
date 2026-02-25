# 回測頁面與報告 — Streamlit
"""
啟動方式：在專案根目錄執行
  streamlit run app.py
"""
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.backtest import BacktestResult, find_optimal, find_optimal_global, run_backtest
from src.backtest.optimizer import DEFAULT_STRATEGIES_GLOBAL, DEFAULT_TIMEFRAMES_GLOBAL, OBJECTIVES
from src.backtest import strategies as backtest_strategies

st.set_page_config(page_title="回測報告", page_icon="📈", layout="wide")

st.title("📈 通用回測")
st.caption("使用緩存 K 線執行策略回測；支援多策略與即時最優參數搜尋。結果僅供研究，實盤請以交易所為準。")


def to_ms(d):
    dt = d if hasattr(d, "tzinfo") and d.tzinfo else d.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


# 全部策略一併回測，不再單選
ALL_STRATEGIES = list(backtest_strategies.STRATEGY_CONFIG.keys())
STRATEGY_LABELS = {
    "sma_cross": "雙均線交叉",
    "buy_and_hold": "買入持有",
    "rsi_signal": "RSI",
    "macd_cross": "MACD 交叉",
    "bollinger_signal": "布林帶",
}


# 常用永續合約交易對（Binance/Bybit 格式）
SYMBOL_OPTIONS = [
    "BTC/USDT:USDT",
    "ETH/USDT:USDT",
    "BNB/USDT:USDT",
    "SOL/USDT:USDT",
    "XRP/USDT:USDT",
    "DOGE/USDT:USDT",
    "ADA/USDT:USDT",
    "AVAX/USDT:USDT",
    "LINK/USDT:USDT",
    "MATIC/USDT:USDT",
    "DOT/USDT:USDT",
    "LTC/USDT:USDT",
    "UNI/USDT:USDT",
    "ATOM/USDT:USDT",
    "ETC/USDT:USDT",
    "XLM/USDT:USDT",
    "NEAR/USDT:USDT",
    "APT/USDT:USDT",
    "ARB/USDT:USDT",
    "OP/USDT:USDT",
    "SUI/USDT:USDT",
    "SEI/USDT:USDT",
    "INJ/USDT:USDT",
    "TIA/USDT:USDT",
    "其他（自填）",
]

with st.sidebar:
    st.header("回測參數")
    exchange_id = st.selectbox("交易所", ["binance", "bybit", "okx"], index=0)
    symbol_choice = st.selectbox("標的（永續合約）", SYMBOL_OPTIONS, index=0)
    if symbol_choice == "其他（自填）":
        symbol = st.text_input("自訂交易對", value="BTC/USDT:USDT", key="symbol_custom")
    else:
        symbol = symbol_choice
    timeframe = st.selectbox("K 線週期", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3)

    today = datetime.now(timezone.utc)
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("開始日期", value=today.replace(day=max(1, today.day - 30)))
    with col2:
        end = st.date_input("結束日期", value=today)

    st.caption("將對全部策略（雙均線、買入持有、RSI、MACD、布林帶）一併回測並畫在同一張圖。")
    initial_equity = st.number_input("初始資金", min_value=100.0, value=10000.0, step=500.0)
    leverage = st.number_input("杠杆倍數", min_value=1.0, value=1.0, step=1.0, max_value=125.0)
    col_tp, col_sl = st.columns(2)
    with col_tp:
        take_profit_pct = st.number_input("止盈 (%)", min_value=0.0, value=0.0, step=0.5)
    with col_sl:
        stop_loss_pct = st.number_input("止損 (%)", min_value=0.0, value=0.0, step=0.5)
    exclude_outliers = st.checkbox("排除插針資料", value=False)
    run_btn = st.button("執行回測", type="primary")

since_ms = to_ms(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc))
until_ms = to_ms(datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc))

if run_btn:
    if since_ms >= until_ms:
        st.error("請選擇「開始日期」早於「結束日期」。")
    else:
        with st.spinner("回測中…（全部策略 × 若缺數據會自動拉取）"):
            results = {}
            for strategy in ALL_STRATEGIES:
                params = (backtest_strategies.STRATEGY_CONFIG.get(strategy, {}).get("defaults") or {}).copy()
                res = run_backtest(
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
                    exclude_outliers=exclude_outliers,
                )
                results[strategy] = res
        st.session_state["backtest_results"] = results
        st.session_state.pop("backtest_result", None)
        for key in ("optimal_result", "optimal_results_list", "optimal_global_result", "optimal_global_strategy", "optimal_global_timeframe", "optimal_global_params", "optimal_global_table", "optimal_global_objective"):
            st.session_state.pop(key, None)

st.sidebar.divider()
st.sidebar.subheader("即時最優策略")
objective = st.sidebar.selectbox(
    "優化目標",
    list(OBJECTIVES.keys()),
    index=0,
    format_func=lambda x: OBJECTIVES[x][0],
)
optimize_btn = st.sidebar.button("找出最優策略", type="primary")
st.sidebar.caption("窮舉所有策略 × K線週期 × 參數，依上方優化目標找出全局最優。")

if optimize_btn and since_ms < until_ms:
    st.subheader("窮舉搜尋中…（策略 × K線週期 × 參數）")
    global_progress = st.progress(0.0, text="0 / ? 組合")
    global_status = st.empty()
    global_chart_placeholder = st.empty()
    global_detail = st.empty()
    try:
        def on_global_progress(s, tf, done, total, best_so_far, best_params):
            try:
                global_progress.progress(done / total if total else 0, text=f"{done} / {total} 組合")
                global_status.caption(f"當前: {STRATEGY_LABELS.get(s, s)} × {tf}")
                # 顯示目前正在做什麼 & 目前全局最佳狀況
                lines = [
                    f"掃描進度：{done} / {total}（策略 × K線週期 × 參數組合）",
                    f"正在處理：{STRATEGY_LABELS.get(s, s)} × {tf}",
                ]
                if best_so_far is not None:
                    score = best_so_far.metrics.get(objective)
                    lines.append(f"當前全局最佳分數（{OBJECTIVES.get(objective, (objective, True))[0]}）：{score}")
                    lines.append(f"全局最佳參數：{best_params}")
                global_detail.markdown("  \n".join(lines))
                if best_so_far and getattr(best_so_far, "equity_curve", None):
                    with global_chart_placeholder.container():
                        st.caption("當前最優權益曲線")
                        curve = best_so_far.equity_curve
                        eq = [e["equity"] for e in curve]
                        idx = pd.to_datetime([e["timestamp"] for e in curve], unit="ms", utc=True)
                        st.line_chart(pd.DataFrame({"equity": eq}, index=idx))
            except Exception:
                pass
        best_res, best_s, best_tf, best_par, results_by_combo = find_optimal_global(
            exchange_id=exchange_id,
            symbol=symbol,
            since_ms=since_ms,
            until_ms=until_ms,
            strategies=DEFAULT_STRATEGIES_GLOBAL,
            timeframes=DEFAULT_TIMEFRAMES_GLOBAL,
            objective=objective,
            initial_equity=initial_equity,
            leverage=leverage,
            take_profit_pct=take_profit_pct or None,
            stop_loss_pct=stop_loss_pct or None,
            exclude_outliers=exclude_outliers,
            max_combos_per_strategy=999,
            use_async=False,  # 使用帶資料重用的同步路徑，避免盲刷過慢
            on_global_progress=on_global_progress,
        )
        global_progress.progress(1.0, text="已完成")
        global_status.caption("窮舉搜尋完成，已遍歷所有策略 × K線週期 × 參數組合。")
        st.session_state["optimal_global_result"] = best_res
        st.session_state["optimal_global_strategy"] = best_s
        st.session_state["optimal_global_timeframe"] = best_tf
        st.session_state["optimal_global_params"] = best_par
        st.session_state["optimal_global_table"] = results_by_combo
        st.session_state["optimal_global_objective"] = objective
        st.session_state["backtest_results"] = {best_s: best_res}
    except Exception as e:
        st.error(str(e))

# ----- 主畫面：回測報告（全部策略一圖 + 彙總表 + 交易明細選策略）-----
if "backtest_results" not in st.session_state or not st.session_state["backtest_results"]:
    if st.session_state.get("optimal_global_result") is not None:
        best_s = st.session_state.get("optimal_global_strategy", "")
        st.session_state["backtest_results"] = {best_s: st.session_state["optimal_global_result"]}
    else:
        st.info("請在左側設定參數後點擊「執行回測」（將回測全部策略並畫在同一張圖），或點擊「找出最優策略」窮舉找出全局最優。")
        st.stop()

backtest_results: dict[str, BacktestResult] = st.session_state["backtest_results"]
# 任一結果的錯誤僅在該策略顯示於表內，不擋整頁
errors = [s for s, r in backtest_results.items() if r.error]

st.header("回測報告（全部策略）")
st.caption(f"杠杆倍數以左側設定為準；共 {len(backtest_results)} 個策略。")

# 權益曲線：全部策略畫在同一張圖
st.subheader("權益曲線（全部策略）")
curves_ok = [(s, r) for s, r in backtest_results.items() if r.equity_curve and not r.error]
if curves_ok:
    # 每條曲線用自家 timestamp 做索引，再以時間軸外連接，長度可不同（如爆倉提早結束）
    series_list = []
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
        series_list.append(pd.Series(eq, index=idx, name=label))
    df_eq = pd.concat(series_list, axis=1).sort_index()
    st.line_chart(df_eq)
else:
    st.write("無權益數據（或全部策略回測失敗）。")

# 各策略績效彙總表
st.subheader("各策略績效彙總")
rows = []
for strategy, res in backtest_results.items():
    if res.error:
        rows.append({"策略": STRATEGY_LABELS.get(strategy, strategy), "總報酬率%": "-", "年化報酬%": "-", "最大回撤%": "-", "夏普": "-", "交易次數": "-", "勝率%": "-", "備註": res.error})
    else:
        m = res.metrics
        rows.append({
            "策略": STRATEGY_LABELS.get(strategy, strategy),
            "總報酬率%": m.get("total_return_pct"),
            "年化報酬%": m.get("annual_return_pct"),
            "最大回撤%": m.get("max_drawdown_pct"),
            "夏普": m.get("sharpe_ratio"),
            "交易次數": m.get("num_trades"),
            "勝率%": m.get("win_rate_pct"),
            "備註": "",
        })
st.dataframe(pd.DataFrame(rows), use_container_width=True)

# 交易明細：各策略各一張表，方便逐策略對比與檢查爆倉
st.subheader("交易明細（各策略）")
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
    st.markdown(f"**策略：{label}**")

    df_trades = pd.DataFrame(res.trades)
    df_trades["序號"] = range(1, len(df_trades) + 1)
    df_trades["進場時間"] = pd.to_datetime(df_trades["entry_ts"], unit="ms", utc=True)
    df_trades["出場時間"] = pd.to_datetime(df_trades["exit_ts"], unit="ms", utc=True)
    duration_ms = df_trades["exit_ts"] - df_trades["entry_ts"]
    duration_h = duration_ms / (1000 * 3600)
    df_trades["持倉時長"] = duration_h.apply(
        lambda h: f"{int(h)//24}d {int(h)%24}h" if h >= 24 else f"{int(h)}h" if h >= 1 else f"{int(h * 60)}m"
    )
    df_trades["方向"] = df_trades["side"].map({1: "多", -1: "空"}).fillna(df_trades["side"].astype(str))
    df_trades["盈虧"] = df_trades["profit"].apply(
        lambda x: "盈" if (x or 0) > 0 else ("虧" if (x or 0) < 0 else "平")
    )
    if "liquidation" in df_trades.columns:
        df_trades["爆倉"] = df_trades["liquidation"].map(lambda x: "是" if x else "否")
        if df_trades["爆倉"].eq("是").any():
            st.warning("本策略曾發生爆倉：爆倉後權益將維持 0，且不再開新倉。")

    show_cols = [
        "序號",
        "進場時間",
        "出場時間",
        "方向",
        "entry_price",
        "exit_price",
        "持倉時長",
        "pnl_pct",
        "盈虧",
        "爆倉",
        "profit",
    ]
    show_cols = [c for c in show_cols if c in df_trades.columns]
    disp = df_trades[show_cols].rename(
        columns={"entry_price": "進場價", "exit_price": "出場價", "pnl_pct": "報酬率%", "profit": "獲利"}
    )

    def _color_盈亏(val):
        if val == "盈":
            return "color: #0d7a0d"
        if val == "虧":
            return "color: #c00"
        return ""

    def _color_num(val):
        if val is None or (isinstance(val, (int, float)) and val == 0):
            return ""
        try:
            v = float(val)
            return "color: #0d7a0d" if v > 0 else "color: #c00"
        except (TypeError, ValueError):
            return ""

    styled = disp.style.map(_color_盈亏, subset=["盈虧"]).map(_color_num, subset=["報酬率%", "獲利"])
    st.dataframe(styled, use_container_width=True)

if not any_trades:
    st.write("無交易記錄。")

# ----- 最優策略結果（窮舉：策略 × K線 × 參數）-----
if st.session_state.get("optimal_global_result") is not None:
    st.divider()
    st.header("最優策略結果（窮舉所有可能性）")
    ob = st.session_state.get("optimal_global_objective", "sharpe_ratio")
    st.caption(f"依「{OBJECTIVES.get(ob, (ob, True))[0]}」窮舉 策略×K線週期×參數 後的全局最優。")
    gbest = st.session_state["optimal_global_result"]
    gs = st.session_state.get("optimal_global_strategy", "")
    gtf = st.session_state.get("optimal_global_timeframe", "")
    gpar = st.session_state.get("optimal_global_params", {})
    st.subheader("最優組合")
    st.write(f"**策略**: {STRATEGY_LABELS.get(gs, gs)} | **K 線週期**: {gtf} | **參數**: {gpar}")
    gm = gbest.metrics
    g0, g1, g2, g3, g4, g5 = st.columns(6)
    g0.metric("杠杆倍數", f"{int(gm.get('leverage', 1))}x", None)
    g1.metric("總報酬率", f"{gm.get('total_return_pct', 0)}%", None)
    g2.metric("年化報酬", f"{gm.get('annual_return_pct', 0)}%", None)
    g3.metric("最大回撤", f"{gm.get('max_drawdown_pct', 0)}%", None)
    g4.metric("夏普", gm.get("sharpe_ratio", 0), None)
    g5.metric("交易次數", gm.get("num_trades", 0), None)
    if gbest.equity_curve:
        curve = gbest.equity_curve
        eq = [e["equity"] for e in curve]
        idx = pd.to_datetime([e["timestamp"] for e in curve], unit="ms", utc=True)
        st.line_chart(pd.DataFrame({"equity": eq}, index=idx))
    tbl = st.session_state.get("optimal_global_table", [])
    if tbl:
        st.subheader("各策略×K線 最優分數")
        rows = [{"策略": STRATEGY_LABELS.get(r["strategy"], r["strategy"]), "K線": r["timeframe"], "參數": str(r.get("params", {})), "分數": r.get("score")} for r in tbl]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # Qwen AI 解讀最優策略
    st.subheader("Qwen AI 解讀最優策略")
    ai_col = st.container()
    with ai_col:
        ai_clicked = st.button("讓 Qwen 分析這組最優策略", key="qwen_analyze_optimal")
        if ai_clicked:
            try:
                from src.ai import qwen_simple

                prompt_lines = [
                    f"最優策略：{STRATEGY_LABELS.get(gs, gs)}",
                    f"K 線週期：{gtf}",
                    f"參數：{gpar}",
                    f"杠杆倍數：{int(gm.get('leverage', 1))}x",
                    f"總報酬率：{gm.get('total_return_pct', 0)}%",
                    f"年化報酬：{gm.get('annual_return_pct', 0)}%",
                    f"最大回撤：{gm.get('max_drawdown_pct', 0)}%",
                    f"夏普：{gm.get('sharpe_ratio', 0)}",
                    f"交易次數：{gm.get('num_trades', 0)}，勝率：{gm.get('win_rate_pct', 0)}%",
                    "",
                    "請用繁體中文，幫我：",
                    "1）簡短說明這組策略的「優點」與「風險點」。",
                    "2）指出在實際下單時需要特別留意哪些情境（例如連續虧損、爆倉風險、滑點等）。",
                ]
                ai_text = qwen_simple("\n".join(prompt_lines))
                st.markdown(ai_text or "（Qwen 沒有回傳內容）")
            except Exception as e:
                st.warning(f"Qwen 調用失敗：{e}")

st.caption("免責聲明：本報告僅供學習與研究，不構成投資建議。最優參數為歷史回測結果，不代表未來表現。")
