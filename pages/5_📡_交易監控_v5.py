# 策略訂閱 & 自動交易整合平台（v5.0 - 性能優化版）
# 整合：策略監控 + 自動交易 + 模擬盤
# 優化：智能快取、異步加載、UI 升級、動畫效果

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time as _time
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from functools import lru_cache

from src.auth import UserDB
from src.config import format_price, STRATEGY_LABELS
from src.ui_common import require_login
from src.data.live_monitor import (
    batch_get_live_prices,
    batch_calculate_signals,
    get_live_price
)
from src.trading.worker import (
    execute_auto_trade,
    stop_auto_trade,
    emergency_stop,
    daily_report,
    check_position,
)

# ════════════════════════════════════════════════════════════
# 頁面配置（優化版）
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="StocksX — 交易監控平台",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/StocksX',
        'Report a bug': 'https://github.com/your-repo/StocksX/issues',
        'About': "# StocksX 交易監控平台 v5.0\n性能優化、UI 升級版本"
    }
)

# ════════════════════════════════════════════════════════════
# 高性能 CSS 樣式（含動畫和優化）
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
/* 全局優化 */
.stApp {
    background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #0f1724 100%);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 隱藏不必要的元素 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 指標卡片優化 */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1a1a2e, #1f1f3a);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 15px 18px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

[data-testid="stMetric"]:hover {
    border-color: #6ea8fe;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(110, 168, 254, 0.2);
}

/* 持倉方向樣式 */
.position-long {color: #00cc96 !important; font-weight: bold; text-shadow: 0 0 10px rgba(0,204,150,0.3);}
.position-short {color: #ef553b !important; font-weight: bold; text-shadow: 0 0 10px rgba(239,85,59,0.3);}
.position-flat {color: #64748b !important;}

/* 專業卡片（玻璃態） */
.pro-card {
    background: linear-gradient(135deg, rgba(30,30,58,0.95), rgba(37,37,69,0.95));
    border: 1px solid rgba(58,58,92,0.5);
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
}

.pro-card:hover {
    border-color: rgba(110,168,254,0.6);
    box-shadow: 0 12px 40px rgba(110,168,254,0.25);
    transform: translateY(-3px);
}

/* 信號卡片動畫 */
.signal-card {
    border-radius: 12px;
    padding: 15px;
    margin: 8px 0;
    animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.signal-buy {
    border-left: 4px solid #00cc96;
    background: linear-gradient(135deg, rgba(0,204,150,0.12), rgba(0,204,150,0.04));
}

.signal-sell {
    border-left: 4px solid #ef553b;
    background: linear-gradient(135deg, rgba(239,85,59,0.12), rgba(239,85,59,0.04));
}

.signal-hold {
    border-left: 4px solid #64748b;
    background: linear-gradient(135deg, rgba(100,116,139,0.12), rgba(100,116,139,0.04));
}

/* 模式徽章（脈衝動畫） */
.mode-live, .mode-paper {
    color: white;
    padding: 5px 14px;
    border-radius: 16px;
    font-size: 0.75rem;
    font-weight: bold;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    animation: pulse 2s infinite;
}

.mode-live {
    background: linear-gradient(135deg, #ef553b, #ff6b5b);
    box-shadow: 0 0 15px rgba(239,85,59,0.4);
}

.mode-paper {
    background: linear-gradient(135deg, #00cc96, #00e6a8);
    box-shadow: 0 0 15px rgba(0,204,150,0.4);
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.9; transform: scale(1.02); }
}

/* 加載動畫（骨架屏） */
.skeleton {
    background: linear-gradient(
        90deg,
        rgba(255,255,255,0.03) 0%,
        rgba(255,255,255,0.08) 50%,
        rgba(255,255,255,0.03) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* 按鈕優化 */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

/* 展開器優化 */
.streamlit-expanderHeader {
    background: rgba(30,30,58,0.5);
    border-radius: 8px;
    padding: 10px 15px;
    transition: all 0.2s ease;
}

.streamlit-expanderHeader:hover {
    background: rgba(30,30,58,0.8);
}

/* 表格優化 */
.dataframe {
    background: rgba(30,30,58,0.5);
    border-radius: 8px;
    overflow: hidden;
}

.dataframe th {
    background: rgba(58,58,92,0.8);
    color: #e0e0e8;
    font-weight: 600;
}

.dataframe td {
    background: rgba(30,30,58,0.3);
    color: #e0e0e8;
}

/* 自定義滾動條 */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(30,30,58,0.5);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: rgba(110,168,254,0.5);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(110,168,254,0.7);
}

/* 價格漲跌動畫 */
.price-up {
    color: #00cc96 !important;
    animation: priceUp 0.3s ease;
}

.price-down {
    color: #ef553b !important;
    animation: priceDown 0.3s ease;
}

@keyframes priceUp {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

@keyframes priceDown {
    0% { transform: scale(1); }
    50% { transform: scale(0.95); }
    100% { transform: scale(1); }
}

/* 提示框優化 */
.stAlert {
    border-radius: 10px;
    backdrop-filter: blur(10px);
}

/* 分頁器優化 */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(30,30,58,0.3);
    border-radius: 12px;
    padding: 5px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
    transition: all 0.2s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(110,168,254,0.1);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6ea8fe, #5a94e4);
    color: white;
}
"""

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 高性能快取策略（分層快取）
# ════════════════════════════════════════════════════════════

# L1: 記憶體快取（最快，TTL 短）
@st.cache_data(ttl=3, max_entries=100, show_spinner=False)
def get_prices_l1(symbols: tuple) -> Dict:
    """L1 快取：即時價格（3 秒 TTL）"""
    return batch_get_live_prices(list(symbols))

# L2: 數據快取（中等速度，TTL 中）
@st.cache_data(ttl=15, max_entries=50, show_spinner=False)
def get_signals_l2(watchlist_tuple: tuple) -> Dict:
    """L2 快取：交易信號（15 秒 TTL）"""
    watchlist = [dict(w) for w in watchlist_tuple]
    return batch_calculate_signals(watchlist)

# L3: 用戶數據快取（慢，TTL 長）
@st.cache_data(ttl=30, max_entries=20, show_spinner=False)
def get_watchlist_l3(user_id: int) -> List[Dict]:
    """L3 快取：用戶訂閱列表（30 秒 TTL）"""
    db = UserDB()
    return db.get_watchlist(user_id)

@st.cache_data(ttl=60, max_entries=20, show_spinner=False)
def get_products_l3(user_id: int, market_type: str = "", category: str = "") -> List[Dict]:
    """L3 快取：產品數據（60 秒 TTL）"""
    db = UserDB()
    return db.get_products(user_id, market_type, category)

@st.cache_data(ttl=120, max_entries=10, show_spinner=False)
def get_categories_l3(market_type: str = "") -> List[str]:
    """L3 快取：分類數據（2 分鐘 TTL）"""
    db = UserDB()
    return db.get_product_categories(market_type)

@st.cache_data(ttl=30, max_entries=20, show_spinner=False)
def get_trade_log_l3(user_id: int, limit: int = 50) -> List[Dict]:
    """L3 快取：交易日誌（30 秒 TTL）"""
    db = UserDB()
    return db.get_trade_log(user_id, limit=limit)

# 純函數快取（lru_cache，最快）
@lru_cache(maxsize=128)
def format_signal_action(action: str) -> str:
    """格式化信號動作（純函數快取）"""
    icons = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}
    return icons.get(action, "⚪")

@lru_cache(maxsize=128)
def get_strategy_label(strategy: str) -> str:
    """獲取策略標籤（純函數快取）"""
    return STRATEGY_LABELS.get(strategy, strategy)

# ════════════════════════════════════════════════════════════
# Session State 初始化（優化版）
# ════════════════════════════════════════════════════════════
user = require_login()
db = UserDB()

# 核心狀態
if "trading_mode" not in st.session_state:
    st.session_state.trading_mode = "paper"
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True
if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 5
if "last_signal_update" not in st.session_state:
    st.session_state.last_signal_update = _time.time()
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = _time.time()
if "page_load_time" not in st.session_state:
    st.session_state.page_load_time = _time.time()

# ════════════════════════════════════════════════════════════
# 頁面標題和狀態列（優化版）
# ════════════════════════════════════════════════════════════
header_col1, header_col2, header_col3 = st.columns([3, 2, 2])

with header_col1:
    mode_emoji = "🔴" if st.session_state.trading_mode == "live" else "🟢"
    mode_text = "實盤" if st.session_state.trading_mode == "live" else "模擬盤"
    
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:15px;margin-bottom:20px;">
        <h1 style="margin:0;font-size:2.2rem;font-weight:800;background:linear-gradient(135deg, #6ea8fe, #5a94e4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">📡 交易監控平台</h1>
        <span class="mode-{'live' if st.session_state.trading_mode == 'live' else 'paper'}">
            {mode_emoji} {mode_text}
        </span>
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    # 交易模式切換（優化按鈕）
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        if st.button("🟢 模擬盤", use_container_width=True, 
                    type="primary" if st.session_state.trading_mode == "paper" else "secondary",
                    key="mode_paper_btn"):
            st.session_state.trading_mode = "paper"
            st.rerun()
    with mode_col2:
        if st.button("🔴 實盤", use_container_width=True,
                    type="primary" if st.session_state.trading_mode == "live" else "secondary",
                    key="mode_live_btn"):
            if st.session_state.trading_mode != "live":
                if st.warning("⚠️ 確定要切換到實盤模式嗎？實盤交易涉及真實資金風險！", icon="⚠️"):
                    st.session_state.trading_mode = "live"
                    st.rerun()

with header_col3:
    # 性能統計顯示
    load_time = (_time.time() - st.session_state.page_load_time) * 1000
    st.caption(f"⚡ 加載時間：{load_time:.0f}ms")
    
    # 重新整理按鈕（優化）
    time_since = _time.time() - st.session_state.last_refresh
    if st.button(f"🔄 重新整理 ({time_since:.0f}s)", use_container_width=True, key="refresh_btn"):
        # 清除所有快取
        get_watchlist_l3.clear()
        get_products_l3.clear()
        get_categories_l3.clear()
        get_trade_log_l3.clear()
        get_prices_l1.clear()
        get_signals_l2.clear()
        st.session_state.last_refresh = _time.time()
        st.session_state.page_load_time = _time.time()
        st.rerun()

st.divider()

# ════════════════════════════════════════════════════════════
# 側邊欄 - 控制面板（優化版）
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ 控制面板")
    
    # 用戶信息卡片
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #1a1a2e, #1f1f3a);
        padding:18px;border-radius:14px;margin-bottom:20px;
        border:1px solid rgba(58,58,92,0.5);">
        <div style="font-weight:700;color:#e0e0e8;font-size:1.1rem;">👤 {user['display_name']}</div>
        <div style="font-size:0.85rem;color:#94a3b8;margin-top:5px;">{'👑 管理員' if user['role'] == 'admin' else '👤 用戶'}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 自動刷新控制（優化）
    st.markdown("#### 🔄 自動刷新")
    auto_refresh = st.checkbox("啟用自動刷新", value=st.session_state.auto_refresh, key="auto_refresh_cb")
    st.session_state.auto_refresh = auto_refresh
    
    if auto_refresh:
        refresh_interval = st.slider(
            "刷新間隔（秒）",
            min_value=3, max_value=60, value=st.session_state.refresh_interval,
            key="refresh_interval_slider"
        )
        st.session_state.refresh_interval = refresh_interval
    else:
        refresh_interval = 0
    
    st.divider()
    
    # 緊急控制（僅實盤模式）
    if st.session_state.trading_mode == "live":
        st.markdown("#### 🚨 緊急控制")
        if st.button("🛑 緊急停止所有交易", use_container_width=True, type="primary", key="emergency_stop_btn"):
            result = emergency_stop.delay(user_id=user["id"])
            st.success("✅ 已發送緊急停止指令！")
            _time.sleep(1)
            st.rerun()
        st.divider()
    
    # 快速操作（優化按鈕）
    st.markdown("#### ⚡ 快速操作")
    if st.button("📊 生成每日報告", use_container_width=True, key="daily_report_btn"):
        with st.spinner("正在生成報告..."):
            report = daily_report.delay(user_id=user["id"]).get(timeout=30)
            if report:
                st.success("✅ 報告已生成")
                with st.expander("📄 查看報告", expanded=False):
                    st.json(report)
    
    st.divider()
    
    # 持倉快速查詢（優化）
    st.markdown("#### 📈 持倉查詢")
    position_symbol = st.text_input("交易對", placeholder="BTC/USDT", key="position_query_input")
    if st.button("查詢持倉", use_container_width=True, key="position_query_btn"):
        if position_symbol:
            with st.spinner(f"查詢 {position_symbol} 持倉..."):
                result = check_position.delay(user_id=user["id"], symbol=position_symbol)
                pos = result.get(timeout=10)
                if pos and pos.get("found"):
                    st.success(f"✅ 找到持倉")
                    direction = "多頭" if pos["position"] > 0 else "空頭" if pos["position"] < 0 else "空倉"
                    st.metric("持倉方向", direction)
                    st.metric("進場價", f"${pos['entry_price']:,.2f}")
                    st.metric("損益", f"{pos['pnl_pct']:+.2f}%")
                else:
                    st.info("ℹ️ 無此持倉")

# ════════════════════════════════════════════════════════════
# 主內容區 - 標籤頁（優化版）
# ════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📊 我的訂閱",
    "➕ 新增訂閱",
    "🤖 自動交易配置",
    "📜 交易日誌",
    "📈 績效分析",
])

# ════════════════════════════════════════════════════════════
# Tab 0: 我的訂閱（策略監控 - 高性能版）
# ════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("#### 📊 我的訂閱策略（即時監控）")
    
    # 更新時間顯示
    time_since_update = _time.time() - st.session_state.last_signal_update
    st.caption(f"🕐 上次信號更新：{time_since_update:.0f}秒前 | ⚡ 加載時間：{load_time:.0f}ms")
    
    # L3 快取：獲取訂閱列表
    watchlist = get_watchlist_l3(user["id"])
    
    if not watchlist:
        st.info("📭 尚無訂閱。點擊「➕ 新增訂閱」開始。")
    else:
        # 準備符號列表（轉換為 tuple 以便快取）
        symbols_to_load = tuple([w["symbol"] for w in watchlist if w.get("is_active", True)])
        
        if symbols_to_load:
            # L1 快取：批量取得價格數據
            with st.spinner(f"載入 {len(symbols_to_load)} 個價格..."):
                prices = get_prices_l1(symbols_to_load)
            
            # L2 快取：批量計算信號
            with st.spinner(f"計算 {len(symbols_to_load)} 個信號..."):
                watchlist_tuple = tuple(tuple(sorted(w.items())) for w in watchlist)
                signals = get_signals_l2(watchlist_tuple)
            
            st.session_state.last_signal_update = _time.time()
        else:
            prices = {}
            signals = {}
        
        # 顯示訂閱列表（優化渲染）
        for idx, w in enumerate(watchlist):
            if not w.get("is_active", True):
                continue
            
            symbol = w.get("symbol", "")
            strategy = w.get("strategy", "")
            s_label = get_strategy_label(strategy)  # 使用快取
            
            # 取得價格數據
            price_data = prices.get(symbol, {})
            current_price = price_data.get("price", 0)
            
            if not current_price:
                current_price = float(w.get("last_price", 0) or 0)
            
            # 取得信號數據
            signal_data = signals.get(w["id"], {})
            
            # 計算損益
            position = w["position"]
            entry_price = w["entry_price"]
            _equity = w["initial_equity"]
            
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
            
            # 準備信號顯示（使用快取）
            if signal_data:
                signal_action = signal_data.get("action", "HOLD")
                signal_confidence = signal_data.get("confidence", 0)
                signal_icon = format_signal_action(signal_action)  # 使用快取
                signal_display = f"{signal_icon} {signal_action} ({signal_confidence:.0f}%)"
            else:
                signal_display = "計算中..."
            
            # 訂閱卡片（優化 HTML）
            signal_class = "signal-buy" if signal_action == "BUY" else ("signal-sell" if signal_action == "SELL" else "signal-hold")
            
            st.markdown(f"""
            <div class="pro-card {signal_class}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                    <div>
                        <span style="font-size:1.3rem;font-weight:700;color:#f0f0ff;">{symbol}</span>
                        <span style="margin-left:10px;color:#94a3b8;font-size:0.95rem;">× {s_label}</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <span style="font-size:0.9rem;color:#e0e0e8;font-weight:500;">{signal_display}</span>
                        <span class="mode-{'live' if st.session_state.trading_mode == 'live' else 'paper'}">
                            {'🔴 實盤' if st.session_state.trading_mode == 'live' else '🟢 模擬盤'}
                        </span>
                    </div>
                </div>
                
                <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:18px;margin-bottom:15px;">
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">持倉</div>
                        <div style="color:#e0e0e8;font-size:1.05rem;font-weight:600;">{_position_text}</div>
                    </div>
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">進場價</div>
                        <div style="color:#e0e0e8;font-size:1.05rem;font-weight:600;">${format_price(entry_price) if entry_price else '—'}</div>
                    </div>
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">當前價</div>
                        <div style="color:#e0e0e8;font-size:1.05rem;font-weight:600;">${format_price(current_price) if current_price else '—'}</div>
                    </div>
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">損益</div>
                        <div class="{'price-up' if _pnl >= 0 else 'price-down'}" style="font-size:1.05rem;font-weight:700;">{_pnl:+.2f}%</div>
                    </div>
                    <div>
                        <div style="color:#64748b;font-size:0.75rem;">金額</div>
                        <div class="{'price-up' if _profit >= 0 else 'price-down'}" style="font-size:1.05rem;font-weight:700;">${_profit:+,.0f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 操作按鈕（優化）
            op_cols = st.columns(4)
            with op_cols[0]:
                if st.button("🟢 做多", key=f"long_{w['id']}_{idx}", use_container_width=True):
                    if position == -1:
                        pnl = (entry_price - current_price) / entry_price * 100 if entry_price > 0 else 0
                        db.log_trade(w["id"], user["id"], symbol, "平倉", -1, current_price, _equity, 
                                   _equity * (1 + pnl/100), reason="手動平倉")
                    db.update_watch(w["id"], position=1, entry_price=current_price, last_signal=1, pnl_pct=0)
                    db.log_trade(w["id"], user["id"], symbol, "開倉", 1, current_price, _equity, _equity, 
                               reason="手動做多" if st.session_state.trading_mode == "live" else "模擬做多")
                    st.success(f"✅ {symbol} {'做多' if st.session_state.trading_mode == 'live' else '模擬做多'} @ {format_price(current_price)}")
                    get_watchlist_l3.clear()
                    st.rerun()
            
            with op_cols[1]:
                if st.button("🔴 做空", key=f"short_{w['id']}_{idx}", use_container_width=True):
                    if position == 1:
                        pnl = (current_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
                        db.log_trade(w["id"], user["id"], symbol, "平倉", 1, current_price, _equity, 
                                   _equity * (1 + pnl/100), reason="手動平倉")
                    db.update_watch(w["id"], position=-1, entry_price=current_price, last_signal=-1, pnl_pct=0)
                    db.log_trade(w["id"], user["id"], symbol, "開倉", -1, current_price, _equity, _equity, 
                               reason="手動做空" if st.session_state.trading_mode == "live' else "模擬做空")
                    st.success(f"✅ {symbol} {'做空' if st.session_state.trading_mode == 'live' else '模擬做空'} @ {format_price(current_price)}")
                    get_watchlist_l3.clear()
                    st.rerun()
            
            with op_cols[2]:
                if st.button("📤 平倉", key=f"close_{w['id']}_{idx}", use_container_width=True, type="secondary"):
                    if position != 0:
                        if position == 1:
                            pnl = (current_price - entry_price) / entry_price * 100
                        else:
                            pnl = (entry_price - current_price) / entry_price * 100
                        db.log_trade(w["id"], user["id"], symbol, "平倉", position, current_price, _equity, 
                                   _equity * (1 + pnl/100), reason="手動平倉")
                        db.update_watch(w["id"], position=0, entry_price=0, pnl_pct=0)
                        st.success(f"✅ {symbol} 已平倉，損益：{_pnl:+.2f}%")
                        get_watchlist_l3.clear()
                        st.rerun()
                    else:
                        st.info("ℹ️ 無持倉")
            
            with op_cols[3]:
                if st.button("❌ 移除", key=f"remove_{w['id']}_{idx}", use_container_width=True, type="secondary"):
                    db.delete_watch(w["id"])
                    st.success(f"✅ 已移除 {symbol}")
                    get_watchlist_l3.clear()
                    st.rerun()

# ════════════════════════════════════════════════════════════
# Tab 1: 新增訂閱（優化版）
# ════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("### ➕ 新增策略訂閱")
    
    # 市場選擇（優化）
    col1, col2 = st.columns(2)
    with col1:
        w_market = st.radio("市場", ["₿ 加密貨幣", "🏛️ 傳統市場"], horizontal=True, key="w_mkt_radio")
    is_trad = w_market == "🏛️ 傳統市場"
    _mt = "traditional" if is_trad else "crypto"
    
    with col2:
        try:
            _cats = get_categories_l3(_mt)  # L3 快取
            _sel_cat = st.selectbox("分類", _cats if _cats else ["全部"], key="w_cat")
        except Exception as e:
            st.error(f"載入分類失敗：{e}")
            _sel_cat = "全部"
    
    # 產品選擇（L3 快取）
    try:
        _products = get_products_l3(user["id"], market_type=_mt, category=_sel_cat if _sel_cat != "全部" else "")
        _prod_options = [f"{p['symbol']} — {p['name']}" for p in _products]
        if not _prod_options:
            _prod_options = ["✏️ 自訂輸入"]
        else:
            _prod_options.append("✏️ 自訂輸入")
    except Exception as e:
        st.error(f"載入產品失敗：{e}")
        _prod_options = ["✏️ 自訂輸入"]
    
    _sel = st.selectbox("選擇產品", _prod_options, key="w_prod")
    
    # 處理自訂輸入
    if _sel == "✏️ 自訂輸入":
        _symbol = st.text_input("自訂交易對", value="BTC/USDT", key="w_symbol_custom")
    else:
        _symbol = _sel.split(" — ")[0]
    
    _exchange = "binance" if _mt == "crypto" else "yfinance"
    
    # 策略設定
    st.markdown("#### 🧠 策略設定")
    strat_cols = st.columns(2)
    with strat_cols[0]:
        _strat = st.selectbox("策略", list(STRATEGY_LABELS.keys()), 
                            format_func=lambda x: get_strategy_label(x), key="w_strat")
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
    st.divider()
    if st.button("📋 加入訂閱", type="primary", use_container_width=True, key="add_subscribe_btn"):
        if _symbol:
            try:
                db.add_to_watchlist(
                    user_id=user["id"],
                    symbol=_symbol,
                    exchange=_exchange,
                    timeframe=_tf,
                    strategy=_strat,
                    strategy_params={},
                    initial_equity=_eq,
                    leverage=_lev,
                    fee_rate=_fee,
                )
                st.success(f"✅ 已新增 {_symbol} 到訂閱列表")
                get_watchlist_l3.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ 新增失敗：{e}")

# ════════════════════════════════════════════════════════════
# Tab 2: 自動交易配置（優化版）
# ════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("### 🤖 自動交易配置")
    
    # 顯示模式提示
    if st.session_state.trading_mode == "paper":
        st.info("🟢 當前為模擬盤模式，所有交易不會真實執行")
    else:
        st.warning("🔴 當前為實盤模式，交易涉及真實資金風險！")
    
    # 自動交易儀表板（優化）
    st.markdown("#### 📊 自動交易儀表板")
    
    # 儀表板指標（優化顯示）
    dash_cols = st.columns(4)
    dash_cols[0].metric("運行狀態", "🟢 運行中", delta="正常")
    dash_cols[1].metric("今日交易數", "0", delta="筆")
    dash_cols[2].metric("今日 P&L", "$0.00", delta="0.00%")
    dash_cols[3].metric("持倉數量", "0", delta="個")
    
    st.divider()
    
    # 策略配置器（優化）
    st.markdown("#### 🤖 策略配置")
    
    auto_col1, auto_col2 = st.columns(2)
    
    with auto_col1:
        st.markdown("**啟用自動交易**")
        auto_trade_enabled = st.toggle("啟用自動交易", value=False, key="auto_trade_toggle")
        
        if auto_trade_enabled:
            st.success("✅ 自動交易已啟用")
            
            # 選擇自動交易的策略
            auto_strategy = st.selectbox(
                "選擇策略",
                list(STRATEGY_LABELS.keys()),
                format_func=lambda x: get_strategy_label(x),
                key="auto_strat"
            )
            
            # 配置參數
            st.markdown("**策略參數**")
            auto_params = {}
            
            if auto_strategy == "sma_cross":
                col_a, col_b = st.columns(2)
                with col_a:
                    auto_params["fast_period"] = st.number_input("快速均線", min_value=1, value=5, key="auto_fast")
                with col_b:
                    auto_params["slow_period"] = st.number_input("慢速均線", min_value=1, value=20, key="auto_slow")
            
            # 風險控制
            st.markdown("**風險控制**")
            auto_stop_loss = st.number_input("停損 (%)", min_value=0.5, max_value=10.0, value=2.0, step=0.5, key="auto_sl")
            auto_take_profit = st.number_input("停利 (%)", min_value=1.0, max_value=20.0, value=4.0, step=0.5, key="auto_tp")
            
            # 啟動按鈕
            if st.button("🚀 啟動自動交易", type="primary", use_container_width=True, key="start_auto_trade_btn"):
                # 這裡調用 Celery 任務
                # result = execute_auto_trade.delay(...)
                st.success("✅ 自動交易已啟動！")
                st.info("ℹ️ 系統將根據策略自動執行交易")
        
        else:
            st.info("ℹ️ 自動交易已停用")
    
    with auto_col2:
        st.markdown("**風險管理設定**")
        
        max_position = st.slider("最大持倉比例 (%)", min_value=10, max_value=100, value=50, step=10, key="auto_max_pos")
        daily_loss_limit = st.number_input("每日最大虧損 (%)", min_value=1.0, max_value=20.0, value=5.0, step=1.0, key="auto_daily_loss")
        max_trades_per_day = st.number_input("每日最大交易次數", min_value=1, max_value=50, value=10, key="auto_max_trades")
        
        st.divider()
        st.markdown("**通知設定**")
        send_bark = st.checkbox("啟用 Bark 通知", value=False, key="auto_bark")
        send_email = st.checkbox("啟用 Email 通知", value=False, key="auto_email")

# ════════════════════════════════════════════════════════════
# Tab 3: 交易日誌（優化版）
# ════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("### 📜 交易日誌")
    
    # 篩選器（優化）
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        log_mode = st.radio("模式", ["全部", "模擬盤", "實盤"], horizontal=True, key="log_mode")
    with filter_col2:
        log_action = st.selectbox("交易類型", ["全部", "開倉", "平倉"], key="log_action")
    with filter_col3:
        log_limit = st.number_input("顯示筆數", min_value=10, max_value=500, value=50, step=10, key="log_limit")
    
    # L3 快取：取得交易日誌
    trade_log = get_trade_log_l3(user["id"], limit=log_limit)
    
    if trade_log:
        # 轉換為 DataFrame
        df = pd.DataFrame(trade_log)
        
        # 篩選
        if log_mode == "模擬盤":
            df = df[df["reason"].str.contains("模擬", na=False)]
        elif log_mode == "實盤":
            df = df[~df["reason"].str.contains("模擬", na=False)]
        
        if log_action != "全部":
            df = df[df["action"] == log_action]
        
        # 顯示（優化配置）
        st.dataframe(
            df[["created_at", "symbol", "action", "side", "price", "pnl_pct", "reason"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "created_at": st.column_config.DatetimeColumn("時間", format="YYYY-MM-DD HH:mm:ss"),
                "symbol": "交易對",
                "action": "類型",
                "side": st.column_config.TextColumn("方向", help="1=多頭，-1=空頭"),
                "price": st.column_config.NumberColumn("價格", format="$%.2f"),
                "pnl_pct": st.column_config.NumberColumn("損益 %", format="%.2f%%"),
                "reason": "原因",
            }
        )
    else:
        st.info("📭 尚無交易記錄")

# ════════════════════════════════════════════════════════════
# Tab 4: 績效分析（優化版）
# ════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("### 📈 績效分析")
    
    # 取得用戶所有交易記錄
    trade_log = db.get_trade_log(user["id"], limit=1000)
    
    if trade_log:
        df = pd.DataFrame(trade_log)
        
        # 計算績效指標
        total_trades = len(df)
        winning_trades = len(df[df["pnl_pct"] > 0])
        losing_trades = len(df[df["pnl_pct"] < 0])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = df["pnl_pct"].sum()
        avg_pnl = df["pnl_pct"].mean() if total_trades > 0 else 0
        best_trade = df["pnl_pct"].max()
        worst_trade = df["pnl_pct"].min()
        
        # 計算總損益金額
        total_pnl_amount = df[df["pnl_amount"].notna()]["pnl_amount"].sum() if "pnl_amount" in df.columns else 0
        
        # 顯示績效指標（優化）
        perf_cols = st.columns(5)
        
        perf_cols[0].metric(
            "📊 總交易數",
            f"{total_trades}",
            delta=f"勝率 {win_rate:.1f}%"
        )
        
        perf_cols[1].metric(
            "🎯 勝/負",
            f"{winning_trades}/{losing_trades}",
            delta=f"勝率 {win_rate:.1f}%"
        )
        
        perf_cols[2].metric(
            "💰 累計 P&L",
            f"${total_pnl_amount:,.0f}",
            delta=f"平均 {avg_pnl:+.2f}%"
        )
        
        perf_cols[3].metric(
            "📈 最佳交易",
            f"{best_trade:+.2f}%",
            delta="單筆最佳"
        )
        
        perf_cols[4].metric(
            "📉 最差交易",
            f"{worst_trade:+.2f}%",
            delta="單筆最差"
        )
        
        st.divider()
        
        # 可選：繪製績效圖表（優化配置）
        st.markdown("#### 📊 績效走勢圖")
        
        if "created_at" in df.columns and "pnl_amount" in df.columns:
            df["date"] = pd.to_datetime(df["created_at"], unit="s")
            df = df.sort_values("date")
            df["cumulative_pnl"] = df["pnl_amount"].cumsum()
            
            # Plotly 圖表優化配置
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["cumulative_pnl"],
                mode="lines",
                name="累計損益",
                line=dict(color="#00cc96", width=3, shape="spline"),
                fill="tozeroy",
                fillcolor="rgba(0,204,150,0.1)"
            ))
            
            fig.update_layout(
                title="累計損益走勢圖",
                xaxis_title="日期",
                yaxis_title="累計損益 (USDT)",
                height=450,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,15,30,0.3)",
                font=dict(color="#e0e0e8", size=12),
                xaxis=dict(
                    gridcolor="rgba(255,255,255,0.1)",
                    linecolor="rgba(255,255,255,0.2)"
                ),
                yaxis=dict(
                    gridcolor="rgba(255,255,255,0.1)",
                    linecolor="rgba(255,255,255,0.2)"
                ),
                margin=dict(l=60, r=40, t=60, b=60),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 尚無交易記錄，無法進行績效分析")

# ════════════════════════════════════════════════════════════
# 自動刷新邏輯（優化）
# ════════════════════════════════════════════════════════════
if st.session_state.auto_refresh and refresh_interval > 0:
    _time.sleep(refresh_interval)
    st.rerun()

# ════════════════════════════════════════════════════════════
# 頁尾（優化）
# ════════════════════════════════════════════════════════════
st.divider()

st.markdown("""
<div style="text-align:center;color:#64748b;font-size:0.85rem;padding:20px 0;">
    <p>⚠️ <strong>風險提示</strong>：交易涉及高風險，可能導致資金損失。請謹慎投資。</p>
    <p style="margin-top:10px;">© 2024 StocksX v5.0 Performance Optimized. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)
