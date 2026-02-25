# 策略訂閱 & 即時監控
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time as _time
from datetime import datetime, timezone
from src.auth import UserDB
from src.data.live import get_live_price, get_current_signal, STRATEGY_LABELS

st.set_page_config(page_title="StocksX — 策略監控", page_icon="📡", layout="wide")
st.markdown('<p style="font-size:0.85rem;color:#888;">🏠 首頁 › 📡 策略監控</p>', unsafe_allow_html=True)

if not st.session_state.get("user"):
    st.warning("⚠️ 請先登入")
    st.page_link("pages/1_🔐_登入.py", label="🔐 前往登入", icon="🔐")
    st.stop()

user = st.session_state["user"]
db = UserDB()

st.sidebar.markdown(f"### 👤 {user['display_name']}")
st.sidebar.page_link("pages/2_📊_回測.py", label="📊 回測", icon="📊")
st.sidebar.page_link("pages/3_📜_歷史.py", label="📜 歷史", icon="📜")

st.markdown("## 📡 策略訂閱 & 即時監控")
st.caption("訂閱策略後，即時查看信號、持倉狀態和損益")

tab_watch, tab_add = st.tabs(["📊 我的訂閱", "➕ 新增訂閱"])

# ─── 新增訂閱 ───
with tab_add:
    st.subheader("➕ 新增策略訂閱")
    with st.form("add_watch"):
        wc1, wc2 = st.columns(2)
        with wc1:
            w_market = st.radio("市場", ["₿ 加密貨幣", "🏛️ 傳統市場"], horizontal=True)
            is_trad = w_market == "🏛️ 傳統市場"
            if is_trad:
                w_symbol = st.text_input("股票代碼", value="AAPL", placeholder="AAPL, 2330.TW, SPY")
                w_exchange = "yfinance"
                w_timeframe = st.selectbox("週期", ["1h", "1d"], index=1, key="w_tf")
            else:
                w_symbol = st.text_input("交易對", value="BTC/USDT:USDT")
                w_exchange = st.selectbox("交易所", ["okx", "bitget", "gate", "mexc", "htx"], key="w_ex")
                w_timeframe = st.selectbox("週期", ["5m", "15m", "1h", "4h", "1d"], index=2, key="w_tf_c")
        with wc2:
            w_strategy = st.selectbox("策略", list(STRATEGY_LABELS.keys()),
                                      format_func=lambda x: STRATEGY_LABELS.get(x, x))
            w_equity = st.number_input("模擬資金", value=10000.0, step=500.0)

            params = {}
            if w_strategy == "sma_cross":
                params["fast"] = st.number_input("快線", value=10, min_value=2)
                params["slow"] = st.number_input("慢線", value=30, min_value=5)
            elif w_strategy == "rsi_signal":
                params["period"] = st.number_input("RSI 週期", value=14, min_value=5)
                params["oversold"] = st.number_input("超賣", value=30.0)
                params["overbought"] = st.number_input("超買", value=70.0)
            elif w_strategy == "macd_cross":
                params["fast"] = st.number_input("MACD 快", value=12, min_value=2)
                params["slow"] = st.number_input("MACD 慢", value=26, min_value=5)
                params["signal"] = st.number_input("信號線", value=9, min_value=2)
            elif w_strategy == "bollinger_signal":
                params["period"] = st.number_input("週期", value=20, min_value=5)
                params["std_dev"] = st.number_input("倍數", value=2.0, min_value=0.5)

        if st.form_submit_button("📡 開始訂閱", type="primary", use_container_width=True):
            db.add_watch(user["id"], w_symbol, w_exchange, w_timeframe, w_strategy, params, w_equity)
            st.success(f"✅ 已訂閱 {w_symbol} × {STRATEGY_LABELS.get(w_strategy, w_strategy)}")
            st.rerun()

