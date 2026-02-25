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
from src.data.traditional import TraditionalDataFetcher
from src.auth import UserDB

st.set_page_config(page_title="StocksX — 通用回測", page_icon="📊", layout="wide")

_user_db = UserDB()

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
    "sma_cross": "雙均線交叉", "buy_and_hold": "買入持有",
    "rsi_signal": "RSI", "macd_cross": "MACD 交叉", "bollinger_signal": "布林帶",
    "ema_cross": "EMA 交叉", "donchian_channel": "唐奇安通道",
    "supertrend": "超級趨勢", "dual_thrust": "雙推力", "vwap_reversion": "VWAP 回歸",
}
STRATEGY_COLORS = {
    "sma_cross": "#636EFA", "buy_and_hold": "#00CC96", "rsi_signal": "#EF553B",
    "macd_cross": "#AB63FA", "bollinger_signal": "#FFA15A", "ema_cross": "#19D3F3",
    "donchian_channel": "#FF6692", "supertrend": "#B6E880", "dual_thrust": "#FF97FF",
    "vwap_reversion": "#FECB52",
}

CRYPTO_CATEGORIES = {
    "🔥 主流永續": [
        "BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT", "SOL/USDT:USDT",
        "XRP/USDT:USDT", "DOGE/USDT:USDT", "ADA/USDT:USDT", "AVAX/USDT:USDT",
        "LINK/USDT:USDT", "DOT/USDT:USDT", "LTC/USDT:USDT",
    ],
    "💎 主流現貨": [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
        "DOGE/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "LTC/USDT",
    ],
    "🌐 DeFi": [
        "UNI/USDT", "AAVE/USDT", "LINK/USDT", "ATOM/USDT", "INJ/USDT",
        "UNI/USDT:USDT", "AAVE/USDT:USDT",
    ],
    "🚀 Layer2 / 新幣": [
        "ARB/USDT", "OP/USDT", "SUI/USDT", "SEI/USDT", "TIA/USDT",
        "APT/USDT", "NEAR/USDT", "WLD/USDT", "JUP/USDT", "STRK/USDT",
        "ARB/USDT:USDT", "OP/USDT:USDT", "SUI/USDT:USDT", "SEI/USDT:USDT",
        "TIA/USDT:USDT", "APT/USDT:USDT", "NEAR/USDT:USDT",
    ],
    "🐸 Meme": [
        "DOGE/USDT", "SHIB/USDT", "PEPE/USDT", "BONK/USDT", "WIF/USDT", "FLOKI/USDT",
        "DOGE/USDT:USDT", "SHIB/USDT:USDT", "PEPE/USDT:USDT", "BONK/USDT:USDT",
        "WIF/USDT:USDT", "FLOKI/USDT:USDT",
    ],
}

TRADITIONAL_CATEGORIES = {
    "📈 美股": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "INTC",
        "NFLX", "CRM", "ORCL", "ADBE", "PYPL", "COIN", "MSTR", "PLTR", "UBER",
    ],
    "🇹🇼 台股": [
        "2330.TW", "2317.TW", "2454.TW", "2308.TW", "2881.TW", "2882.TW",
        "2303.TW", "3711.TW", "2412.TW", "1301.TW",
    ],
    "🏦 ETF": [
        "SPY", "QQQ", "IWM", "DIA", "VTI",
        "GLD", "SLV", "USO", "TLT", "HYG",
        "ARKK", "SOXX", "XLF", "XLE", "XLK",
        "0050.TW", "00878.TW", "00919.TW",
    ],
    "🛢️ 期貨 / 商品": [
        "GC=F", "SI=F", "CL=F", "NG=F",
        "ES=F", "NQ=F", "YM=F", "RTY=F",
        "ZB=F", "ZN=F", "ZC=F", "ZS=F",
    ],
    "🌍 指數": [
        "^GSPC", "^DJI", "^IXIC", "^RUT",
        "^FTSE", "^GDAXI", "^N225", "^HSI",
        "^TWII",
    ],
}

