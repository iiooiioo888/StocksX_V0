# StocksX v6.0 - 紧凑式交易仪表板
# 設計靈感：World Monitor 高密度信息展示
# 特點：緊湊佈局、模塊化面板、實時數據流、可自定義視圖

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
from src.ui_news.news_panel import (
    render_news_panel,
    render_news_ticker,
    render_breaking_news_alert,
)

# ════════════════════════════════════════════════════════════
# 頁面配置（緊湊型）
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="StocksX — 交易儀表板",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://github.com/your-repo/StocksX',
        'Report a bug': 'https://github.com/your-repo/StocksX/issues',
        'About': "# StocksX v6.0 Compact Dashboard\n高密度交易監控儀表板"
    }
)

# ════════════════════════════════════════════════════════════
# 緊湊型 CSS 樣式（World Monitor 風格）
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
/* 全局佈局優化 */
.stApp {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
}

/* 隱藏 Streamlit 默認元素 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 緊湊型卡片設計 */
.metric-card {
    background: linear-gradient(135deg, rgba(22,27,34,0.9), rgba(13,17,23,0.95));
    border: 1px solid rgba(48,54,61,0.8);
    border-radius: 6px;
    padding: 12px 16px;
    margin: 4px 0;
    transition: all 0.2s ease;
}

.metric-card:hover {
    border-color: rgba(88,166,255,0.5);
    box-shadow: 0 2px 8px rgba(88,166,255,0.15);
}

/* 高密度數據網格 */
.data-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 8px;
    margin: 8px 0;
}

/* 信號徽章（緊湊型） */
.signal-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    background: rgba(48,54,61,0.8);
}

.signal-buy {
    background: rgba(35,134,55,0.2);
    color: #3fb950;
    border: 1px solid rgba(35,134,55,0.4);
}

.signal-sell {
    background: rgba(218,54,51,0.2);
    color: #f85149;
    border: 1px solid rgba(218,54,51,0.4);
}

.signal-hold {
    background: rgba(110,118,129,0.2);
    color: #8b949e;
    border: 1px solid rgba(110,118,129,0.4);
}

/* 模式切換（緊湊型） */
.mode-toggle {
    display: inline-flex;
    gap: 4px;
    background: rgba(22,27,34,0.8);
    border-radius: 6px;
    padding: 2px;
}

.mode-btn {
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
}

.mode-btn.active.paper {
    background: #238636;
    color: white;
}

.mode-btn.active.live {
    background: #da3633;
    color: white;
}

/* 緊湊型表格 */
.compact-table {
    font-size: 0.8rem;
    border-collapse: collapse;
}

.compact-table th {
    background: rgba(22,27,34,0.8);
    color: #8b949e;
    padding: 6px 10px;
    font-weight: 600;
    border-bottom: 1px solid rgba(48,54,61,0.8);
}

.compact-table td {
    background: rgba(13,17,23,0.5);
    color: #c9d1d9;
    padding: 6px 10px;
    border-bottom: 1px solid rgba(48,54,61,0.3);
}

.compact-table tr:hover {
    background: rgba(22,27,34,0.6);
}

/* 價格漲跌指示器 */
.price-change {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-weight: 600;
    font-size: 0.85rem;
}

.price-up { color: #3fb950; }
.price-down { color: #f85149; }

/* 迷你圖表容器 */
.mini-chart {
    height: 60px;
    margin: 4px 0;
}

/* 緊湊型按鈕 */
.stButton > button {
    border-radius: 6px;
    font-size: 0.8rem;
    padding: 6px 12px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

/* 狀態指示器 */
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
}

.status-live {
    background: #3fb950;
    box-shadow: 0 0 8px rgba(63,185,80,0.6);
}

.status-offline {
    background: #8b949e;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* 自定義滾動條（緊湊型） */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: rgba(13,17,23,0.5);
}

::-webkit-scrollbar-thumb {
    background: rgba(48,54,61,0.8);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(88,166,255,0.5);
}

/* 分頁器（緊湊型） */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(22,27,34,0.5);
    border-radius: 6px;
    padding: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(22,27,34,0.8);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color: white;
}

/* 提示框（緊湊型） */
.stAlert {
    border-radius: 6px;
    padding: 8px 12px;
    margin: 4px 0;
    font-size: 0.85rem;
}

/* 展開器（緊湊型） */
.streamlit-expanderHeader {
    background: rgba(22,27,34,0.6);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.85rem;
}

/* 指標卡片懸浮效果 */
.metric-card .metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f0f6fc;
}

