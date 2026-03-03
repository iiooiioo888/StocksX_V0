# 策略訂閱 & 即時監控（增強版 v2.0）
# 新增功能：持倉手動操作、自動策略切換、風險管理

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time as _time
from datetime import datetime, timezone
from src.auth import UserDB
from src.data.live import get_live_price, get_current_signal, STRATEGY_LABELS
from src.config import format_price
from src.ui_common import require_login

st.set_page_config(page_title="StocksX — 策略監控", page_icon="📡", layout="wide")

# ════════════════════════════════════════════════════════════
# CSS 樣式
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
/* 全局背景 */
.stApp {background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #0f1724 100%);}

/* 指標卡片 */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1a1a2e, #1f1f3a);
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 10px 12px;
}
[data-testid="stMetricValue"] {font-size: 1.2rem !important; color: #6ea8fe !important;}
[data-testid="stMetricLabel"] {font-size: 0.7rem !important; color: #64748b !important;}

/* 持倉狀態 */
.position-long {color: #00cc96 !important; font-weight: bold;}
.position-short {color: #ef553b !important; font-weight: bold;}
.position-flat {color: #64748b !important;}

/* 按鈕優化 */
.stButton > button {
    border-radius: 6px !important;
    font-size: 0.8rem !important;
    padding: 5px 10px !important;
}
"""

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 頁面初始化
# ════════════════════════════════════════════════════════════
user = require_login()
db = UserDB()

# 頁面標題
st.markdown('<div class="page-header"><h1>📡 策略訂閱 & 即時監控</h1></div>', unsafe_allow_html=True)
st.caption("訂閱策略後，即時查看信號、持倉狀態和損益，支援手動操作和自動策略切換")

# 側邊欄
with st.sidebar:
    st.markdown(f"### 👤 {user['display_name']}")
    st.caption(f"{'👑 管理員' if user['role'] == 'admin' else '👤 用戶'}")
    st.divider()
    
    watchlist = db.get_watchlist(user["id"])
    active_count = sum(1 for w in watchlist if w.get("is_active", True))
    
    st.metric("📊 訂閱策略", f"{len(watchlist)}", delta=f"{active_count} 運作中")
    
    # 總體統計
    if watchlist:
        total_pnl = sum(w.get("pnl_pct", 0) * w.get("initial_equity", 10000) / 100 for w in watchlist)
        st.metric("💰 總 P&L", f"${total_pnl:+,.0f}")
    
    if st.button("🔄 重新整理", use_container_width=True):
        st.rerun()

# 主標籤頁
tabs = st.tabs(["📊 我的訂閱", "➕ 新增訂閱", "🤖 自動策略"])

# ════════════════════════════════════════════════════════════
# Tab 1: 新增訂閱
# ════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("### ➕ 新增策略訂閱")
    
    # 市場選擇
    col1, col2 = st.columns(2)
    with col1:
        w_market = st.radio("市場", ["₿ 加密貨幣", "🏛️ 傳統市場"], horizontal=True, key="w_mkt_radio")
    is_trad = w_market == "🏛️ 傳統市場"
    _mt = "traditional" if is_trad else "crypto"
    
    with col2:
        _cats = db.get_product_categories(_mt)
        _sel_cat = st.selectbox("分類", _cats if _cats else ["全部"], key="w_cat")
    
    # 產品選擇
    _products = db.get_products(user["id"], market_type=_mt, category=_sel_cat if _sel_cat != "全部" else "")
    _prod_options = [f"{p['symbol']} — {p['name']}" for p in _products]
    _prod_options.append("✏️ 自訂輸入")
    _sel_prod = st.selectbox("產品", _prod_options, key="w_prod")
    
    if _sel_prod == "✏️ 自訂輸入":
        ci1, ci2 = st.columns(2)
        with ci1:
            w_symbol = st.text_input("代碼", value="BTC/USDT:USDT" if not is_trad else "AAPL", key="w_sym_custom")
        with ci2:
            w_exchange = "yfinance" if is_trad else st.selectbox("交易所", ["binance", "okx", "bitget", "gate", "mexc", "htx"], key="w_ex")
    else:
        _idx = _prod_options.index(_sel_prod)
        _p = _products[_idx]
        w_symbol = _p["symbol"]
        w_exchange = _p["exchange"]
    
    st.divider()
    
    # 策略參數
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
            w_leverage = st.number_input("槓桿", value=1.0, min_value=1.0, max_value=125.0)
        
        # 策略參數
        params = {}
        if w_strategy == "sma_cross":
            p1, p2 = st.columns(2)
            params["fast"] = p1.number_input("快線", value=10, min_value=2)
            params["slow"] = p2.number_input("慢線", value=30, min_value=5)
        elif w_strategy == "rsi_signal":
            p1, p2, p3 = st.columns(3)
            params["period"] = p1.number_input("RSI 週期", value=14, min_value=5)
            params["oversold"] = p2.number_input("超賣", value=30.0)
            params["overbought"] = p3.number_input("超買", value=70.0)
        elif w_strategy == "macd_cross":
            p1, p2, p3 = st.columns(3)
            params["fast"] = p1.number_input("MACD 快", value=12, min_value=2)
            params["slow"] = p2.number_input("MACD 慢", value=26, min_value=5)
            params["signal"] = p3.number_input("信號線", value=9, min_value=2)
        elif w_strategy == "bollinger_signal":
            p1, p2 = st.columns(2)
            params["period"] = p1.number_input("週期", value=20, min_value=5)
            params["std_dev"] = p2.number_input("倍數", value=2.0, min_value=0.5)
        elif w_strategy == "supertrend":
            p1, p2 = st.columns(2)
            params["period"] = p1.number_input("週期", value=10, min_value=5)
            params["multiplier"] = p2.number_input("倍數", value=3.0, min_value=1.0)
        
        # 風險管理
        st.divider()
        st.markdown("**🛡️ 風險管理設定**")
        rm1, rm2 = st.columns(2)
        with rm1:
            stop_loss = st.number_input("停損 %", value=5.0, min_value=0.0, max_value=50.0, help="虧損達到此百分比時自動平倉")
            take_profit = st.number_input("停利 %", value=10.0, min_value=0.0, max_value=100.0, help="獲利達到此百分比時自動平倉")
        with rm2:
            trailing_stop = st.number_input("移動停損 %", value=3.0, min_value=0.0, max_value=50.0, help="從最高獲利回撤此百分比時平倉")
            max_position = st.number_input("最大持倉 %", value=100.0, min_value=10.0, max_value=100.0, help="單一策略最大資金配置")
        
        risk_params = {
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "trailing_stop": trailing_stop,
            "max_position": max_position
        }
        
        if st.form_submit_button("📡 開始訂閱", type="primary", use_container_width=True):
            db.add_watch(user["id"], w_symbol, w_exchange, w_timeframe, w_strategy, 
                        {**params, **risk_params}, w_equity, leverage=w_leverage)
            st.success(f"✅ 已訂閱 {w_symbol} × {STRATEGY_LABELS.get(w_strategy, w_strategy)}")
            st.rerun()

# ════════════════════════════════════════════════════════════
# Tab 2: 自動策略切換
# ════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("### 🤖 自動策略切換系統")
    st.caption("根據市場狀況自動切換最佳策略，提升獲利穩定性")
    
    # 創建自動策略配置
    auto_strategies = db.get_auto_strategies(user["id"])
    
    with st.form("add_auto_strategy"):
        st.markdown("**➕ 新增自動策略配置**")
        
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            auto_market = st.radio("市場", ["₿ 加密貨幣", "🏛️ 傳統市場"], horizontal=True, key="auto_mkt")
            auto_is_trad = auto_market == "🏛️ 傳統市場"
            auto_symbol = st.text_input("標的", value="BTC/USDT:USDT" if not auto_is_trad else "AAPL")
            auto_exchange = "yfinance" if auto_is_trad else st.selectbox("交易所", ["binance", "okx", "bitget"], key="auto_ex")
        
        with ac2:
            auto_timeframe = st.selectbox("週期", ["5m", "15m", "1h", "4h", "1d"], index=2)
            auto_equity = st.number_input("配置資金", value=10000.0, step=500.0)
            auto_eval_period = st.number_input("評估週期（小時）", value=24, min_value=1, max_value=168, 
                                              help="每隔多少小時評估一次策略表現")
        
        with ac3:
            # 可選策略池
            available_strategies = st.multiselect(
                "策略池",
                list(STRATEGY_LABELS.keys()),
                default=["sma_cross", "macd_cross", "rsi_signal", "bollinger_signal"],
                format_func=lambda x: STRATEGY_LABELS.get(x, x)
            )
            auto_selection_method = st.selectbox("選擇方式", [
                ("最佳夏普比率", "sharpe"),
                ("最高報酬率", "return"),
                ("最高勝率", "winrate"),
                ("輪動策略", "rotation")
            ], format_func=lambda x: x[0])
        
        if st.form_submit_button("💾 儲存自動策略配置", use_container_width=True):
            if available_strategies:
                config = {
                    "symbol": auto_symbol,
                    "exchange": auto_exchange,
                    "timeframe": auto_timeframe,
                    "equity": auto_equity,
                    "strategies": available_strategies,
                    "selection_method": auto_selection_method[1],
                    "eval_period_hours": auto_eval_period
                }
                db.save_auto_strategy(user["id"], config)
                st.success("✅ 已儲存自動策略配置")
                st.rerun()
    
    # 顯示現有自動策略
    if auto_strategies:
        st.divider()
        st.markdown("**📋 現有自動策略配置**")
        
        for i, auto in enumerate(auto_strategies):
            with st.expander(f"🤖 {auto['symbol']} - {len(auto['config'].get('strategies', []))}個策略", expanded=False):
                config = auto.get("config", {})
                
                # 顯示配置
                c1, c2, c3 = st.columns(3)
                c1.metric("標的", config.get("symbol", "N/A"))
                c2.metric("評估週期", f"{config.get('eval_period_hours', 24)}小時")
                c3.metric("選擇方式", config.get("selection_method", "N/A"))
                
                # 策略池
                st.markdown("**策略池**")
                strategies = config.get("strategies", [])
                strat_cols = st.columns(len(strategies) if strategies else 1)
                for j, strat in enumerate(strategies):
                    strat_cols[j % len(strat_cols)].markdown(f"- {STRATEGY_LABELS.get(strat, strat)}")
                
                # 操作
                op_cols = st.columns(2)
                with op_cols[0]:
                    if st.button("▶️ 啟動", key=f"start_auto_{auto['id']}", use_container_width=True):
                        db.update_auto_strategy(auto["id"], is_active=True)
                        st.rerun()
                with op_cols[1]:
                    if st.button("🗑️ 刪除", key=f"del_auto_{auto['id']}", use_container_width=True):
                        db.delete_auto_strategy(auto["id"])
                        st.rerun()

# ════════════════════════════════════════════════════════════
# Tab 3: 我的訂閱（主監控頁面）
# ════════════════════════════════════════════════════════════
with tabs[0]:
    watchlist = db.get_watchlist(user["id"])
    
    if not watchlist:
        st.info("📭 尚無訂閱。點擊「➕ 新增訂閱」開始。")
    else:
        # 批量操作
        batch_col1, batch_col2, batch_col3 = st.columns(3)
        with batch_col1:
            if st.button("🔄 全部刷新", use_container_width=True):
                for w in watchlist:
                    if w.get("is_active", True):
                        # 觸發刷新邏輯
                        pass
                st.rerun()
        with batch_col2:
            if st.button("⏸️ 全部暫停", use_container_width=True):
                for w in watchlist:
                    if w.get("is_active", True):
                        db.toggle_watch(w["id"])
                st.rerun()
        with batch_col3:
            if st.button("▶️ 全部啟用", use_container_width=True):
                for w in watchlist:
                    if not w.get("is_active", True):
                        db.toggle_watch(w["id"])
                st.rerun()
        
        st.divider()
        
        # 訂閱列表
        for w in watchlist:
            s_label = STRATEGY_LABELS.get(w["strategy"], w["strategy"])
            status_icon = "🟢" if w.get("is_active", True) else "⏸️"

            # 計算數據
            _w_equity = w.get("initial_equity", 10000)
            _w_pnl = w.get("pnl_pct", 0)
            _w_pos = w.get("position", 0)
            
            # 取得已實現 P&L
            _w_stats = db.get_trade_stats(w["id"])
            _w_realized_pnl = _w_stats.get("total_pnl", 0)  # 已實現 P&L（美元）
            
            # 計算未實現 P&L（美元）
            _w_unrealized_profit = _w_equity * (_w_pnl / 100) if _w_pos != 0 else 0
            
            # 帳戶價值 = 初始資金 + 已實現 P&L + 未實現 P&L
            _w_value = _w_equity + _w_realized_pnl + _w_unrealized_profit
            _w_total_pnl_pct = (_w_value - _w_equity) / _w_equity * 100 if _w_equity > 0 else 0
            
            _w_sig = {1: "🟢做多", -1: "🔴做空", 0: "⚪觀望"}.get(w.get("last_signal", 0), "⚪觀望")
            _w_pnl_str = f"{'🟢' if _w_total_pnl_pct > 0 else '🔴' if _w_total_pnl_pct < 0 else '⚪'}{_w_total_pnl_pct:+.2f}%"

            # 標題
            _header = f"{status_icon} **{w['symbol']}** × {s_label} | {_w_sig} | 💰${_w_value:,.0f} | {_w_pnl_str}"
            
            with st.expander(_header, expanded=False):
                # 刷新數據
                if w.get("is_active", True):
                    with st.spinner(f"更新 {w['symbol']}…"):
                        live = get_live_price(w["symbol"], w["exchange"])
                        sig_data = get_current_signal(
                            w["symbol"], w["exchange"], w["timeframe"],
                            w["strategy"], w.get("strategy_params", {})
                        )
                        
                        if live:
                            price = live["price"]
                            new_signal = sig_data.get("signal", 0)
                            old_position = w.get("position", 0)
                            entry_price = w.get("entry_price", 0)
                            _eq = w.get("initial_equity", 10000)
                            
                            # 風險管理參數
                            risk_params = w.get("strategy_params", {})
                            stop_loss = risk_params.get("stop_loss", 5.0)
                            take_profit = risk_params.get("take_profit", 10.0)
                            
                            # 檢查停損/停利
                            if old_position != 0 and entry_price > 0:
                                current_pnl = (price - entry_price) / entry_price * old_position * 100
                                
                                # 停損檢查
                                if current_pnl <= -stop_loss:
                                    st.toast(f"🛑 {w['symbol']} 觸發停損！P&L: {current_pnl:+.2f}%", icon="🛑")
                                    new_signal = 0  # 強制平倉
                                
                                # 停利檢查
                                if current_pnl >= take_profit:
                                    st.toast(f"✅ {w['symbol']} 觸發停利！P&L: {current_pnl:+.2f}%", icon="✅")
                                    new_signal = 0  # 強制平倉
                            
                            # 持倉更新邏輯（簡化）
                            if old_position == 0 and new_signal != 0:
                                entry_price = price
                                old_position = new_signal
                                db.log_trade(w["id"], user["id"], w["symbol"], "開倉",
                                           new_signal, price, _eq, _eq, reason=f"信號 → {'做多' if new_signal == 1 else '做空'}")
                            elif old_position != 0 and new_signal != old_position:
                                if entry_price > 0:
                                    pnl = (price - entry_price) / entry_price * old_position * 100
                                    _fee_rate = 0.05
                                    _cost = _fee_rate * 2
                                    _net_pnl = pnl - _cost
                                    _pnl_amt = _eq * _net_pnl / 100
                                    
                                    db.log_trade(w["id"], user["id"], w["symbol"], "平倉",
                                               old_position, price, _eq, _eq + _pnl_amt,
                                               round(_net_pnl, 2), round(_pnl_amt, 2),
                                               reason=f"平倉 P&L:{_net_pnl:+.2f}%")
                                
                                entry_price = price if new_signal != 0 else 0
                                old_position = new_signal
                            
                            # 計算當前 P&L
                            pnl = 0.0
                            if old_position != 0 and entry_price > 0:
                                pnl = (price - entry_price) / entry_price * old_position * 100
                            
                            # 更新資料庫
                            db.update_watch(w["id"],
                                          last_check=_time.time(), last_signal=new_signal,
                                          last_price=price, entry_price=entry_price,
                                          position=old_position, pnl_pct=round(pnl, 4))
                            
                            # 更新本地數據
                            w.update({
                                "last_price": price, "last_signal": new_signal,
                                "entry_price": entry_price, "position": old_position, "pnl_pct": round(pnl, 4)
                            })
                
                # 顯示面板
                _equity = w.get("initial_equity", 10000)
                _pnl = w.get("pnl_pct", 0)
                _position = w.get("position", 0)
                
                # 取得已實現 P&L（從 trade_stats）
                _stats = db.get_trade_stats(w["id"])
                _realized_pnl = _stats.get("total_pnl", 0)  # 已實現 P&L（美元）
                
                # 計算未實現 P&L（美元）
                _unrealized_profit = _equity * (_pnl / 100) if _position != 0 else 0
                
                # 帳戶價值 = 初始資金 + 已實現 P&L + 未實現 P&L
                _current_value = _equity + _realized_pnl + _unrealized_profit
                
                # 總利潤 = 已實現 + 未實現
                _total_profit = _realized_pnl + _unrealized_profit

                # 主要指標
                r1, r2, r3 = st.columns(3)
                r1.metric("💰 即時價格", format_price(w.get("last_price", 0)) if w.get("last_price") else "—")
                sig_text = {1: "🟢 做多", -1: "🔴 做空", 0: "⚪ 觀望"}.get(w.get("last_signal", 0), "⚪ 觀望")
                r2.metric("📡 當前信號", sig_text)
                pos_text = {1: "🟢 多頭", -1: "🔴 空頭", 0: "⬜ 空倉"}.get(_position, "⬜ 空倉")
                pos_class = "position-long" if _position == 1 else "position-short" if _position == -1 else "position-flat"
                # 使用 markdown 渲染 HTML 而不是 metric
                r3.markdown(f'<div class="metric-card"><div style="font-size:0.75rem;color:#64748b;">📊 持倉狀態</div><div class="{pos_class}" style="font-size:1.2rem;font-weight:700;">{pos_text}</div></div>', unsafe_allow_html=True)

                # 帳戶價值（包含已實現和未實現 P&L）
                v1, v2, v3, v4 = st.columns(4)
                _val_color = "normal" if _total_profit >= 0 else "inverse"
                v1.metric("🏦 帳戶價值", f"${_current_value:,.2f}", delta=f"{_total_profit:+,.2f}", delta_color=_val_color)
                
                # 分開顯示已實現和未實現 P&L
                v2.metric("💹 未實現 P&L", f"{_pnl:+.2f}%", delta=f"${_unrealized_profit:+,.2f}", delta_color=_val_color)
                
                # 新增已實現 P&L 顯示
                realized_color = "normal" if _realized_pnl >= 0 else "inverse"
                v3.metric("✅ 已實現 P&L", f"${_realized_pnl:+,.2f}", delta="已平倉利潤", delta_color=realized_color)
                
                entry = w.get("entry_price", 0)
                v4.metric("📍 進場價", format_price(entry) if entry else "—")
                
                # 手動操作按鈕
                st.divider()
                st.markdown("**🎯 手動持倉操作**")
                manual_cols = st.columns(4)
                
                with manual_cols[0]:
                    if st.button("🟢 做多", key=f"long_{w['id']}", use_container_width=True):
                        # 平空倉並開多倉
                        if _position == -1:
                            # 先平空倉
                            pnl = (entry - w.get("last_price", entry)) / entry * 100 if entry > 0 else 0
                            db.log_trade(w["id"], user["id"], w["symbol"], "平倉",
                                       -1, w.get("last_price", entry), _equity, _equity * (1 + pnl/100),
                                       reason="手動平倉")
                        # 開多倉
                        db.update_watch(w["id"], position=1, entry_price=w.get("last_price", 0),
                                      last_signal=1, pnl_pct=0)
                        db.log_trade(w["id"], user["id"], w["symbol"], "開倉",
                                   1, w.get("last_price", 0), _equity, _equity, reason="手動做多")
                        st.success(f"✅ {w['symbol']} 做多 @ {format_price(w.get('last_price', 0))}")
                        st.rerun()
                
                with manual_cols[1]:
                    if st.button("🔴 做空", key=f"short_{w['id']}", use_container_width=True):
                        # 平多倉並開空倉
                        if _position == 1:
                            pnl = (w.get("last_price", entry) - entry) / entry * 100 if entry > 0 else 0
                            db.log_trade(w["id"], user["id"], w["symbol"], "平倉",
                                       1, w.get("last_price", entry), _equity, _equity * (1 + pnl/100),
                                       reason="手動平倉")
                        # 開空倉
                        db.update_watch(w["id"], position=-1, entry_price=w.get("last_price", 0),
                                      last_signal=-1, pnl_pct=0)
                        db.log_trade(w["id"], user["id"], w["symbol"], "開倉",
                                   -1, w.get("last_price", 0), _equity, _equity, reason="手動做空")
                        st.success(f"✅ {w['symbol']} 做空 @ {format_price(w.get('last_price', 0))}")
                        st.rerun()
                
                with manual_cols[2]:
                    if st.button("⚪ 平倉/觀望", key=f"flat_{w['id']}", use_container_width=True):
                        if _position != 0:
                            pnl = (w.get("last_price", entry) - entry) / entry * _position * 100 if entry > 0 else 0
                            db.log_trade(w["id"], user["id"], w["symbol"], "平倉",
                                       _position, w.get("last_price", entry), _equity, _equity * (1 + pnl/100),
                                       reason="手動平倉")
                        db.update_watch(w["id"], position=0, entry_price=0, last_signal=0, pnl_pct=0)
                        st.success(f"✅ {w['symbol']} 已平倉")
                        st.rerun()
                
                with manual_cols[3]:
                    if st.button("🔄 刷新此策略", key=f"refresh_{w['id']}", use_container_width=True):
                        st.rerun()
                
                # 走勢圖表
                st.divider()
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
                            _signals = _strat_mod.get_signal(w["strategy"], _rows, **w.get("strategy_params", {}))
                            
                            _df = pd.DataFrame(_rows)
                            _df["time"] = pd.to_datetime(_df["timestamp"], unit="ms", utc=True)
                            _real = _df[_df.get("filled", 0) == 0] if "filled" in _df.columns else _df
                            
                            _fig = go.Figure()
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
                                xaxis=dict(gridcolor="rgba(50,50,90,0.2)"),
                                yaxis=dict(gridcolor="rgba(50,50,90,0.2)"),
                                hovermode="x unified",
                            )
                            st.plotly_chart(_fig, use_container_width=True, key=f"wchart_{w['id']}")
                    except Exception as _e:
                        st.caption(f"⚠️ 圖表載入失敗：{str(_e)[:60]}")
                
                # 策略控制
                st.divider()
                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    if st.button("⏸️ 暫停" if w.get("is_active", True) else "▶️ 啟用", key=f"toggle_{w['id']}"):
                        db.toggle_watch(w["id"])
                        st.rerun()
                with bc2:
                    if st.button("📊 前往回測", key=f"bt_{w['id']}"):
                        st.session_state["_rerun_config"] = {
                            "symbol": w["symbol"], "exchange": w["exchange"],
                            "timeframe": w["timeframe"], "strategy": w["strategy"],
                        }
                        st.switch_page("pages/2_₿_加密回測.py")
                with bc3:
                    if st.button("🗑️ 刪除", key=f"del_{w['id']}"):
                        db.delete_watch(w["id"])
                        st.rerun()
                
                # 交易統計
                _stats = db.get_trade_stats(w["id"])
                if _stats.get("total_trades", 0) > 0:
                    st.divider()
                    st.markdown("**📊 交易績效統計**")
                    _st1, _st2, _st3, _st4, _st5 = st.columns(5)
                    _st1.metric("📊 總交易", _stats.get("total_trades", 0))
                    _st2.metric("✅ 勝/負", f"{_stats.get('wins', 0)}/{_stats.get('losses', 0)}")
                    _st3.metric("🎯 勝率", f"{_stats.get('win_rate', 0):.1f}%")
                    _st4.metric("💰 累計 P&L", f"${_stats.get('total_pnl', 0):+,.0f}")
                    _st5.metric("💸 累計費用", f"${_stats.get('total_fees', 0):,.0f}")