EXCHANGE_OPTIONS = {
    "okx": "OKX",
    "bitget": "Bitget",
    "gate": "Gate.io",
    "kucoin": "KuCoin（僅現貨）",
    "mexc": "MEXC",
    "htx": "HTX (火幣)",
    "bingx": "BingX",
    "woo": "WOO X",
    "binance": "Binance（受地區限制）",
    "bybit": "Bybit（受地區限制）",
    "cryptocom": "Crypto.com（僅現貨）",
}

# ────────────────────────── 側邊欄 ──────────────────────────
with st.sidebar:
    _u = st.session_state.get("user")
    if _u:
        st.markdown(f"### 👤 {_u['display_name']}")
        _sc1, _sc2 = st.columns(2)
        _sc1.page_link("pages/3_📜_歷史.py", label="📜 歷史", use_container_width=True)
        if _u["role"] == "admin":
            _sc2.page_link("pages/4_🛠️_管理.py", label="🛠️ 管理", use_container_width=True)
        if st.button("🚪 登出", use_container_width=True, key="sidebar_logout"):
            st.session_state.pop("user", None)
            st.switch_page("pages/1_🔐_登入.py")
        st.divider()
    st.markdown("## 📊 StocksX 回測")

    with st.expander("🔧 基本設定", expanded=True):
        market_type = st.radio("市場大類", ["₿ 加密貨幣", "🏛️ 傳統市場"], horizontal=True, key="mkt_type")
        is_traditional = (market_type == "🏛️ 傳統市場")

        if is_traditional:
            trad_keys = list(TRADITIONAL_CATEGORIES.keys())
            sub_cat = st.selectbox("細類", trad_keys, index=0, key="sub_cat_trad")
            cat_symbols = TRADITIONAL_CATEGORIES.get(sub_cat, trad_keys and TRADITIONAL_CATEGORIES[trad_keys[0]] or [])
            cat_symbols = list(cat_symbols) + ["其他（自填）"]
            exchange_id = "yfinance"
            st.caption("📊 數據來源：Yahoo Finance")
        else:
            crypto_keys = list(CRYPTO_CATEGORIES.keys())
            sub_cat = st.selectbox("細類", crypto_keys, index=0, key="sub_cat_crypto")
            cat_symbols = CRYPTO_CATEGORIES.get(sub_cat, crypto_keys and CRYPTO_CATEGORIES[crypto_keys[0]] or [])
            cat_symbols = list(cat_symbols) + ["其他（自填）"]
            exchange_id = st.selectbox(
                "交易所", list(EXCHANGE_OPTIONS.keys()), index=0,
                format_func=lambda x: EXCHANGE_OPTIONS.get(x, x),
            )

        symbol_choice = st.selectbox("交易對 / 股票代碼", cat_symbols, index=0)
        if symbol_choice == "其他（自填）":
            placeholder = "例: AAPL, 2330.TW, GC=F" if is_traditional else "例: BTC/USDT:USDT"
            symbol = st.text_input("自訂代碼", value="", placeholder=placeholder, key="symbol_custom")
            if not symbol:
                symbol = "AAPL" if is_traditional else "BTC/USDT:USDT"
        else:
            symbol = symbol_choice or ("AAPL" if is_traditional else "BTC/USDT:USDT")
        if is_traditional:
            timeframe = st.selectbox("K 線週期", ["1h", "1d"], index=1)
        else:
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

    with st.expander("⚙️ 策略參數自訂", expanded=False):
        st.caption("調整各策略的參數，留空則使用預設值")
        custom_params: dict[str, dict] = {}
        c1, c2 = st.columns(2)
        with c1:
            sma_fast = st.number_input("SMA 快線", min_value=2, value=10, step=1, key="sma_f")
            sma_slow = st.number_input("SMA 慢線", min_value=5, value=30, step=5, key="sma_s")
        custom_params["sma_cross"] = {"fast": sma_fast, "slow": sma_slow}
        with c2:
            rsi_period = st.number_input("RSI 週期", min_value=5, value=14, step=1, key="rsi_p")
            rsi_ob = st.number_input("RSI 超買", min_value=50, value=70, step=5, key="rsi_ob")
            rsi_os = st.number_input("RSI 超賣", min_value=10, value=30, step=5, key="rsi_os")
        custom_params["rsi_signal"] = {"period": rsi_period, "oversold": float(rsi_os), "overbought": float(rsi_ob)}
        mc1, mc2 = st.columns(2)
        with mc1:
            macd_f = st.number_input("MACD 快線", min_value=2, value=12, step=1, key="macd_f")
            macd_s = st.number_input("MACD 慢線", min_value=5, value=26, step=1, key="macd_s")
            macd_sig = st.number_input("MACD 信號", min_value=2, value=9, step=1, key="macd_sig")
        custom_params["macd_cross"] = {"fast": macd_f, "slow": macd_s, "signal": macd_sig}
        with mc2:
            boll_p = st.number_input("布林帶週期", min_value=5, value=20, step=1, key="boll_p")
            boll_std = st.number_input("布林帶倍數", min_value=0.5, value=2.0, step=0.5, key="boll_std")
        custom_params["bollinger_signal"] = {"period": boll_p, "std_dev": boll_std}
        custom_params["buy_and_hold"] = {}
        st.divider()
        st.caption("新策略參數")
        nc1, nc2 = st.columns(2)
        with nc1:
            ema_f = st.number_input("EMA 快線", min_value=2, value=12, step=1, key="ema_f")
            ema_s = st.number_input("EMA 慢線", min_value=5, value=26, step=1, key="ema_s")
            dc_p = st.number_input("唐奇安週期", min_value=5, value=20, step=1, key="dc_p")
        custom_params["ema_cross"] = {"fast": ema_f, "slow": ema_s}
        custom_params["donchian_channel"] = {"period": dc_p, "breakout_mode": 1}
        with nc2:
            st_p = st.number_input("Supertrend 週期", min_value=5, value=10, step=1, key="st_p")
            st_m = st.number_input("Supertrend 倍數", min_value=1.0, value=3.0, step=0.5, key="st_m")
            dt_p = st.number_input("雙推力週期", min_value=2, value=4, step=1, key="dt_p")
        custom_params["supertrend"] = {"period": st_p, "multiplier": st_m}
        custom_params["dual_thrust"] = {"period": dt_p, "k1": 0.5, "k2": 0.5}
        custom_params["vwap_reversion"] = {"period": 20, "threshold": 2.0}

    with st.expander("🔄 多標的對比", expanded=False):
        compare_symbols_str = st.text_input(
            "輸入要對比的交易對（逗號分隔）",
            value="", placeholder="例: ETH/USDT:USDT, SOL/USDT:USDT",
            key="compare_syms",
        )
        compare_btn = st.button("📊 執行對比回測", use_container_width=True, key="compare_btn")

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
                if is_traditional:
                    fetcher = TraditionalDataFetcher()
                else:
                    _eid = exchange_id or "okx"
                    fetcher = CryptoDataFetcher(_eid)
                _sym = symbol or "BTC/USDT:USDT"
                rows = fetcher.get_ohlcv(_sym, timeframe, since_ms, until_ms, fill_gaps=True, exclude_outliers=exclude_outliers)
            except Exception as e:
                st.error(f"數據拉取失敗：{e}")
                rows = None
            if rows is not None:
                st.session_state["ohlcv_rows"] = rows
                for strategy in ALL_STRATEGIES:
                    params = custom_params.get(strategy) or (backtest_strategies.STRATEGY_CONFIG.get(strategy, {}).get("defaults") or {}).copy()
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
        # 自動保存回測歷史 + 檢查提醒
        _cur_user = st.session_state.get("user")
        if _cur_user and results:
            for _strat, _res in results.items():
                if not _res.error:
                    _user_db.save_backtest(
                        _cur_user["id"], symbol, exchange_id or "okx", timeframe, _strat,
                        custom_params.get(_strat, {}), _res.metrics,
                    )
            triggered = _user_db.check_alerts(_cur_user["id"], results)
            if triggered:
                for t in triggered:
                    st.toast(f"🔔 提醒觸發！{t['symbol']} — {t['strategy']}：{t['condition_type']} 實際值={t['actual']:.2f}%", icon="🔔")

