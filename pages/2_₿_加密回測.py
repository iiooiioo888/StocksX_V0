# 加密貨幣回測（增強版 v4.0）
# 新增：策略參數管理、參數預設、快捷設定

import streamlit as st
import time as _time_mod
from datetime import datetime, timezone
from src.backtest.fees import get_fee_rate, get_slippage, EXCHANGE_FEES
from src.backtest import strategies as backtest_strategies
from src.data.crypto import CryptoDataFetcher
from src.data.integrity import validate_ohlcv
from src.auth import UserDB
from src.config import STRATEGY_LABELS, CRYPTO_CATEGORIES, EXCHANGE_OPTIONS
from src.ui_common import apply_theme, breadcrumb, check_session, sidebar_user_nav
from src.ui_backtest import ALL_STRATEGIES, run_all_strategies, render_summary_line, \
    render_kline_chart, render_equity_curves, render_performance_table, render_trade_details
from src.ui_strategy_params import (
    render_strategy_params,
    render_param_shortcuts,
    render_preset_manager,
    STRATEGY_PARAMS,
    validate_params,
)

st.set_page_config(page_title="StocksX — 加密回測", page_icon="💰", layout="wide")
apply_theme()
breadcrumb("加密貨幣回測", "💰")

_user = check_session()
_db = UserDB()

with st.sidebar:
    sidebar_user_nav(_user)

    with st.expander("🔧 設定", expanded=True):
        sub_cat = st.selectbox("分類", list(CRYPTO_CATEGORIES.keys()), index=0)
        cat_symbols = CRYPTO_CATEGORIES.get(sub_cat, []) + ["其他（自填）"]
        symbol = st.selectbox("交易對", cat_symbols, index=0)
        if symbol == "其他（自填）":
            symbol = st.text_input("自訂", value="BTC/USDT:USDT")
        exchange_id = st.selectbox("交易所", list(EXCHANGE_OPTIONS.keys()), index=0,
                                   format_func=lambda x: EXCHANGE_OPTIONS.get(x, x))
        timeframe = st.selectbox("K 線週期", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3)

    with st.expander("📅 時間", expanded=True):
        today = datetime.now(timezone.utc)
        c1, c2 = st.columns(2)
        start = c1.date_input("開始", value=today.replace(day=max(1, today.day - 30)))
        end = c2.date_input("結束", value=today)

    with st.expander("💰 資金", expanded=False):
        _settings = _db.get_settings(_user["id"]) if _user else {}
        initial_equity = st.number_input("初始資金", min_value=100.0,
                                         value=float(_settings.get("default_equity", 10000)), step=500.0)
        leverage = st.number_input("槓桿", min_value=1.0,
                                    value=float(_settings.get("default_leverage", 1)), max_value=125.0)
        _fee = get_fee_rate(exchange_id)
        _slip = get_slippage(exchange_id)
        st.caption(f"💸 {EXCHANGE_OPTIONS.get(exchange_id, exchange_id)}: {_fee}% + 滑點 {_slip}%")
        user_fee = st.number_input("手續費%", min_value=0.0, value=_fee, step=0.01)
        user_slip = st.number_input("滑點%", min_value=0.0, value=_slip, step=0.01)

    # 回測模式選擇
    mode = st.radio(
        "回測模式",
        ["全部策略", "單一策略（自訂參數）"],
        index=0,
        key="backtest_mode"
    )
    
    selected_strategy = None
    custom_params = {}
    
    if mode == "單一策略（自訂參數）":
        # 策略選擇
        selected_strategy = st.selectbox(
            "選擇策略",
            options=list(STRATEGY_PARAMS.keys()),
            format_func=lambda x: STRATEGY_PARAMS[x]["name"],
            index=0
        )
        
        # 快捷設定
        shortcuts = render_param_shortcuts(selected_strategy, key_prefix=f"shortcut_{selected_strategy}")
        
        # 參數設定
        custom_params = render_strategy_params(
            selected_strategy,
            key_prefix=f"custom_{selected_strategy}"
        )
        
        # 參數預設管理
        if _user:
            render_preset_manager(
                _user["id"],
                selected_strategy,
                custom_params,
                key_prefix=f"preset_{selected_strategy}"
            )
        
        # 驗證參數
        if custom_params:
            is_valid, error_msg = validate_params(selected_strategy, custom_params)
            if not is_valid:
                st.error(error_msg)
    
    run_btn = st.button("🚀 執行回測", type="primary", use_container_width=True)

