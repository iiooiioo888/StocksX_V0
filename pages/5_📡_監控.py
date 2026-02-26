# 策略訂閱 & 即時監控
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time as _time
from datetime import datetime, timezone
from src.auth import UserDB
from src.data.live import get_live_price, get_current_signal, STRATEGY_LABELS
from src.ui_common import apply_theme, breadcrumb, require_login, sidebar_user_nav

st.set_page_config(page_title="StocksX — 策略監控", page_icon="📡", layout="wide")
apply_theme()
breadcrumb("策略監控", "📡")

user = require_login()
db = UserDB()
sidebar_user_nav(user)

st.markdown("## 📡 策略訂閱 & 即時監控")
st.caption("訂閱策略後，即時查看信號、持倉狀態和損益")

tab_watch, tab_add = st.tabs(["📊 我的訂閱", "➕ 新增訂閱"])

# ─── 新增訂閱 ───
with tab_add:
    st.subheader("➕ 新增策略訂閱")

    # 市場/分類/產品 在 form 外面，即時聯動
    _wm1, _wm2 = st.columns(2)
    with _wm1:
        w_market = st.radio("市場", ["₿ 加密貨幣", "🏛️ 傳統市場"], horizontal=True, key="w_mkt_radio")
    is_trad = w_market == "🏛️ 傳統市場"
    _mt = "traditional" if is_trad else "crypto"

    _wc1, _wc2 = st.columns(2)
    with _wc1:
        _cats = db.get_product_categories(_mt)
        _sel_cat = st.selectbox("分類", _cats if _cats else ["全部"], key="w_cat")
    with _wc2:
        _products = db.get_products(user["id"], market_type=_mt, category=_sel_cat if _sel_cat != "全部" else "")
        _prod_options = [f"{p['symbol']} — {p['name']}" for p in _products]
        _prod_options.append("✏️ 自訂輸入")
        _sel_prod = st.selectbox("產品", _prod_options, key="w_prod")

    if _sel_prod == "✏️ 自訂輸入":
        _ci1, _ci2 = st.columns(2)
        with _ci1:
            w_symbol = st.text_input("代碼", value="BTC/USDT:USDT" if not is_trad else "AAPL", key="w_sym_custom")
        with _ci2:
            w_exchange = "yfinance" if is_trad else st.selectbox("交易所", ["binance", "okx", "bitget", "gate", "mexc", "htx"], key="w_ex")
    else:
        _idx = _prod_options.index(_sel_prod)
        _p = _products[_idx]
        w_symbol = _p["symbol"]
        w_exchange = _p["exchange"]

    st.divider()

    # 策略/參數/資金 在 form 裡面
    with st.form("add_watch"):
        wc1, wc2 = st.columns(2)
        with wc1:
            st.caption(f"📌 已選：**{w_symbol}** ({w_exchange})")
            if is_trad:
                w_timeframe = st.selectbox("週期", ["1h", "1d"], index=1, key="w_tf")
            else:
                w_timeframe = st.selectbox("週期", ["5m", "15m", "1h", "4h", "1d"], index=2, key="w_tf_c")
        with wc2:
            w_strategy = st.selectbox("策略", list(STRATEGY_LABELS.keys()),
                                      format_func=lambda x: STRATEGY_LABELS.get(x, x))
            w_equity = st.number_input("模擬資金", value=10000.0, step=500.0)

        params = {}
        if w_strategy == "sma_cross":
            _p1, _p2 = st.columns(2)
            params["fast"] = _p1.number_input("快線", value=10, min_value=2)
            params["slow"] = _p2.number_input("慢線", value=30, min_value=5)
        elif w_strategy == "rsi_signal":
            _p1, _p2, _p3 = st.columns(3)
            params["period"] = _p1.number_input("RSI 週期", value=14, min_value=5)
            params["oversold"] = _p2.number_input("超賣", value=30.0)
            params["overbought"] = _p3.number_input("超買", value=70.0)
        elif w_strategy == "macd_cross":
            _p1, _p2, _p3 = st.columns(3)
            params["fast"] = _p1.number_input("MACD 快", value=12, min_value=2)
            params["slow"] = _p2.number_input("MACD 慢", value=26, min_value=5)
            params["signal"] = _p3.number_input("信號線", value=9, min_value=2)
        elif w_strategy == "bollinger_signal":
            _p1, _p2 = st.columns(2)
            params["period"] = _p1.number_input("週期", value=20, min_value=5)
            params["std_dev"] = _p2.number_input("倍數", value=2.0, min_value=0.5)

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

            _w_equity = w.get("initial_equity", 10000)
            _w_pnl = w.get("pnl_pct", 0)
            _w_pos = w.get("position", 0)
            _w_value = _w_equity * (1 + _w_pnl / 100) if _w_pos != 0 else _w_equity
            _w_sig = {1: "🟢做多", -1: "🔴做空", 0: "⚪觀望"}.get(w.get("last_signal", 0), "⚪觀望")
            _w_pnl_str = f"{'🟢' if _w_pnl > 0 else '🔴' if _w_pnl < 0 else '⚪'}{_w_pnl:+.2f}%"
            _w_price_str = f"${w['last_price']:,.2f}" if w.get("last_price") else ""

            _header = f"{status_icon} {w['symbol']} × {s_label}　|　{_w_sig}　|　💰${_w_value:,.0f}　|　{_w_pnl_str}"
            if _w_price_str:
                _header += f"　|　{_w_price_str}"

            with st.expander(_header, expanded=False):
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

                # 走勢圖表
                _show_chart = st.checkbox("📈 顯示走勢圖", value=False, key=f"chart_{w['id']}")
                if _show_chart:
                    try:
                        if w["exchange"] == "yfinance":
                            from src.data.traditional import TraditionalDataFetcher
                            _fetcher = TraditionalDataFetcher()
                        else:
                            from src.data.crypto import CryptoDataFetcher
                            _fetcher = CryptoDataFetcher(w["exchange"])
                        _until = int(_time.time() * 1000)
                        _tf_ms = {"1m": 60000, "5m": 300000, "15m": 900000, "1h": 3600000,
                                  "4h": 14400000, "1d": 86400000}.get(w["timeframe"], 3600000)
                        _since = _until - 100 * _tf_ms
                        _rows = _fetcher.get_ohlcv(w["symbol"], w["timeframe"], _since, _until, fill_gaps=True)

                        if _rows:
                            from src.backtest import strategies as _strat_mod
                            _signals = _strat_mod.get_signal(w["strategy"], _rows, **w["strategy_params"])

                            _df = pd.DataFrame(_rows)
                            _df["time"] = pd.to_datetime(_df["timestamp"], unit="ms", utc=True)
                            _real = _df[_df.get("filled", 0) == 0] if "filled" in _df.columns else _df

                            _fig = go.Figure()
                            # 收盤價線
                            _fig.add_trace(go.Scatter(
                                x=_real["time"], y=_real["close"], mode="lines", name="收盤價",
                                line=dict(color="#8888cc", width=1.5),
                            ))
                            # 進場價水平線
                            if entry and entry > 0:
                                _fig.add_hline(y=entry, line=dict(color="#FFD700", width=1, dash="dash"),
                                               annotation_text=f"進場 {entry:,.2f}",
                                               annotation_font_color="#FFD700")

                            # 信號標記
                            _sig_map = {}
                            for _si, _r in enumerate(_rows):
                                if _si < len(_signals):
                                    _sig_map[_r["timestamp"]] = _signals[_si]
                            _real_copy = _real.copy()
                            _real_copy["signal"] = _real_copy["timestamp"].map(_sig_map).fillna(0).astype(int)
                            _buys = _real_copy[(_real_copy["signal"] == 1) & (_real_copy["signal"].shift(1) != 1)]
                            _sells = _real_copy[(_real_copy["signal"] == -1) & (_real_copy["signal"].shift(1) != -1)]
                            if len(_buys) > 0:
                                _fig.add_trace(go.Scatter(
                                    x=_buys["time"], y=_buys["close"], mode="markers", name="做多",
                                    marker=dict(symbol="triangle-up", size=9, color="#26A69A"),
                                ))
                            if len(_sells) > 0:
                                _fig.add_trace(go.Scatter(
                                    x=_sells["time"], y=_sells["close"], mode="markers", name="做空",
                                    marker=dict(symbol="triangle-down", size=9, color="#EF5350"),
                                ))

                            _fig.update_layout(
                                height=280, margin=dict(l=0, r=0, t=10, b=0),
                                legend=dict(orientation="h", y=1.05), yaxis_side="right",
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,15,30,0.5)",
                                font=dict(color="#c8c8e0", size=11),
                                xaxis=dict(gridcolor="rgba(50,50,90,0.2)", range=[_real["time"].min(), _real["time"].max()]),
                                yaxis=dict(gridcolor="rgba(50,50,90,0.2)"),
                                hovermode="x unified",
                            )
                            st.plotly_chart(_fig, use_container_width=True, key=f"wchart_{w['id']}")
                    except Exception as _e:
                        st.caption(f"⚠️ 圖表載入失敗: {str(_e)[:60]}")

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
                    st.switch_page("pages/2_₿_加密回測.py")
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