# ────────────────────────── 多標的對比 ──────────────────────────
if compare_btn and compare_symbols_str.strip():
    compare_list = [s.strip() for s in compare_symbols_str.split(",") if s.strip()]
    if symbol not in compare_list:
        compare_list.insert(0, symbol)
    with st.spinner(f"正在對比 {len(compare_list)} 個標的…"):
        compare_results: dict[str, dict] = {}
        for sym in compare_list:
            try:
                fetcher = CryptoDataFetcher(exchange_id)
                rows = fetcher.get_ohlcv(sym, timeframe, since_ms, until_ms, fill_gaps=True)
                params_bh = {}
                res = _run_backtest_on_rows(
                    rows=rows, exchange_id=exchange_id, symbol=sym, timeframe=timeframe,
                    since_ms=since_ms, until_ms=until_ms, strategy="buy_and_hold", strategy_params=params_bh,
                    initial_equity=initial_equity, leverage=leverage,
                    take_profit_pct=None, stop_loss_pct=None,
                )
                compare_results[sym] = {"result": res, "rows": rows}
            except Exception as e:
                compare_results[sym] = {"error": str(e)}
        st.session_state["compare_results"] = compare_results

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

ohlcv_rows = st.session_state.get("ohlcv_rows")
curves_ok = [(s, r) for s, r in backtest_results.items() if r.equity_curve and not r.error]