# ─── 我的訂閱 ───
with tab_watch:
    watchlist = db.get_watchlist(user["id"])

    if not watchlist:
        st.info("尚無訂閱。點擊「➕ 新增訂閱」開始。")
    else:
        # 手動刷新按鈕
        refresh = st.button("🔄 刷新即時數據", type="primary", use_container_width=True)

        for w in watchlist:
            s_label = STRATEGY_LABELS.get(w["strategy"], w["strategy"])
            status_icon = "🟢" if w["is_active"] else "⏸️"

            with st.expander(f"{status_icon} {w['symbol']} × {s_label} — {w['timeframe']}", expanded=w["is_active"]):
                if refresh and w["is_active"]:
                    with st.spinner(f"更新 {w['symbol']}…"):
                        # 即時價格
                        live = get_live_price(w["symbol"], w["exchange"])
                        # 策略信號
                        sig_data = get_current_signal(
                            w["symbol"], w["exchange"], w["timeframe"],
                            w["strategy"], w["strategy_params"],
                        )

                        if live:
                            price = live["price"]
                            # 更新持倉邏輯
                            new_signal = sig_data.get("signal", 0)
                            old_position = w["position"]
                            entry_price = w["entry_price"]
                            pnl = 0.0

                            if old_position == 0 and new_signal != 0:
                                entry_price = price
                                old_position = new_signal
                            elif old_position != 0 and new_signal != old_position:
                                if entry_price > 0:
                                    pnl = (price - entry_price) / entry_price * old_position * 100
                                if new_signal != 0:
                                    entry_price = price
                                    old_position = new_signal
                                else:
                                    entry_price = 0
                                    old_position = 0

                            if old_position != 0 and entry_price > 0:
                                pnl = (price - entry_price) / entry_price * old_position * 100

                            db.update_watch(w["id"],
                                            last_check=_time.time(), last_signal=new_signal,
                                            last_price=price, entry_price=entry_price,
                                            position=old_position, pnl_pct=round(pnl, 4))
                            w.update({"last_price": price, "last_signal": new_signal,
                                      "entry_price": entry_price, "position": old_position, "pnl_pct": round(pnl, 4)})

                # 顯示面板
                _equity = w.get("initial_equity", 10000)
                _pnl = w.get("pnl_pct", 0)
                _position = w.get("position", 0)
                _current_value = _equity * (1 + _pnl / 100) if _position != 0 else _equity
                _profit = _current_value - _equity

                r1, r2, r3 = st.columns(3)
                r1.metric("💰 即時價格", f"{w['last_price']:,.2f}" if w["last_price"] else "—")
                sig_text = {1: "🟢 做多", -1: "🔴 做空", 0: "⚪ 觀望"}.get(w.get("last_signal", 0), "⚪ 觀望")
                r2.metric("📡 當前信號", sig_text)
                pos_text = {1: "🟢 多頭", -1: "🔴 空頭", 0: "⬜ 空倉"}.get(_position, "⬜ 空倉")
                r3.metric("📊 持倉狀態", pos_text)

                v1, v2, v3, v4 = st.columns(4)
                _val_color = "normal" if _profit == 0 else ("off" if _profit < 0 else "normal")
                v1.metric("🏦 帳戶價值", f"${_current_value:,.2f}", delta=f"{_profit:+,.2f}", delta_color=_val_color)
                v2.metric("💹 未實現 P&L", f"{_pnl:+.2f}%", delta=f"${_profit:+,.2f}", delta_color=_val_color)
                entry = w.get("entry_price", 0)
                v3.metric("📍 進場價", f"{entry:,.2f}" if entry else "—")
                v4.metric("💵 初始資金", f"${_equity:,.2f}")

                # 操作按鈕
                bc1, bc2, bc3 = st.columns(3)
                if bc1.button("⏸️ 暫停" if w["is_active"] else "▶️ 啟用", key=f"toggle_{w['id']}"):
                    db.toggle_watch(w["id"])
                    st.rerun()
                if bc2.button("📊 前往回測", key=f"bt_{w['id']}"):
                    st.session_state["_rerun_config"] = {
                        "symbol": w["symbol"], "exchange": w["exchange"],
                        "timeframe": w["timeframe"], "strategy": w["strategy"],
                    }
                    st.switch_page("pages/2_📊_回測.py")
                if bc3.button("🗑️ 刪除", key=f"del_{w['id']}"):
                    db.delete_watch(w["id"])
                    st.rerun()

                # 詳細資訊
                st.caption(
                    f"交易所: {w['exchange']} | 週期: {w['timeframe']} | "
                    f"參數: {w['strategy_params']} | 模擬資金: {w['initial_equity']}"
                )
                if w.get("last_check"):
                    st.caption(f"上次更新: {datetime.fromtimestamp(w['last_check'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
