# 策略訂閱 & 即時監控（優化版 v3.0 - 即時信號）
# 優化：批量數據加載、智能快取、異步更新、即時信號計算

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time as _time
from datetime import datetime, timezone
from src.auth import UserDB
from src.config import format_price, STRATEGY_LABELS
from src.ui_common import require_login
from src.data.live_monitor import (
    batch_get_live_prices,
    batch_calculate_signals,
    get_live_price
)

st.set_page_config(page_title="StocksX — 策略監控", page_icon="📡", layout="wide")

# ════════════════════════════════════════════════════════════
# CSS 樣式
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
.stApp {background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #0f1724 100%);}

[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1a1a2e, #1f1f3a);
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 10px 12px;
}

.position-long {color: #00cc96 !important; font-weight: bold;}
.position-short {color: #ef553b !important; font-weight: bold;}
.position-flat {color: #64748b !important;}
"""

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 快取優化
# ════════════════════════════════════════════════════════════

@st.cache_data(ttl=5, show_spinner=False)
def get_watchlist_cached(user_id: int):
    """快取.watchlist 數據（5 秒）"""
    db = UserDB()
    return db.get_watchlist(user_id)

@st.cache_data(ttl=30, show_spinner=False)
def get_products_cached(user_id: int, market_type: str = "", category: str = ""):
    """快取產品數據（30 秒）"""
    db = UserDB()
    return db.get_products(user_id, market_type, category)

@st.cache_data(ttl=60, show_spinner=False)
def get_categories_cached(market_type: str = ""):
    """快取分類數據（60 秒）"""
    db = UserDB()
    return db.get_product_categories(market_type)

# ════════════════════════════════════════════════════════════
# 批量數據加載
# ════════════════════════════════════════════════════════════

def batch_get_live_prices(symbols: list) -> dict:
    """批量取得價格（減少 API 呼叫）"""
    from src.data.live import get_live_price
    prices = {}
    for symbol in symbols:
        try:
            price_data = get_live_price(symbol)
            if price_data:
                prices[symbol] = price_data
        except Exception:
            pass
    return prices

def batch_get_signals(symbols: list, strategies: list) -> dict:
    """批量取得信號（減少 API 呼叫）"""
    from src.data.live import get_current_signal
    signals = {}
    for symbol in symbols:
        for strategy in strategies:
            try:
                signal_data = get_current_signal(symbol, strategy=strategy)
                if signal_data:
                    signals[f"{symbol}_{strategy}"] = signal_data
            except Exception:
                pass
    return signals

# ════════════════════════════════════════════════════════════
# 頁面初始化
# ════════════════════════════════════════════════════════════

user = require_login()
db = UserDB()

st.markdown('<div style="margin-bottom:20px;"><h1 style="margin:0;">📡 策略訂閱 & 即時監控</h1></div>', unsafe_allow_html=True)

# 側邊欄 - 使用快取
with st.sidebar:
    st.markdown(f"### 👤 {user['display_name']}")
    st.caption(f"{'👑 管理員' if user['role'] == 'admin' else '👤 用戶'}")
    st.divider()

    # 使用快取的 watchlist
    watchlist = get_watchlist_cached(user["id"])
    active_count = sum(1 for w in watchlist if w.get("is_active", True))

    st.metric("📊 訂閱策略", f"{len(watchlist)}", delta=f"{active_count} 運作中")

    # 總體統計
    if watchlist:
        # get_watchlist 已經確保數值類型正確
        total_pnl = sum(
            w["pnl_pct"] * w["initial_equity"] / 100 
            for w in watchlist
        )
        st.metric("💰 總 P&L", f"${total_pnl:+,.0f}")

    # 重新整理按鈕（帶計時器）
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = _time.time()
    
    time_since = _time.time() - st.session_state.last_refresh
    
    if st.button(f"🔄 重新整理 ({time_since:.0f}s)", use_container_width=True):
        # 清除快取
        get_watchlist_cached.clear()
        get_products_cached.clear()
        get_categories_cached.clear()
        st.session_state.last_refresh = _time.time()
        st.rerun()

# 主標籤頁
tabs = st.tabs(["📊 我的訂閱", "➕ 新增訂閱", "🤖 自動策略"])

# ════════════════════════════════════════════════════════════
# Tab 1: 我的訂閱（優化版）
# ════════════════════════════════════════════════════════════

with tabs[0]:
    st.markdown("#### 📊 我的訂閱策略（即時監控）")
    
    # 顯示上次更新時間
    if "last_signal_update" not in st.session_state:
        st.session_state.last_signal_update = _time.time()
    
    time_since_update = _time.time() - st.session_state.last_signal_update
    st.caption(f"🕐 上次信號更新：{time_since_update:.0f}秒前")
    
    # 自動重新整理選項
    auto_refresh = st.checkbox("🔄 自動重新整理（每 10 秒）", value=True)
    
    if not watchlist:
        st.info("📭 尚無訂閱。點擊「➕ 新增訂閱」開始。")
    else:
        # 批量取得價格數據（一次性加載）
        symbols_to_load = [w["symbol"] for w in watchlist if w.get("is_active", True)]
        
        if symbols_to_load:
            with st.spinner(f"載入 {len(symbols_to_load)} 個價格..."):
                prices = batch_get_live_prices(symbols_to_load)
            
            # 批量計算信號
            with st.spinner(f"計算 {len(symbols_to_load)} 個信號..."):
                signals = batch_calculate_signals(watchlist)
            
            # 更新 session state
            st.session_state.last_signal_update = _time.time()
        else:
            prices = {}
            signals = {}
        
        # 顯示訂閱列表（優化佈局）
        for idx, w in enumerate(watchlist):
            if not w.get("is_active", True):
                continue
            
            symbol = w.get("symbol", "")
            strategy = w.get("strategy", "")
            s_label = STRATEGY_LABELS.get(strategy, strategy)
            
            # 取得價格數據
            price_data = prices.get(symbol, {})
            current_price = price_data.get("price", 0)
            
            # 如果沒有即時價格，使用資料庫數據
            if not current_price:
                current_price = float(w.get("last_price", 0) or 0)
            
            # 取得信號數據
            signal_data = signals.get(w["id"], {})
            
            # 如果有新信號，自動更新
            if signal_data:
                new_signal = signal_data.get("signal", 0)
                action = signal_data.get("action", "HOLD")
                confidence = signal_data.get("confidence", 0)
                
                # 顯示信號
                if new_signal != 0:
                    signal_emoji = "🟢" if new_signal == 1 else "🔴"
                    st.toast(f"{signal_emoji} {symbol} {strategy}: {action} (信心度：{confidence:.0f}%)")
            
            # 計算損益
            position = w["position"]
            entry_price = w["entry_price"]
            _equity = w["initial_equity"]
            
            # 確保價格是數值類型
            current_price = float(current_price or 0)
            entry_price = float(entry_price or 0)
            
            if position > 0 and entry_price > 0 and current_price > 0:
                _pnl = (current_price - entry_price) / entry_price * 100
                _profit = (current_price - entry_price) * (_equity / entry_price)
            elif position < 0 and entry_price > 0 and current_price > 0:
                _pnl = (entry_price - current_price) / entry_price * 100
                _profit = (entry_price - current_price) * (_equity / entry_price)
            else:
                _pnl = float(w.get("pnl_pct", 0) or 0)
                _profit = 0
            
            _pnl_color = "normal" if _pnl >= 0 else "inverse"
            _position_text = {1: "🟢 多頭", -1: "🔴 空頭", 0: "⚪ 空倉"}.get(position, "⚪ 空倉")
            
            # 使用 expander 優化顯示（包含帳戶號碼和即時信號）
            account_id = w.get("account_id", "N/A")
            
            # 準備信號顯示
            if signal_data:
                signal_action = signal_data.get("action", "HOLD")
                signal_confidence = signal_data.get("confidence", 0)
                signal_icon = "🟢" if signal_action == "BUY" else ("🔴" if signal_action == "SELL" else "⚪")
                signal_display = f"{signal_icon} {signal_action} ({signal_confidence:.0f}%)"
            else:
                signal_display = "計算中..."
            
            with st.expander(f"**{symbol}** × {s_label} | {_position_text} | 💰${_equity:,.0f} | {_pnl:+.2f}% | {signal_display}", expanded=False):
                # 顯示帳戶號碼
                st.caption(f"📋 帳戶號碼：`{account_id}`")
                
                # 即時價格和信號
                r1, r2, r3 = st.columns(3)
                with r1:
                    if current_price > 0:
                        st.metric("💰 即時價格", format_price(current_price))
                    else:
                        st.markdown("💰 即時價格：`等待數據...`")
                
                with r2:
                    if signal_data:
                        st.metric("📡 即時信號", signal_display)
                    else:
                        st.markdown("📡 即時信號：`計算中...`")
                
                with r3:
                    pos_class = "position-long" if position == 1 else "position-short" if position == -1 else "position-flat"
                    st.markdown(f'<div style="font-size:1.2rem;font-weight:700;" class="{pos_class}">{_position_text}</div>', unsafe_allow_html=True)
                
                # 信號詳情
                if signal_data:
                    st.divider()
                    st.markdown("**🔍 信號詳情**")
                    sig_col1, sig_col2, sig_col3 = st.columns(3)
                    
                    with sig_col1:
                        st.markdown(f"**策略**: {s_label}")
                    with sig_col2:
                        st.markdown(f"**信心度**: {signal_confidence:.1f}%")
                    with sig_col3:
                        if "rsi" in signal_data:
                            st.markdown(f"**RSI**: {signal_data['rsi']:.2f}")
                        elif "macd" in signal_data:
                            st.markdown(f"**MACD**: {signal_data['macd']:.4f}")
                        elif "upper_band" in signal_data:
                            st.markdown(f"**布林帶**: 上軌 {signal_data['upper_band']:.2f} / 下軌 {signal_data['lower_band']:.2f}")
                
                # 帳戶價值
                v1, v2, v3, v4 = st.columns(4)
                _val_color = "normal" if _profit >= 0 else "inverse"
                v1.metric("🏦 帳戶價值", f"${_equity * (1 + _pnl/100):,.2f}" if position != 0 else f"${_equity:,.2f}", delta=f"{_profit:+,.2f}", delta_color=_val_color)
                v2.metric("💹 未實現 P&L", f"{_pnl:+.2f}%", delta=f"${_profit:+,.2f}", delta_color=_val_color)
                entry = w.get("entry_price", 0)
                v3.metric("📍 進場價", format_price(entry) if entry else "—")
                v4.metric("💵 初始資金", f"${_equity:,.2f}")
                
                # 手動操作按鈕
                st.divider()
                st.markdown("**🎯 手動持倉操作**")
                manual_cols = st.columns(4)

                with manual_cols[0]:
                    if st.button("🟢 做多", key=f"long_{w['id']}_{idx}", use_container_width=True):
                        if position == -1:
                            pnl = (entry - current_price) / entry * 100 if entry > 0 else 0
                            db.log_trade(w["id"], user["id"], symbol, "平倉", -1, current_price, _equity, _equity * (1 + pnl/100), reason="手動平倉")
                        db.update_watch(w["id"], position=1, entry_price=current_price, last_signal=1, pnl_pct=0)
                        db.log_trade(w["id"], user["id"], symbol, "開倉", 1, current_price, _equity, _equity, reason="手動做多")
                        st.success(f"✅ {symbol} 做多 @ {format_price(current_price)}")
                        get_watchlist_cached.clear()
                        st.rerun()

                with manual_cols[1]:
                    if st.button("🔴 做空", key=f"short_{w['id']}_{idx}", use_container_width=True):
                        if position == 1:
                            pnl = (current_price - entry) / entry * 100 if entry > 0 else 0
                            db.log_trade(w["id"], user["id"], symbol, "平倉", 1, current_price, _equity, _equity * (1 + pnl/100), reason="手動平倉")
                        db.update_watch(w["id"], position=-1, entry_price=current_price, last_signal=-1, pnl_pct=0)
                        db.log_trade(w["id"], user["id"], symbol, "開倉", -1, current_price, _equity, _equity, reason="手動做空")
                        st.success(f"✅ {symbol} 做空 @ {format_price(current_price)}")
                        get_watchlist_cached.clear()
                        st.rerun()

                with manual_cols[2]:
                    if st.button("⚪ 平倉/觀望", key=f"flat_{w['id']}_{idx}", use_container_width=True):
                        if position != 0:
                            if position == 1:
                                pnl = (current_price - entry) / entry * 100 if entry > 0 else 0
                            else:
                                pnl = (entry - current_price) / entry * 100 if entry > 0 else 0
                            db.log_trade(w["id"], user["id"], symbol, "平倉", position, current_price, _equity, _equity * (1 + pnl/100), reason="手動平倉")
                        db.update_watch(w["id"], position=0, entry_price=0, pnl_pct=0)
                        st.success(f"✅ {symbol} 平倉")
                        get_watchlist_cached.clear()
                        st.rerun()

                with manual_cols[3]:
                    if st.button("🗑️ 刪除", key=f"del_{w['id']}_{idx}", use_container_width=True, type="secondary"):
                        db.delete_watch(w["id"])
                        st.success(f"🗑️ 已刪除 {symbol}")
                        get_watchlist_cached.clear()
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
                    
                    # 交易記錄列表
                    st.markdown("**📋 交易記錄**")
                    
                    # 取得交易記錄
                    trade_log = db.get_trade_log(w["id"], limit=50)
                    
                    if trade_log:
                        # 建立交易記錄表格
                        trade_data = []
                        for trade in trade_log:
                            # 計算數量（如果沒有記錄）
                            quantity = trade.get("quantity", 0)
                            if quantity == 0 and trade.get("price", 0) > 0:
                                # 從權益和價格估算
                                quantity = trade.get("equity_before", _equity) / trade.get("price", 1)
                            
                            trade_data.append({
                                "時間": datetime.fromtimestamp(trade.get("created_at", 0), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                                "操作": trade.get("action", ""),
                                "方向": {"1": "🟢 多頭", "-1": "🔴 空頭"}.get(str(trade.get("side", 0)), "⚪"),
                                "價格": f"${trade.get('price', 0):,.2f}",
                                "數量": f"{quantity:,.4f}",
                                "P&L": f"${trade.get('pnl_amount', 0):+.2f}" if trade.get("action") == "平倉" else "-",
                                "P&L%": f"{trade.get('pnl_pct', 0):+.2f}%" if trade.get("action") == "平倉" else "-",
                                "費用": f"${trade.get('fee', 0):.2f}" if trade.get("fee", 0) > 0 else "-",
                                "原因": trade.get("reason", "")
                            })
                        
                        # 顯示表格
                        trade_df = pd.DataFrame(trade_data)
                        
                        # 自定義樣式
                        def color_pnl(val):
                            if isinstance(val, str):
                                if val.startswith('$+'):
                                    return 'color: #00cc96'
                                elif val.startswith('$-'):
                                    return 'color: #ef553b'
                            return ''
                        
                        # 應用樣式
                        styled_df = trade_df.style.applymap(color_pnl, subset=['P&L', 'P&L%'])
                        
                        st.dataframe(
                            styled_df,
                            use_container_width=True,
                            hide_index=True,
                            height=300
                        )
                        
                        # 匯出按鈕
                        csv = trade_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 匯出交易記錄 (CSV)",
                            data=csv,
                            file_name=f"{symbol}_trade_log_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.info("暫無交易記錄")

# 自動重新整理
if auto_refresh and watchlist:
    _time.sleep(10)
    st.rerun()

# ════════════════════════════════════════════════════════════
# Tab 2: 新增訂閱（優化版）
# ════════════════════════════════════════════════════════════

with tabs[1]:
    st.markdown("### ➕ 新增策略訂閱")

    # 市場選擇 - 使用快取
    col1, col2 = st.columns(2)
    with col1:
        w_market = st.radio("市場", ["₿ 加密貨幣", "🏛️ 傳統市場"], horizontal=True, key="w_mkt_radio")
    is_trad = w_market == "🏛️ 傳統市場"
    _mt = "traditional" if is_trad else "crypto"

    with col2:
        # 使用快取的分類
        _cats = get_categories_cached(_mt)
        _sel_cat = st.selectbox("分類", _cats if _cats else ["全部"], key="w_cat")

    # 產品選擇 - 使用快取
    _products = get_products_cached(user["id"], market_type=_mt, category=_sel_cat if _sel_cat != "全部" else "")
    _prod_options = [f"{p['symbol']} — {p['name']}" for p in _products]
    _prod_options.append("✏️ 自訂輸入")

    _sel = st.selectbox("選擇產品", _prod_options, key="w_prod")
    _symbol = st.text_input("自訂", value="BTC/USDT") if _sel == "✏️ 自訂輸入" else _sel.split(" — ")[0]
    _exchange = "binance" if _mt == "crypto" else "yfinance"

    # 策略選擇
    st.markdown("#### 🧠 策略設定")
    strat_cols = st.columns(2)
    with strat_cols[0]:
        _strat = st.selectbox("策略", list(STRATEGY_LABELS.keys()), format_func=lambda x: STRATEGY_LABELS.get(x, x), key="w_strat")
    with strat_cols[1]:
        _tf = st.selectbox("時間框架", ["5m", "15m", "1h", "4h", "1d"], index=2, key="w_tf")

    # 資金設定
    st.markdown("#### 💰 資金設定")
    fund_cols = st.columns(3)
    with fund_cols[0]:
        _eq = st.number_input("初始資金", min_value=100.0, value=10000.0, step=500.0, key="w_eq")
    with fund_cols[1]:
        _lev = st.number_input("槓桿", min_value=1.0, value=1.0, max_value=125.0, step=0.5, key="w_lev")
    with fund_cols[2]:
        _fee = st.number_input("手續費%", min_value=0.0, value=0.05, step=0.01, key="w_fee")

    # 訂閱按鈕
    if st.button("📋 加入訂閱", type="primary", use_container_width=True):
        if _symbol:
            wid = db.add_watch(user["id"], _symbol, _exchange, _tf, _strat, {}, _eq, _lev)
            if wid:
                st.success(f"✅ 已新增 {_symbol} × {STRATEGY_LABELS.get(_strat, _strat)} 到訂閱列表")
                # 清除快取
                get_watchlist_cached.clear()
                st.rerun()
            else:
                st.error("❌ 新增失敗")
        else:
            st.warning("請輸入交易對")

# ════════════════════════════════════════════════════════════
# Tab 3: 自動策略
# ════════════════════════════════════════════════════════════

with tabs[2]:
    st.markdown("### 🤖 自動策略配置")
    st.info("🚧 開發中 - 預計下個版本推出")
    
    st.markdown("""
    #### 功能預告：
    
    1. **📊 策略池管理**
       - 設定多個策略自動輪動
       - 根據市場狀況自動選擇最佳策略
    
    2. **📈 績效評估**
       - 定期評估各策略表現
       - 自動切換到表現最佳的策略
    
    3. **🛡️ 風險管理**
       - 設定停損/停利點
       - 最大回撤控制
       - 倉位自動調整
    
    4. **⚡ 即時監控**
       - 24/7 自動監控市場
       - 自動執行交易
       - 即時通知推送
    """)