# ─── 用 Tabs 分頁，避免同時渲染太多 Plotly 圖表 ───
tab_names = ["🕯️ K線+權益", "📊 統計分析", "🔔 信號視覺化"]
tab1, tab2, tab3 = st.tabs(tab_names)

with tab1:
    # K 線圖 + 買賣點
    if ohlcv_rows and len(ohlcv_rows) > 1:
        real_bars = [r for r in ohlcv_rows if not r.get("filled")]
        if real_bars:
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
            fig_k.update_layout(height=500, xaxis_rangeslider_visible=False,
                                margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", y=1.02))
            fig_k.update_yaxes(title_text="價格", row=1, col=1)
            fig_k.update_yaxes(title_text="量", row=2, col=1)
            st.plotly_chart(fig_k, use_container_width=True)

    # 權益曲線
    if curves_ok:
        st.subheader("📈 權益曲線")
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
            fig_eq.add_trace(go.Scatter(x=idx, y=eq, mode="lines", name=label,
                                        line=dict(color=color, width=2),
                                        hovertemplate=f"{label}<br>權益: %{{y:,.0f}}<br>%{{x}}<extra></extra>"))
        fig_eq.add_hline(y=initial_equity, line_dash="dash", line_color="gray",
                         annotation_text="初始資金", annotation_position="top left")
        fig_eq.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0),
                             legend=dict(orientation="h", y=1.05), yaxis_title="權益", hovermode="x unified")
        st.plotly_chart(fig_eq, use_container_width=True)

    # 回撤曲線
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
                fig_dd.add_trace(go.Scatter(x=timestamps, y=drawdowns, mode="lines", name=label,
                                            line=dict(color=color, width=1.5), fill="tozeroy",
                                            hovertemplate=f"{label}<br>回撤: %{{y:.2f}}%<br>%{{x}}<extra></extra>"))
            fig_dd.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                                 yaxis_title="回撤 %", legend=dict(orientation="h", y=1.08), hovermode="x unified")
            st.plotly_chart(fig_dd, use_container_width=True)

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