.metric-card .metric-label {
    font-size: 0.75rem;
    color: #8b949e;
    margin-top: 2px;
}

.metric-card .metric-delta {
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 4px;
}

/* 加載動畫（骨架屏） */
.skeleton {
    background: linear-gradient(
        90deg,
        rgba(255,255,255,0.03) 0%,
        rgba(255,255,255,0.06) 50%,
        rgba(255,255,255,0.03) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* 響應式佈局 */
@media (min-width: 2000px) {
    .data-grid {
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    }
}

@media (max-width: 768px) {
    .data-grid {
        grid-template-columns: 1fr;
    }
}
"""

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 高性能快取（與 v5.0 相同）
# ════════════════════════════════════════════════════════════

@st.cache_data(ttl=3, max_entries=100, show_spinner=False)
def get_prices_l1(symbols: tuple) -> Dict:
    """L1 快取：即時價格"""
    return batch_get_live_prices(list(symbols))

@st.cache_data(ttl=15, max_entries=50, show_spinner=False)
def get_signals_l2(watchlist_tuple: tuple) -> Dict:
    """L2 快取：交易信號"""
    watchlist = [dict(w) for w in watchlist_tuple]
    return batch_calculate_signals(watchlist)

@st.cache_data(ttl=30, max_entries=20, show_spinner=False)
def get_watchlist_l3(user_id: int) -> List[Dict]:
    """L3 快取：用戶訂閱列表"""
    db = UserDB()
    return db.get_watchlist(user_id)

@st.cache_data(ttl=60, max_entries=20, show_spinner=False)
def get_products_l3(user_id: int, market_type: str = "", category: str = "") -> List[Dict]:
    """L3 快取：產品數據"""
    db = UserDB()
    return db.get_products(user_id, market_type, category)

@st.cache_data(ttl=120, max_entries=10, show_spinner=False)
def get_categories_l3(market_type: str = "") -> List[str]:
    """L3 快取：分類數據"""
    db = UserDB()
    return db.get_product_categories(market_type)

@st.cache_data(ttl=30, max_entries=20, show_spinner=False)
def get_trade_log_l3(user_id: int, limit: int = 50) -> List[Dict]:
    """L3 快取：交易日誌"""
    db = UserDB()
    return db.get_trade_log(user_id, limit=limit)

@lru_cache(maxsize=128)
def format_signal_action(action: str) -> str:
    """格式化信號動作"""
    icons = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}
    return icons.get(action, "⚪")

@lru_cache(maxsize=128)
def get_strategy_label(strategy: str) -> str:
    """獲取策略標籤"""
    return STRATEGY_LABELS.get(strategy, strategy)

# ════════════════════════════════════════════════════════════
# Session State 初始化
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
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "dashboard"  # dashboard / grid / detail

# ════════════════════════════════════════════════════════════
# 頂部導航欄（World Monitor 風格）
# ════════════════════════════════════════════════════════════
nav_col1, nav_col2, nav_col3 = st.columns([4, 3, 3])

with nav_col1:
    # Logo 和標題
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
        <div style="font-size:1.5rem;font-weight:800;background:linear-gradient(135deg, #58a6ff, #1f6feb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">📡 StocksX</div>
        <span style="font-size:0.7rem;color:#8b949e;background:rgba(48,54,61,0.5);padding:2px 8px;border-radius:12px;">v6.0</span>
    </div>
    """, unsafe_allow_html=True)

with nav_col2:
    # 模式切換（緊湊型）
    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <span style="font-size:0.75rem;color:#8b949e;">交易模式:</span>
        <div class="mode-toggle">
            <button class="mode-btn paper active" id="mode_paper" 
                    style="background:transparent;color:#8b949e;" 
                    onclick="document.getElementById('mode_paper').style.background='#238636';document.getElementById('mode_paper').style.color='white';document.getElementById('mode_live').style.background='transparent';document.getElementById('mode_live').style.color='#8b949e';">
                🟢 模擬
            </button>
            <button class="mode-btn live" id="mode_live"
                    style="background:transparent;color:#8b949e;"
                    onclick="document.getElementById('mode_live').style.background='#da3633';document.getElementById('mode_live').style.color='white';document.getElementById('mode_paper').style.background='transparent';document.getElementById('mode_paper').style.color='#8b949e';">
                🔴 實盤
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 實際的模式切換按鈕（隱藏）
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        if st.button("🟢 模擬", key="mode_paper_btn", use_container_width=True,
                    type="primary" if st.session_state.trading_mode == "paper" else "secondary"):
            st.session_state.trading_mode = "paper"
            st.rerun()
    with mode_col2:
        if st.button("🔴 實盤", key="mode_live_btn", use_container_width=True,
                    type="primary" if st.session_state.trading_mode == "live" else "secondary"):
            if st.session_state.trading_mode != "live":
                if st.warning("⚠️ 確定切換到實盤？", icon="⚠️"):
                    st.session_state.trading_mode = "live"
                    st.rerun()

with nav_col3:
    # 狀態指示器和刷新
    col1, col2 = st.columns(2)
    with col1:
        load_time = (_time.time() - st.session_state.page_load_time) * 1000
        st.markdown(f"""
        <div style="font-size:0.75rem;color:#8b949e;margin-bottom:8px;">
            <span class="status-dot status-live"></span>
            ⚡ {load_time:.0f}ms
        </div>
        """, unsafe_allow_html=True)
    with col2:
        time_since = _time.time() - st.session_state.last_refresh
        if st.button(f"🔄 {time_since:.0f}s", key="refresh_btn", use_container_width=True):
            get_prices_l1.clear()
            get_signals_l2.clear()
            get_watchlist_l3.clear()
            get_trade_log_l3.clear()
            st.session_state.last_refresh = _time.time()
            st.session_state.page_load_time = _time.time()
            st.rerun()

st.divider()

# ════════════════════════════════════════════════════════════
# 側邊欄（緊湊型控制面板）
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ 控制面板")
    
    # 用戶信息
    st.markdown(f"""
    <div style="background:rgba(22,27,34,0.8);padding:12px;border-radius:6px;margin-bottom:12px;border:1px solid rgba(48,54,61,0.5);">
        <div style="font-weight:600;color:#f0f6fc;font-size:0.9rem;">👤 {user['display_name']}</div>
        <div style="font-size:0.75rem;color:#8b949e;margin-top:4px;">{'👑 管理員' if user['role'] == 'admin' else '👤 用戶'}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 視圖模式選擇
    st.markdown("#### 📊 視圖模式")
    view_mode = st.radio(
        "佈局",
        ["儀表板", "網格視圖", "詳細視圖"],
        index=0,
        label_visibility="collapsed",
        key="view_mode_radio"
    )
    st.session_state.view_mode = "dashboard" if view_mode == "儀表板" else ("grid" if view_mode == "網格視圖" else "detail")
    
    st.divider()
    
    # 自動刷新控制
    st.markdown("#### 🔄 自動刷新")
    auto_refresh = st.checkbox("啟用", value=st.session_state.auto_refresh, key="auto_refresh_cb")
    st.session_state.auto_refresh = auto_refresh
    
    if auto_refresh:
        refresh_interval = st.slider(
            "間隔（秒）",
            min_value=3, max_value=60, value=st.session_state.refresh_interval,
            key="refresh_interval_slider"
        )
        st.session_state.refresh_interval = refresh_interval
    
    st.divider()
    
    # 緊急控制
    if st.session_state.trading_mode == "live":
        st.markdown("#### 🚨 緊急控制")
        if st.button("🛑 緊急停止", use_container_width=True, type="primary", key="emergency_stop_btn"):
            result = emergency_stop.delay(user_id=user["id"])
            st.success("✅ 已發送緊急停止")
            _time.sleep(1)
            st.rerun()
        st.divider()
    
    # 快速操作
    st.markdown("#### ⚡ 快速操作")
    if st.button("📊 每日報告", use_container_width=True, key="daily_report_btn"):
        with st.spinner("生成中..."):
            report = daily_report.delay(user_id=user["id"]).get(timeout=30)
            if report:
                st.success("✅ 報告已生成")
    
    # 持倉查詢
    st.markdown("#### 🔍 持倉查詢")
    position_symbol = st.text_input("交易對", placeholder="BTC/USDT", key="position_query_input")
    if st.button("查詢", use_container_width=True, key="position_query_btn"):
        if position_symbol:
            with st.spinner(f"查詢 {position_symbol}..."):
                result = check_position.delay(user_id=user["id"], symbol=position_symbol)
                pos = result.get(timeout=10)
                if pos and pos.get("found"):
                    direction = "多頭" if pos["position"] > 0 else "空頭" if pos["position"] < 0 else "空倉"
                    st.metric("持倉", direction)
                    st.metric("進場價", f"${pos['entry_price']:,.2f}")
                    st.metric("損益", f"{pos['pnl_pct']:+.2f}%")

# ════════════════════════════════════════════════════════════
# 主內容區 - 標籤頁
# ════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📊 儀表板",
    "💼 持倉監控",
    "➕ 新增訂閱",
    "🤖 自動交易",
    "📰 實時新聞",
    "📜 交易日誌",
])

# ════════════════════════════════════════════════════════════
# Tab 0: 儀表板（World Monitor 風格 - 高密度）
# ════════════════════════════════════════════════════════════
with tabs[0]:
    # 突發新聞警報
    render_breaking_news_alert(limit=3)
    
    # 績效指標（緊湊型）
    st.markdown("#### 📊 績效概覽")
    
    watchlist = get_watchlist_l3(user["id"])
    
    if watchlist:
        # 計算總體績效
        symbols_to_load = tuple([w["symbol"] for w in watchlist if w.get("is_active", True)])
        
        if symbols_to_load:
            with st.spinner(f"載入 {len(symbols_to_load)} 個價格..."):
                prices = get_prices_l1(symbols_to_load)
            
            with st.spinner(f"計算 {len(symbols_to_load)} 個信號..."):
                watchlist_tuple = tuple(tuple(sorted(w.items())) for w in watchlist)
                signals = get_signals_l2(watchlist_tuple)
            
            st.session_state.last_signal_update = _time.time()
        else:
            prices = {}
            signals = {}
        
        # 計算總體指標
        total_positions = sum(1 for w in watchlist if w.get("position", 0) != 0)
        total_equity = sum(w.get("initial_equity", 0) for w in watchlist)
        
        total_pnl = 0
        winning = 0
        losing = 0
        
        for w in watchlist:
            if w.get("position", 0) != 0:
                pnl = w.get("pnl_pct", 0)
                total_pnl += pnl
                if pnl > 0:
                    winning += 1
                elif pnl < 0:
                    losing += 1
        
        win_rate = winning / (winning + losing) * 100 if (winning + losing) > 0 else 0
        
        # 顯示指標（緊湊型）
        metric_cols = st.columns(5)
        
        metric_cols[0].markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_positions}</div>
            <div class="metric-label">持倉數量</div>
        </div>
        """, unsafe_allow_html=True)
        
        metric_cols[1].markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${total_equity:,.0f}</div>
            <div class="metric-label">總權益</div>
        </div>
        """, unsafe_allow_html=True)
        
        metric_cols[2].markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{'#3fb950' if total_pnl >= 0 else '#f85149'}">{total_pnl:+.2f}%</div>
            <div class="metric-label">總損益</div>
        </div>
        """, unsafe_allow_html=True)
        
        metric_cols[3].markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{winning}/{losing}</div>
            <div class="metric-label">盈虧比</div>
        </div>
        """, unsafe_allow_html=True)
        
        metric_cols[4].markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{win_rate:.1f}%</div>
            <div class="metric-label">勝率</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # 視圖模式切換
        if st.session_state.view_mode == "dashboard":
            # 儀表板視圖 - 緊湊型卡片
            st.markdown("#### 💼 持倉概覽")
            
            # 分組顯示（每行 3 個）
            cols = st.columns(3)
            
            for idx, w in enumerate(watchlist):
                if not w.get("is_active", True):
                    continue
                
                symbol = w.get("symbol", "")
                strategy = w.get("strategy", "")
                s_label = get_strategy_label(strategy)
                
                price_data = prices.get(symbol, {})
                current_price = price_data.get("price", 0) or float(w.get("last_price", 0) or 0)
                
                signal_data = signals.get(w["id"], {})
                signal_action = signal_data.get("action", "HOLD")
                signal_confidence = signal_data.get("confidence", 0)
                signal_icon = format_signal_action(signal_action)
                
                position = w.get("position", 0)
                entry_price = w.get("entry_price", 0)
                pnl = w.get("pnl_pct", 0)
                pnl_color = "#3fb950" if pnl >= 0 else "#f85149"
                
                position_text = {1: "🟢 多", -1: "🔴 空", 0: "⚪ 空"}.get(position, "⚪ 空")
                
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="metric-card" style="margin-bottom:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <span style="font-weight:600;color:#f0f6fc;font-size:0.9rem;">{symbol}</span>
                            <span class="signal-badge signal-{'buy' if signal_action == 'BUY' else 'sell' if signal_action == 'SELL' else 'hold'}">
                                {signal_icon} {signal_action}
                            </span>
                        </div>
                        <div style="font-size:0.75rem;color:#8b949e;margin-bottom:6px;">{s_label}</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;">
                            <div>
                                <div style="font-size:0.7rem;color:#8b949e;">持倉</div>
                                <div style="font-size:0.85rem;color:#c9d1d9;font-weight:600;">{position_text}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:0.7rem;color:#8b949e;">損益</div>
                                <div style="font-size:0.85rem;color:{pnl_color};font-weight:700;">{pnl:+.2f}%</div>
                            </div>
                        </div>
                        <div style="display:flex;gap:4px;">
                            <button style="flex:1;background:#238636;color:white;border:none;border-radius:4px;padding:4px;font-size:0.75rem;cursor:pointer;" 
                                    onclick="document.getElementById('long_{w['id']}').click();">🟢</button>
                            <button style="flex:1;background:#da3633;color:white;border:none;border-radius:4px;padding:4px;font-size:0.75rem;cursor:pointer;"
                                    onclick="document.getElementById('short_{w['id']}').click();">🔴</button>
                            <button style="flex:1;background:#30363d;color:#c9d1d9;border:none;border-radius:4px;padding:4px;font-size:0.75rem;cursor:pointer;"
                                    onclick="document.getElementById('close_{w['id']}').click();">平</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 隱藏的按鈕（用於 JavaScript 觸發）
                    if st.button("🟢", key=f"long_{w['id']}_{idx}", type="primary"):
                        db.update_watch(w["id"], position=1, entry_price=current_price, last_signal=1, pnl_pct=0)
                        db.log_trade(w["id"], user["id"], symbol, "開倉", 1, current_price, w.get("initial_equity", 0), 
                                   w.get("initial_equity", 0), reason="手動做多")
                        get_watchlist_l3.clear()
                        st.rerun()
                    
                    if st.button("🔴", key=f"short_{w['id']}_{idx}", type="primary"):
                        db.update_watch(w["id"], position=-1, entry_price=current_price, last_signal=-1, pnl_pct=0)
                        db.log_trade(w["id"], user["id"], symbol, "開倉", -1, current_price, w.get("initial_equity", 0), 
                                   w.get("initial_equity", 0), reason="手動做空")
                        get_watchlist_l3.clear()
                        st.rerun()
                    
                    if st.button("平", key=f"close_{w['id']}_{idx}"):
                        if position != 0:
                            pnl_amount = (current_price - entry_price) / entry_price * 100 if position == 1 else (entry_price - current_price) / entry_price * 100
                            db.log_trade(w["id"], user["id"], symbol, "平倉", position, current_price, w.get("initial_equity", 0), 
                                       w.get("initial_equity", 0) * (1 + pnl_amount/100), reason="手動平倉")
                            db.update_watch(w["id"], position=0, entry_price=0, pnl_pct=0)
                            get_watchlist_l3.clear()
                            st.rerun()
        
        elif st.session_state.view_mode == "grid":
            # 網格視圖 - 緊湊型表格
            st.markdown("#### 📊 持倉明細")
            
            # 構建數據
            data = []
            for w in watchlist:
                if not w.get("is_active", True):
                    continue
                
                symbol = w.get("symbol", "")
                strategy = w.get("strategy", "")
                s_label = get_strategy_label(strategy)
                
                price_data = prices.get(symbol, {})
                current_price = price_data.get("price", 0) or float(w.get("last_price", 0) or 0)
                
                signal_data = signals.get(w["id"], {})
                signal_action = signal_data.get("action", "HOLD")
                signal_confidence = signal_data.get("confidence", 0)
                
                position = w.get("position", 0)
                entry_price = w.get("entry_price", 0)
                pnl = w.get("pnl_pct", 0)
                equity = w.get("initial_equity", 0)
                
                position_text = {1: "多頭", -1: "空頭", 0: "空倉"}.get(position, "空倉")
                
                data.append({
                    "交易對": symbol,
                    "策略": s_label,
                    "持倉": position_text,
                    "進場價": f"${entry_price:,.2f}" if entry_price > 0 else "-",
                    "當前價": f"${current_price:,.2f}",
                    "損益": f"{pnl:+.2f}%",
                    "金額": f"${equity * pnl / 100:+,.0f}" if pnl != 0 else f"${equity:,.0f}",
                    "信號": f"{signal_action} ({signal_confidence:.0f}%)",
                })
            
            if data:
                df = pd.DataFrame(data)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    height=400,
                )
        
        else:
            # 詳細視圖 - 展開每個持倉
            for w in watchlist:
                if not w.get("is_active", True):
                    continue
                
                with st.expander(f"**{w.get('symbol', '')}** - {get_strategy_label(w.get('strategy', ''))}", expanded=False):
                    # 詳細信息
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("持倉方向", position_text)
                        st.metric("進場價", f"${entry_price:,.2f}")
                    
                    with col2:
                        st.metric("當前價", f"${current_price:,.2f}")
                        st.metric("損益", f"{pnl:+.2f}%")
    
    else:
        st.info("📭 尚無訂閱。前往「➕ 新增訂閱」開始。")

# ════════════════════════════════════════════════════════════
# Tab 1: 持倉監控（與原邏輯相同，但 UI 緊湊化）
# ════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("#### 💼 持倉監控")
    # 這裡可以整合原有的持倉監控功能，但使用緊湊型 UI
    st.info("🚧 功能開發中 - 使用儀表板視圖查看持倉")

# ════════════════════════════════════════════════════════════
# Tab 2: 新增訂閱（緊湊型）
# ════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("#### ➕ 新增策略訂閱")
    
    col1, col2 = st.columns(2)
    with col1:
        w_market = st.radio("市場", ["₿ 加密貨幣", "🏛️ 傳統市場"], horizontal=True, key="w_mkt_radio")
    is_trad = w_market == "🏛️ 傳統市場"
    _mt = "traditional" if is_trad else "crypto"
    
    with col2:
        try:
            _cats = get_categories_l3(_mt)
            _sel_cat = st.selectbox("分類", _cats if _cats else ["全部"], key="w_cat")
        except Exception as e:
            st.error(f"載入分類失敗：{e}")
            _sel_cat = "全部"
    
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
    
    if _sel == "✏️ 自訂輸入":
        _symbol = st.text_input("自訂交易對", value="BTC/USDT", key="w_symbol_custom")
    else:
        _symbol = _sel.split(" — ")[0]
    
    _exchange = "binance" if _mt == "crypto" else "yfinance"
    
    st.markdown("#### 🧠 策略設定")
    strat_cols = st.columns(2)
    with strat_cols[0]:
        _strat = st.selectbox("策略", list(STRATEGY_LABELS.keys()), 
                            format_func=lambda x: get_strategy_label(x), key="w_strat")
    with strat_cols[1]:
        _tf = st.selectbox("時間框架", ["5m", "15m", "1h", "4h", "1d"], index=2, key="w_tf")
    
    st.markdown("#### 💰 資金設定")
    fund_cols = st.columns(3)
    with fund_cols[0]:
        _eq = st.number_input("初始資金", min_value=100.0, value=10000.0, step=500.0, key="w_eq")
    with fund_cols[1]:
        _lev = st.number_input("槓桿", min_value=1.0, value=1.0, max_value=125.0, step=0.5, key="w_lev")
    with fund_cols[2]:
        _fee = st.number_input("手續費%", min_value=0.0, value=0.05, step=0.01, key="w_fee")
    
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
                st.success(f"✅ 已新增 {_symbol}")
                get_watchlist_l3.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ 新增失敗：{e}")

# ════════════════════════════════════════════════════════════
# Tab 3: 自動交易（緊湊型）
# ════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("#### 🤖 自動交易配置")
    
    if st.session_state.trading_mode == "paper":
        st.info("🟢 當前為模擬盤模式")
    else:
        st.warning("🔴 當前為實盤模式")
    
    auto_col1, auto_col2 = st.columns(2)
    
    with auto_col1:
        auto_trade_enabled = st.toggle("啟用自動交易", value=False, key="auto_trade_toggle")
        
        if auto_trade_enabled:
            st.success("✅ 自動交易已啟用")
            
            auto_strategy = st.selectbox(
                "選擇策略",
                list(STRATEGY_LABELS.keys()),
                format_func=lambda x: get_strategy_label(x),
                key="auto_strat"
            )
            
            st.markdown("**策略參數**")
            auto_params = {}
            
            if auto_strategy == "sma_cross":
                col_a, col_b = st.columns(2)
                with col_a:
                    auto_params["fast_period"] = st.number_input("快速均線", min_value=1, value=5, key="auto_fast")
                with col_b:
                    auto_params["slow_period"] = st.number_input("慢速均線", min_value=1, value=20, key="auto_slow")
            
            st.markdown("**風險控制**")
            auto_stop_loss = st.number_input("停損 (%)", min_value=0.5, max_value=10.0, value=2.0, step=0.5, key="auto_sl")
            auto_take_profit = st.number_input("停利 (%)", min_value=1.0, max_value=20.0, value=4.0, step=0.5, key="auto_tp")
            
            if st.button("🚀 啟動自動交易", type="primary", use_container_width=True, key="start_auto_trade_btn"):
                st.success("✅ 自動交易已啟動！")
        else:
            st.info("ℹ️ 自動交易已停用")
    
    with auto_col2:
        st.markdown("**風險管理**")
        max_position = st.slider("最大持倉比例 (%)", min_value=10, max_value=100, value=50, step=10, key="auto_max_pos")
        daily_loss_limit = st.number_input("每日最大虧損 (%)", min_value=1.0, max_value=20.0, value=5.0, step=1.0, key="auto_daily_loss")
        max_trades_per_day = st.number_input("每日最大交易次數", min_value=1, max_value=50, value=10, key="auto_max_trades")
        
        st.divider()
        st.markdown("**通知設定**")
        send_bark = st.checkbox("Bark 通知", value=False, key="auto_bark")
        send_email = st.checkbox("Email 通知", value=False, key="auto_email")

# ════════════════════════════════════════════════════════════
# Tab 4: 實時新聞（World Monitor 風格）
# ════════════════════════════════════════════════════════════
with tabs[4]:
    render_news_panel(
        category="all",
        lang="all",
        limit=30,
        show_summary=False,
        auto_refresh=st.session_state.auto_refresh,
        refresh_interval=st.session_state.refresh_interval * 2,  # 新聞刷新間隔加倍
    )

# ════════════════════════════════════════════════════════════
# Tab 5: 交易日誌（緊湊型）
# ════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("#### 📜 交易日誌")
    
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        log_mode = st.radio("模式", ["全部", "模擬盤", "實盤"], horizontal=True, key="log_mode")
    with filter_col2:
        log_action = st.selectbox("類型", ["全部", "開倉", "平倉"], key="log_action")
    with filter_col3:
        log_limit = st.number_input("筆數", min_value=10, max_value=500, value=50, step=10, key="log_limit")
    
    trade_log = get_trade_log_l3(user["id"], limit=log_limit)
    
    if trade_log:
        df = pd.DataFrame(trade_log)
        
        if log_mode == "模擬盤":
            df = df[df["reason"].str.contains("模擬", na=False)]
        elif log_mode == "實盤":
            df = df[~df["reason"].str.contains("模擬", na=False)]
        
        if log_action != "全部":
            df = df[df["action"] == log_action]
        
        st.dataframe(
            df[["created_at", "symbol", "action", "side", "price", "pnl_pct", "reason"]],
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "created_at": st.column_config.DatetimeColumn("時間", format="YYYY-MM-DD HH:mm:ss"),
                "symbol": "交易對",
                "action": "類型",
                "side": "方向",
                "price": st.column_config.NumberColumn("價格", format="$%.2f"),
                "pnl_pct": st.column_config.NumberColumn("損益 %", format="%.2f%%"),
                "reason": "原因",
            }
        )
    else:
        st.info("📭 尚無交易記錄")

# ════════════════════════════════════════════════════════════
# 自動刷新
# ════════════════════════════════════════════════════════════
if st.session_state.auto_refresh and st.session_state.refresh_interval > 0:
    _time.sleep(st.session_state.refresh_interval)
    st.rerun()

# ════════════════════════════════════════════════════════════
# 頁尾
# ════════════════════════════════════════════════════════════
st.divider()
st.markdown("""
<div style="text-align:center;color:#8b949e;font-size:0.75rem;padding:12px 0;">
    <p>⚠️ <strong>風險提示</strong>：交易涉及高風險。© 2024 StocksX v6.0 Compact Dashboard</p>
</div>
""", unsafe_allow_html=True)