def _to_ms(d):
    return int(datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).timestamp() * 1000)

since_ms = _to_ms(start)
until_ms = int(datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc).timestamp() * 1000)

if run_btn and since_ms < until_ms:
    _t0 = _time_mod.time()
    _bar = st.progress(0, text="連接交易所…")
    try:
        _bar.progress(20, text="拉取 K 線…")
        fetcher = CryptoDataFetcher(exchange_id or "okx")
        rows = fetcher.get_ohlcv(symbol or "BTC/USDT:USDT", timeframe, since_ms, until_ms, fill_gaps=True)
        _issues = validate_ohlcv(rows) if rows else ["無數據"]
        for _i in _issues:
            st.warning(f"⚠️ {_i}")
    except Exception as e:
        st.error(f"❌ {e}")
        rows = None
    
    if rows:
        if mode == "全部策略":
            # 執行所有策略
            _bar.progress(40, text=f"回測 {len(ALL_STRATEGIES)} 策略…")
            results = run_all_strategies(rows, exchange_id, symbol, timeframe, since_ms, until_ms,
                                         initial_equity, leverage, None, None, user_fee, user_slip)
        else:
            # 執行單一策略（自訂參數）
            if selected_strategy and custom_params:
                _bar.progress(40, text=f"回測策略：{STRATEGY_LABELS.get(selected_strategy, selected_strategy)}…")
                from src.backtest.engine import run_backtest as run_single_backtest
                result = run_single_backtest(
                    rows, exchange_id, symbol, timeframe, since_ms, until_ms,
                    initial_equity, leverage, selected_strategy, custom_params, user_fee, user_slip
                )
                results = {selected_strategy: result}
            else:
                st.error("請選擇策略並設定參數")
                results = {}
        
        _bar.progress(100, text="✅ 完成")
        _elapsed = _time_mod.time() - _t0
        st.session_state["crypto_results"] = results
        st.session_state["crypto_rows"] = rows
        st.markdown(f'<div class="success-banner">🎉 完成！{_elapsed:.1f}s</div>',
                    unsafe_allow_html=True)
        
        # 保存歷史
        if _user:
            for s, r in results.items():
                if not r.error:
                    params_to_save = custom_params if mode == "單一策略（自訂參數）" and s == selected_strategy else {}
                    _db.save_backtest(_user["id"], symbol, exchange_id or "okx", timeframe, s, params_to_save, r.metrics)

if "crypto_results" in st.session_state:
    results = st.session_state["crypto_results"]
    rows = st.session_state.get("crypto_rows", [])
    best, valid = render_summary_line(results)
    if valid:
        tab1, tab2 = st.tabs(["🕯️ 圖表", "📊 績效"])
        with tab1:
            if rows:
                render_kline_chart(rows, best)
            render_equity_curves(results, initial_equity)
        with tab2:
            render_performance_table(results)
            with st.expander("📝 交易明細", expanded=False):
                render_trade_details(results)
else:
    st.info("👈 選擇交易對和參數，點擊「🚀 執行回測」開始")
    st.divider()
    _sc = st.columns(3)
    _sc[0].markdown("#### 🔥 熱門回測\nBTC、ETH、SOL 永續合約")
    _sc[1].markdown("#### ⚡ 快速開始\n選擇分類 → 交易對 → 執行")
    _sc[2].markdown("#### 📊 15 種策略\n趨勢、擺盪、突破、均值回歸")