with tab2:
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
                "總報酬率%": m.get("total_return_pct"), "年化報酬%": m.get("annual_return_pct"),
                "最大回撤%": m.get("max_drawdown_pct"), "夏普": m.get("sharpe_ratio"),
                "Sortino": m.get("sortino_ratio"), "Calmar": m.get("calmar_ratio"),
                "交易次數": m.get("num_trades"), "勝率%": m.get("win_rate_pct"), "備註": "",
            })
    df_perf = pd.DataFrame(perf_rows)
    st.subheader("📋 績效彙總")
    num_cols = ["總報酬率%", "年化報酬%", "夏普", "Sortino", "Calmar"]
    existing_num_cols = [c for c in num_cols if c in df_perf.columns]
    if existing_num_cols:
        st.dataframe(df_perf.style.map(_highlight_perf, subset=existing_num_cols), use_container_width=True, hide_index=True)
    else:
        st.dataframe(df_perf, use_container_width=True, hide_index=True)
    csv_buf = BytesIO()
    df_perf.to_csv(csv_buf, index=False, encoding="utf-8-sig")
    st.download_button("📥 下載績效摘要 CSV", csv_buf.getvalue(), "backtest_summary.csv", "text/csv")

    all_trades_for_charts = []
    for strategy in ALL_STRATEGIES:
        if strategy not in backtest_results:
            continue
        res = backtest_results[strategy]
        if res.error or not res.trades:
            continue
        for t in res.trades:
            t_copy = dict(t)
            t_copy["strategy"] = STRATEGY_LABELS.get(strategy, strategy)
            all_trades_for_charts.append(t_copy)

    if all_trades_for_charts:
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("**📊 交易損益分佈**")
            pnl_values = [t["pnl_pct"] for t in all_trades_for_charts]
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(x=pnl_values, nbinsx=30, name="P&L %",
                                            marker_color="rgba(239,83,80,0.7)"))
            win_count = sum(1 for v in pnl_values if v > 0)
            loss_count = sum(1 for v in pnl_values if v < 0)
            avg_win = sum(v for v in pnl_values if v > 0) / win_count if win_count else 0
            avg_loss = sum(v for v in pnl_values if v < 0) / loss_count if loss_count else 0
            fig_hist.add_vline(x=0, line_dash="dash", line_color="gray")
            fig_hist.update_layout(height=280, margin=dict(l=0, r=0, t=30, b=0),
                                   xaxis_title="報酬率 %", yaxis_title="次數",
                                   title_text=f"盈 {win_count} 筆 ({avg_win:.2f}%) / 虧 {loss_count} 筆 ({avg_loss:.2f}%)",
                                   title_font_size=12)
            st.plotly_chart(fig_hist, use_container_width=True)
        with chart_col2:
            st.markdown("**⏱️ 持倉時長分佈**")
            durations_h = [(t["exit_ts"] - t["entry_ts"]) / 3600000 for t in all_trades_for_charts]
            fig_dur = go.Figure()
            fig_dur.add_trace(go.Histogram(x=durations_h, nbinsx=20, name="時長",
                                           marker_color="rgba(99,110,250,0.7)"))
            avg_dur = sum(durations_h) / len(durations_h) if durations_h else 0
            fig_dur.add_vline(x=avg_dur, line_dash="dash", line_color="#FF9800",
                              annotation_text=f"平均 {avg_dur:.1f}h")
            fig_dur.update_layout(height=280, margin=dict(l=0, r=0, t=30, b=0),
                                  xaxis_title="持倉時長 (小時)", yaxis_title="次數",
                                  title_text=f"共 {len(durations_h)} 筆，平均 {avg_dur:.1f}h", title_font_size=12)
            st.plotly_chart(fig_dur, use_container_width=True)

    if curves_ok and valid_results:
        with st.expander("🗓️ 每日報酬率熱力圖", expanded=False):
            heatmap_strategy = st.selectbox("選擇策略", list(valid_results.keys()), index=0,
                                            format_func=lambda x: STRATEGY_LABELS.get(x, x), key="heatmap_strat")
            hr = valid_results[heatmap_strategy]
            if hr.equity_curve and len(hr.equity_curve) > 1:
                eq_ts = pd.to_datetime([e["timestamp"] for e in hr.equity_curve], unit="ms", utc=True)
                eq_vals = [e["equity"] for e in hr.equity_curve]
                eq_series = pd.Series(eq_vals, index=eq_ts)
                daily_eq = eq_series.resample("D").last().dropna()
                daily_ret = daily_eq.pct_change().dropna() * 100
                if len(daily_ret) > 0:
                    df_daily = pd.DataFrame({"date": daily_ret.index, "return": daily_ret.values})
                    df_daily["week"] = df_daily["date"].dt.isocalendar().week.astype(int)
                    df_daily["weekday"] = df_daily["date"].dt.weekday
                    wn = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
                    pivot = df_daily.pivot_table(index="weekday", columns="week", values="return", aggfunc="mean")
                    pivot = pivot.reindex(range(7))
                    pivot.index = [wn[i] for i in pivot.index]
                    fig_hm = go.Figure(data=go.Heatmap(
                        z=pivot.values, x=[f"W{c}" for c in pivot.columns], y=pivot.index,
                        colorscale="RdYlGn", zmid=0, colorbar_title="日報酬%",
                        hovertemplate="週: %{x}<br>%{y}<br>報酬: %{z:.2f}%<extra></extra>"))
                    fig_hm.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0),
                                         yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig_hm, use_container_width=True)
                else:
                    st.info("資料不足以產生熱力圖（需至少 2 天）")

# ─── 多標的對比結果 ───
if st.session_state.get("compare_results"):
    st.divider()
    st.markdown("## 🔄 多標的對比")
    compare_data = st.session_state["compare_results"]
    fig_cmp = go.Figure()
    cmp_table_rows = []
    cmp_colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#FF6692", "#B6E880"]
    for i, (sym, data) in enumerate(compare_data.items()):
        if "error" in data:
            cmp_table_rows.append({"標的": sym, "報酬率%": "-", "最大回撤%": "-", "備註": data["error"]})
            continue
        res = data["result"]
        if res.error or not res.equity_curve:
            cmp_table_rows.append({"標的": sym, "報酬率%": "-", "最大回撤%": "-", "備註": res.error or "無數據"})
            continue
        eq = [e["equity"] for e in res.equity_curve]
        idx = pd.to_datetime([e["timestamp"] for e in res.equity_curve], unit="ms", utc=True)
        eq_norm = [e / eq[0] * 100 for e in eq]
        color = cmp_colors[i % len(cmp_colors)]
        fig_cmp.add_trace(go.Scatter(x=idx, y=eq_norm, mode="lines", name=sym,
                                     line=dict(color=color, width=2)))
        m = res.metrics
        cmp_table_rows.append({
            "標的": sym, "報酬率%": m.get("total_return_pct"), "年化%": m.get("annual_return_pct"),
            "最大回撤%": m.get("max_drawdown_pct"), "夏普": m.get("sharpe_ratio"), "備註": "",
        })

    fig_cmp.add_hline(y=100, line_dash="dash", line_color="gray")
    fig_cmp.update_layout(
        height=400, margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="正規化權益 (%)", legend=dict(orientation="h", y=1.05),
        hovermode="x unified",
    )
    st.plotly_chart(fig_cmp, use_container_width=True)
    st.dataframe(pd.DataFrame(cmp_table_rows), use_container_width=True, hide_index=True)

with tab3:
    if ohlcv_rows and len(ohlcv_rows) > 1 and valid_results:
        sig_strategy = st.selectbox(
            "選擇策略查看信號", [s for s in ALL_STRATEGIES if s != "buy_and_hold" and s in valid_results],
            format_func=lambda x: STRATEGY_LABELS.get(x, x), key="sig_strat"
        )
        sig_params = custom_params.get(sig_strategy) or (backtest_strategies.STRATEGY_CONFIG.get(sig_strategy, {}).get("defaults") or {})
        signals = backtest_strategies.get_signal(sig_strategy, ohlcv_rows, **sig_params)

        real_bars = [r for r in ohlcv_rows if not r.get("filled")]
        if real_bars:
            df_sig = pd.DataFrame(real_bars)
            df_sig["time"] = pd.to_datetime(df_sig["timestamp"], unit="ms", utc=True)

            sig_map = {}
            for i, r in enumerate(ohlcv_rows):
                if i < len(signals):
                    sig_map[r["timestamp"]] = signals[i]
            df_sig["signal"] = df_sig["timestamp"].map(sig_map).fillna(0).astype(int)

            buy_pts = df_sig[(df_sig["signal"] == 1) & (df_sig["signal"].shift(1) != 1)]
            sell_pts = df_sig[(df_sig["signal"] == -1) & (df_sig["signal"].shift(1) != -1)]

            fig_sig = go.Figure()
            fig_sig.add_trace(go.Scatter(
                x=df_sig["time"], y=df_sig["close"], mode="lines", name="收盤價",
                line=dict(color="#888", width=1),
            ))
            if len(buy_pts) > 0:
                fig_sig.add_trace(go.Scatter(
                    x=buy_pts["time"], y=buy_pts["close"], mode="markers", name="做多信號",
                    marker=dict(symbol="triangle-up", size=10, color="#26A69A"),
                ))
            if len(sell_pts) > 0:
                fig_sig.add_trace(go.Scatter(
                    x=sell_pts["time"], y=sell_pts["close"], mode="markers", name="做空信號",
                    marker=dict(symbol="triangle-down", size=10, color="#EF5350"),
                ))
            fig_sig.update_layout(
                height=380, margin=dict(l=0, r=0, t=30, b=0),
                title_text=f"{STRATEGY_LABELS.get(sig_strategy, sig_strategy)} 信號 — ▲多 ▼空",
                title_font_size=14, legend=dict(orientation="h", y=1.05),
            )
            st.plotly_chart(fig_sig, use_container_width=True)
    else:
        st.info("需先執行回測才能顯示策略信號")

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

# ─── 批量回測結果（每個策略×週期的獨立細節） ───
if st.session_state.get("optimal_global_result") is not None:
    st.divider()
    st.markdown("## 🏆 批量回測結果")
    ob = st.session_state.get("optimal_global_objective", "sharpe_ratio")
    ob_label = OBJECTIVES.get(ob, (ob, True))[0]
    st.caption(f"依「{ob_label}」窮舉搜尋，以下為全局最優與各策略×K線的獨立分析")

    gbest = st.session_state["optimal_global_result"]
    gs = st.session_state.get("optimal_global_strategy", "")
    gtf = st.session_state.get("optimal_global_timeframe", "")
    gpar = st.session_state.get("optimal_global_params", {})
    tbl = st.session_state.get("optimal_global_table", [])

    # ── 全局最優摘要 ──
    st.info(f"🥇 **全局最優**：{STRATEGY_LABELS.get(gs, gs)} × {gtf}　|　參數：{gpar}")
    gm = gbest.metrics
    g_cols = st.columns(6)
    g_cols[0].metric("杠杆", f"{int(gm.get('leverage', 1))}x")
    g_cols[1].metric("總報酬", f"{gm.get('total_return_pct', 0)}%")
    g_cols[2].metric("年化", f"{gm.get('annual_return_pct', 0)}%")
    g_cols[3].metric("回撤", f"{gm.get('max_drawdown_pct', 0)}%")
    g_cols[4].metric("夏普", gm.get("sharpe_ratio", 0))
    g_cols[5].metric("交易", gm.get("num_trades", 0))

    # ── 排行榜表格 ──
    if tbl:
        st.subheader("📊 全部組合排行榜")
        rank_rows = []
        sorted_tbl = sorted(tbl, key=lambda r: r.get("score") or -9999, reverse=(ob != "max_drawdown_pct"))
        for rank, r in enumerate(sorted_tbl, 1):
            rm = r["result"].metrics if r.get("result") else {}
            is_best = (r["strategy"] == gs and r["timeframe"] == gtf)
            rank_rows.append({
                "排名": f"🥇 {rank}" if is_best else str(rank),
                "策略": STRATEGY_LABELS.get(r["strategy"], r["strategy"]),
                "K線": r["timeframe"],
                "參數": str(r.get("params", {})),
                f"{ob_label}": r.get("score"),
                "報酬率%": rm.get("total_return_pct"),
                "回撤%": rm.get("max_drawdown_pct"),
                "交易數": rm.get("num_trades"),
                "勝率%": rm.get("win_rate_pct"),
            })
        df_rank = pd.DataFrame(rank_rows)
        st.dataframe(df_rank, use_container_width=True, hide_index=True)

        # CSV
        csv_rank = BytesIO()
        df_rank.to_csv(csv_rank, index=False, encoding="utf-8-sig")
        st.download_button("📥 下載排行榜 CSV", csv_rank.getvalue(), "optimizer_ranking.csv", "text/csv",
                           key="dl_rank")

    # ── 每個策略×週期的獨立細節分析 ──
    if tbl:
        st.subheader("🔍 各組合詳細分析")
        st.caption("點選下方各組合展開查看獨立的指標、權益曲線與交易明細")

        for idx_r, r in enumerate(sorted_tbl):
            res = r.get("result")
            if not res or res.error:
                continue
            s_name = STRATEGY_LABELS.get(r["strategy"], r["strategy"])
            tf_name = r["timeframe"]
            rm = res.metrics
            is_best = (r["strategy"] == gs and r["timeframe"] == gtf)
            badge = "🥇 " if is_best else ""
            score_val = r.get("score", 0)

            with st.expander(
                f"{badge}{s_name} × {tf_name}　|　{ob_label}={score_val}　報酬={rm.get('total_return_pct', 0)}%",
                expanded=is_best,
            ):
                _show_detail = st.checkbox("載入圖表", value=is_best, key=f"show_{idx_r}")
                if not _show_detail:
                    st.caption("勾選上方「載入圖表」以顯示權益曲線")
                    mc = st.columns(6)
                    mc[0].metric("報酬率", f"{rm.get('total_return_pct', 0)}%")
                    mc[1].metric("年化", f"{rm.get('annual_return_pct', 0)}%")
                    mc[2].metric("回撤", f"{rm.get('max_drawdown_pct', 0)}%")
                    mc[3].metric("夏普", rm.get("sharpe_ratio", 0))
                    mc[4].metric("Sortino", rm.get("sortino_ratio", 0))
                    mc[5].metric("交易/勝率", f"{rm.get('num_trades', 0)} / {rm.get('win_rate_pct', 0)}%")
                    continue
                # 指標卡片
                mc = st.columns(6)
                mc[0].metric("報酬率", f"{rm.get('total_return_pct', 0)}%")
                mc[1].metric("年化", f"{rm.get('annual_return_pct', 0)}%")
                mc[2].metric("回撤", f"{rm.get('max_drawdown_pct', 0)}%")
                mc[3].metric("夏普", rm.get("sharpe_ratio", 0))
                mc[4].metric("Sortino", rm.get("sortino_ratio", 0))
                mc[5].metric("交易/勝率", f"{rm.get('num_trades', 0)} / {rm.get('win_rate_pct', 0)}%")

                st.caption(f"參數：{r.get('params', {})}")

                # 權益曲線
                if res.equity_curve:
                    eq = [e["equity"] for e in res.equity_curve]
                    eq_idx = pd.to_datetime([e["timestamp"] for e in res.equity_curve], unit="ms", utc=True)
                    fig_detail = go.Figure()
                    fig_detail.add_trace(go.Scatter(
                        x=eq_idx, y=eq, mode="lines", name=f"{s_name} × {tf_name}",
                        line=dict(color=STRATEGY_COLORS.get(r["strategy"], "#636EFA"), width=2),
                    ))
                    fig_detail.add_hline(y=eq[0], line_dash="dash", line_color="gray")
                    fig_detail.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="權益")
                    st.plotly_chart(fig_detail, use_container_width=True, key=f"eq_{idx_r}")

                # 交易明細
                if res.trades:
                    df_t = pd.DataFrame(res.trades)
                    df_t["序號"] = range(1, len(df_t) + 1)
                    df_t["進場"] = pd.to_datetime(df_t["entry_ts"], unit="ms", utc=True).dt.strftime("%m/%d %H:%M")
                    df_t["出場"] = pd.to_datetime(df_t["exit_ts"], unit="ms", utc=True).dt.strftime("%m/%d %H:%M")
                    df_t["方向"] = df_t["side"].map({1: "🟢多", -1: "🔴空"})
                    df_t["盈虧"] = df_t["profit"].apply(lambda x: "✅" if x > 0 else "❌" if x < 0 else "➖")
                    show = ["序號", "進場", "出場", "方向", "entry_price", "exit_price", "pnl_pct", "profit", "盈虧"]
                    show = [c for c in show if c in df_t.columns]
                    disp_t = df_t[show].rename(columns={
                        "entry_price": "進場價", "exit_price": "出場價", "pnl_pct": "報酬%", "profit": "獲利"
                    })
                    st.dataframe(disp_t, use_container_width=True, hide_index=True)
                    csv_detail = BytesIO()
                    disp_t.to_csv(csv_detail, index=False, encoding="utf-8-sig")
                    st.download_button(
                        f"📥 下載 {s_name}×{tf_name} 交易明細",
                        csv_detail.getvalue(), f"trades_{r['strategy']}_{tf_name}.csv", "text/csv",
                        key=f"dl_detail_{idx_r}",
                    )
                else:
                    st.caption("無交易記錄")

st.caption("⚠️ 免責聲明：本報告僅供學習與研究，不構成投資建議。最優參數為歷史回測結果，不代表未來表現。")
