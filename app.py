# StocksX — 通用回測平台
# 現代化設計 v3.0

import streamlit as st
from src.auth import UserDB
from src.config import APP_CSS, format_price
from typing import Any, Dict, List, Optional

st.set_page_config(
    page_title="StocksX — 通用回測平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ════════════════════════════════════════════════════════════
# CSS 樣式定義 - 現代化設計
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
/* ─── 全局設定 ─── */
.stApp {
    background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #0f1724 100%);
}

/* ─── 導航欄 ─── */
.nav-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 15px 25px;
    background: rgba(20,20,35,0.7);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(110,168,254,0.1);
    border-radius: 16px;
    margin: 15px 0 25px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.nav-logo {
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6ea8fe, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: flex;
    align-items: center;
    gap: 10px;
}
.nav-search input {
    width: 400px;
    background: rgba(30,30,50,0.6) !important;
    border: 1px solid rgba(110,168,254,0.3) !important;
    border-radius: 12px !important;
    padding: 10px 15px !important;
    color: #e0e0e8 !important;
    font-size: 0.9rem;
    transition: all 0.3s;
}
.nav-search input:focus {
    border-color: rgba(110,168,254,0.6) !important;
    box-shadow: 0 0 20px rgba(110,168,254,0.2) !important;
}

/* ─── Hero Banner ─── */
.hero-banner {
    background: linear-gradient(135deg, rgba(26,26,46,0.9) 0%, rgba(22,33,62,0.9) 50%, rgba(15,52,96,0.9) 100%);
    border-radius: 20px;
    padding: 35px 45px;
    margin: 20px 0 30px 0;
    border: 1px solid rgba(110,168,254,0.15);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(110,168,254,0.08) 0%, transparent 70%);
    animation: pulse 8s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.8; }
}
.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6ea8fe 0%, #a78bfa 50%, #6ea8fe 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 12px;
    position: relative;
    z-index: 1;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    font-size: 1rem;
    color: #94a3b8;
    margin-bottom: 25px;
    position: relative;
    z-index: 1;
    line-height: 1.6;
}
.hero-stats {
    display: flex;
    gap: 25px;
    flex-wrap: wrap;
    position: relative;
    z-index: 1;
}
.hero-stat-item {
    background: linear-gradient(135deg, rgba(110,168,254,0.1), rgba(167,139,250,0.05));
    backdrop-filter: blur(10px);
    border: 1px solid rgba(110,168,254,0.2);
    border-radius: 14px;
    padding: 18px 28px;
    min-width: 120px;
    transition: all 0.3s;
}
.hero-stat-item:hover {
    transform: translateY(-3px);
    border-color: rgba(110,168,254,0.4);
    box-shadow: 0 8px 20px rgba(110,168,254,0.15);
}
.hero-stat-value {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6ea8fe, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-stat-label {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 6px;
    font-weight: 500;
}

/* ─── 功能卡片 ─── */
.feature-card {
    background: linear-gradient(135deg, rgba(30,30,58,0.8), rgba(37,37,69,0.8));
    border: 1px solid rgba(58,58,92,0.5);
    border-radius: 16px;
    padding: 22px;
    transition: all 0.3s ease;
    height: 100%;
    position: relative;
    overflow: hidden;
}
.feature-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, rgba(110,168,254,0.5), transparent);
    opacity: 0;
    transition: opacity 0.3s;
}
.feature-card:hover {
    transform: translateY(-5px);
    border-color: rgba(110,168,254,0.4);
    box-shadow: 0 12px 35px rgba(0,0,0,0.4);
}
.feature-card:hover::before {
    opacity: 1;
}
.feature-icon {
    font-size: 2.2rem;
    margin-bottom: 14px;
    display: inline-block;
    transition: transform 0.3s;
}
.feature-card:hover .feature-icon {
    transform: scale(1.1) rotate(5deg);
}
.feature-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #f0f0ff;
    margin-bottom: 10px;
}
.feature-desc {
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.6;
    margin-bottom: 12px;
}
.feature-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}
.feature-tag {
    background: linear-gradient(135deg, rgba(110,168,254,0.15), rgba(167,139,250,0.1));
    color: #6ea8fe;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    border: 1px solid rgba(110,168,254,0.1);
}

/* ─── 市場行情區塊 ─── */
.market-section {
    background: rgba(26,26,46,0.5);
    border: 1px solid rgba(58,58,92,0.3);
    border-radius: 16px;
    padding: 25px;
    margin: 30px 0;
}

/* ─── 情緒儀表板 ─── */
.sentiment-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin: 25px 0;
}
.sentiment-card {
    background: linear-gradient(135deg, rgba(42,26,58,0.8), rgba(53,37,69,0.8));
    border: 1px solid rgba(90,58,124,0.4);
    border-radius: 16px;
    padding: 25px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.sentiment-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #6ea8fe, #a78bfa, #6ea8fe);
}
.sentiment-value {
    font-size: 3rem;
    font-weight: 800;
    line-height: 1;
    margin: 15px 0;
    text-shadow: 0 0 30px rgba(110,168,254,0.3);
}
.sentiment-label {
    font-size: 0.85rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
}
.sentiment-gauge {
    width: 100%;
    height: 8px;
    background: rgba(255,255,255,0.05);
    border-radius: 4px;
    margin-top: 20px;
    overflow: hidden;
}
.sentiment-gauge-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}

/* ─── 績效儀表板 ─── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(30,30,58,0.6), rgba(37,37,69,0.6));
    border: 1px solid rgba(58,58,92,0.4);
    border-radius: 12px;
    padding: 15px 18px;
    transition: all 0.3s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: rgba(110,168,254,0.3);
    box-shadow: 0 6px 20px rgba(110,168,254,0.1);
}
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #6ea8fe, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    color: #64748b !important;
    font-weight: 500 !important;
}

/* ─── 按鈕樣式 ─── */
.stButton > button {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    transition: all 0.3s !important;
    border: 1px solid transparent !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4a6cf7, #6366f1) !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #5b7cf8, #7577f2) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important;
    transform: translateY(-2px) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(40,40,70,0.6) !important;
    border: 1px solid rgba(74,74,108,0.5) !important;
    color: #d0d0e8 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: rgba(110,168,254,0.5) !important;
    background: rgba(40,40,70,0.8) !important;
}

/* ─── Tab 樣式 ─── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(26,26,46,0.5);
    border-radius: 12px;
    padding: 5px;
    border: 1px solid rgba(58,58,92,0.3);
    gap: 3px;
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 20px;
    border-radius: 10px;
    margin: 0 2px;
    font-size: 0.9rem;
    font-weight: 500;
    border: none !important;
    background: transparent !important;
    color: #94a3b8 !important;
    transition: all 0.3s;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(110,168,254,0.1) !important;
    color: #6ea8fe !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4a6cf7, #6366f1) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.3);
}

/* ─── 頁面鏈接 ─── */
[data-testid="stPageLink"] {
    background: linear-gradient(135deg, rgba(30,30,58,0.6), rgba(37,37,69,0.6));
    border: 1px solid rgba(58,58,92,0.3);
    border-radius: 14px;
    padding: 15px;
    transition: all 0.3s;
}
[data-testid="stPageLink"]:hover {
    background: linear-gradient(135deg, rgba(30,30,58,0.8), rgba(37,37,69,0.8));
    border-color: rgba(110,168,254,0.3);
    box-shadow: 0 6px 20px rgba(110,168,254,0.1);
    transform: translateY(-2px);
}

/* ─── 響應式設計 ─── */
@media (max-width: 768px) {
    .hero-title { font-size: 2rem; }
    .hero-stats { flex-direction: column; gap: 15px; }
    .nav-search input { width: 250px; }
    .feature-card { padding: 18px; }
}
"""

st.markdown(f"<style>{APP_CSS}\n{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 頁面路徑定義
# ════════════════════════════════════════════════════════════
_login_page = "pages/1_🔐_登入.py"
_crypto_page = "pages/2_₿_加密回測.py"
_trad_page = "pages/2_🏛️_傳統回測.py"
_history_page = "pages/3_📜_歷史.py"
_monitor_page = "pages/5_📡_監控.py"
_admin_page = "pages/4_🛠️_管理.py"
_news_page = "pages/6_📰_新聞.py"

user = st.session_state.get("user")

# ════════════════════════════════════════════════════════════
# 載入市場數據（快取優化）
# ════════════════════════════════════════════════════════════
from src.data.market_overview import (
    fetch_market_data,
    fetch_yahoo_reference_futures,
    fetch_yahoo_reference_trending,
)

@st.cache_data(ttl=60, show_spinner=False)
def get_market_data():
    return fetch_market_data()

@st.cache_data(ttl=60, show_spinner=False)
def get_yahoo_futures():
    return fetch_yahoo_reference_futures()

@st.cache_data(ttl=60, show_spinner=False)
def get_yahoo_trending():
    return fetch_yahoo_reference_trending()

# 載入數據
market_data = get_market_data()
yahoo_futures = get_yahoo_futures()
yahoo_trending = get_yahoo_trending()

# 已登入用戶才載入績效數據
if user:
    @st.cache_data(ttl=30, show_spinner=False)
    def get_user_performance(user_id: int):
        db = UserDB()
        history = db.get_history(user_id, limit=100)
        favorites = db.get_favorites(user_id)
        return history, favorites
    
    history, favorites = get_user_performance(user["id"])
else:
    history, favorites = [], []

# ════════════════════════════════════════════════════════════
# 導航欄
# ════════════════════════════════════════════════════════════
nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

with nav_col1:
    st.markdown('<div class="nav-logo">📊 StocksX</div>', unsafe_allow_html=True)

with nav_col2:
    st.text_input(
        "🔍 搜索代幣/代碼/名稱",
        placeholder="例如：BTC, AAPL, 台積電，黃金...",
        label_visibility="collapsed",
        key="global_search",
        help="輸入代幣代碼、股票代號或名稱進行搜索"
    )

with nav_col3:
    if user:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<span style="font-size:1.2rem;">👤</span> '
            f'<span style="color:#94a3b8;font-weight:500;">{user["display_name"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.page_link(_login_page, label="🔐 登入", icon="🔐")

st.markdown('<div class="nav-container"></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# Hero Banner
# ════════════════════════════════════════════════════════════
if not user:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">StocksX 通用回測平台</div>
        <div class="hero-subtitle">
            跨市場策略回測 · 15 種專業策略 · 即時監控 · 多資產支援
        </div>
        <div class="hero-stats">
            <div class="hero-stat-item">
                <div class="hero-stat-value">15+</div>
                <div class="hero-stat-label">交易策略</div>
            </div>
            <div class="hero-stat-item">
                <div class="hero-stat-value">500+</div>
                <div class="hero-stat-label">交易對</div>
            </div>
            <div class="hero-stat-item">
                <div class="hero-stat-value">31</div>
                <div class="hero-stat-label">交易所費率</div>
            </div>
            <div class="hero-stat-item">
                <div class="hero-stat-value">24/7</div>
                <div class="hero-stat-label">即時監控</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    db = UserDB()
    stats = db.get_stats()
    history_count = len(db.get_history(user["id"], limit=999))
    favorites_count = len(db.get_favorites(user["id"]))

    st.markdown(f"""
    <div class="hero-banner" style="background: linear-gradient(135deg, rgba(26,46,58,0.9) 0%, rgba(22,49,62,0.9) 50%, rgba(15,52,64,0.9) 100%);">
        <div class="hero-title">歡迎回來，{user['display_name']}！</div>
        <div class="hero-subtitle">
            {'👑 管理員控制台' if user['role'] == 'admin' else '👤 個人交易儀表板'}
        </div>
        <div class="hero-stats">
            <div class="hero-stat-item">
                <div class="hero-stat-value">{history_count}</div>
                <div class="hero-stat-label">我的回測</div>
            </div>
            <div class="hero-stat-item">
                <div class="hero-stat-value">{favorites_count}</div>
                <div class="hero-stat-label">收藏策略</div>
            </div>
            <div class="hero-stat-item">
                <div class="hero-stat-value">{stats['total_users']}</div>
                <div class="hero-stat-label">平台用戶</div>
            </div>
            <div class="hero-stat-item">
                <div class="hero-stat-value">{stats['recent_backtests_24h']}</div>
                <div class="hero-stat-label">24H 回測</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 用戶績效儀表板（僅已登入用戶）
# ════════════════════════════════════════════════════════════
if user and history:
    st.markdown("#### 📊 我的績效儀表板")
    
    # 績效指標
    total_trades = len(history)
    returns = [h.get("metrics", {}).get("total_return_pct", 0) for h in history]
    profitable_count = sum(1 for r in returns if r > 0)
    win_rate = profitable_count / total_trades * 100 if total_trades > 0 else 0
    avg_return = sum(returns) / len(returns) if returns else 0
    best_trade = max(returns) if returns else 0
    worst_trade = min(returns) if returns else 0
    
    if len(returns) > 1:
        import statistics
        std_dev = statistics.stdev(returns)
        sharpe = (avg_return / std_dev) if std_dev > 0 else 0
    else:
        sharpe = 0
    
    perf_cols = st.columns(5)
    perf_cols[0].metric("📈 總回測數", f"{total_trades}", delta=f"{win_rate:.1f}% 勝率")
    perf_cols[1].metric("💰 平均報酬", f"{avg_return:+.2f}%", delta=f"最佳：{best_trade:+.2f}%")
    perf_cols[2].metric("🏆 最佳交易", f"{best_trade:+.2f}%", delta=f"勝率 {win_rate:.1f}%")
    perf_cols[3].metric("📉 最大回撤", f"{worst_trade:.2f}%", delta=f"夏普：{sharpe:.2f}")
    perf_cols[4].metric("⭐ 收藏策略", f"{len(favorites)}", delta="個")
    
    st.divider()
    
    # 圖表
    chart_config = {'displayModeBar': False, 'responsive': True}
    
    cumulative_returns = []
    cumulative = 0
    for h in reversed(history):
        ret = h.get("metrics", {}).get("total_return_pct", 0)
        cumulative += ret
        cumulative_returns.append(cumulative)
    
    if cumulative_returns:
        chart_col1, chart_col2 = st.columns(2, gap="small")
        
        with chart_col1:
            import plotly.graph_objects as go
            
            final_return = cumulative_returns[-1] if cumulative_returns else 0
            line_color = '#00cc96' if final_return >= 0 else '#ef553b'
            
            fig_cumulative = go.Figure()
            fig_cumulative.add_trace(go.Scatter(
                y=cumulative_returns,
                mode='lines',
                line=dict(color=line_color, width=2.5),
                fill='tozeroy',
                fillcolor=f'rgba({0 if final_return >= 0 else 239},{155 if final_return >= 0 else 59},{96 if final_return >= 0 else 59},0.2)',
                hoverinfo='y'
            ))
            fig_cumulative.update_layout(
                title=dict(text="📈 累積報酬曲線", font_size=14, font=dict(color='#e0e0e8')),
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(50,50,90,0.3)', tickformat='.0f%', tickfont=dict(color='#94a3b8')),
                height=280,
                margin=dict(l=30, r=20, t=35, b=30),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(30,30,50,0.3)',
            )
            st.plotly_chart(fig_cumulative, use_container_width=True, key="cumulative_chart", config=chart_config)
        
        with chart_col2:
            import plotly.graph_objects as go
            
            if returns:
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(
                    x=returns,
                    nbinsx=15,
                    marker_color=['#00cc96' if r > 0 else '#ef553b' for r in returns],
                    opacity=0.85,
                    hoverinfo='x'
                ))
                fig_hist.update_layout(
                    title=dict(text="💹 收益分佈", font_size=14, font=dict(color='#e0e0e8')),
                    xaxis=dict(showgrid=False, tickformat='.1f%', tickfont=dict(color='#94a3b8')),
                    yaxis=dict(showgrid=True, gridcolor='rgba(50,50,90,0.3)', tickfont=dict(color='#94a3b8')),
                    height=280,
                    margin=dict(l=30, r=20, t=35, b=30),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(30,30,50,0.3)',
                )
                st.plotly_chart(fig_hist, use_container_width=True, key="hist_chart", config=chart_config)
    
    # 熱門策略
    st.markdown("#### 🎯 我的熱門策略")
    
    strategy_stats = {}
    for h in history:
        strategy = h.get("strategy", "Unknown")
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {"count": 0, "total_return": 0, "wins": 0}
        strategy_stats[strategy]["count"] += 1
        ret = h.get("metrics", {}).get("total_return_pct", 0)
        strategy_stats[strategy]["total_return"] += ret
        if ret > 0:
            strategy_stats[strategy]["wins"] += 1
    
    sorted_strategies = sorted(
        strategy_stats.items(),
        key=lambda x: x[1]["total_return"],
        reverse=True
    )[:5]
    
    strat_cols = st.columns(5 if len(sorted_strategies) >= 5 else len(sorted_strategies), gap="small")
    for idx, (strategy, stats) in enumerate(sorted_strategies):
        col = strat_cols[idx]
        avg_ret = stats["total_return"] / stats["count"] if stats["count"] > 0 else 0
        win_rate_s = stats["wins"] / stats["count"] * 100 if stats["count"] > 0 else 0
        
        from src.config import STRATEGY_LABELS
        strategy_name = STRATEGY_LABELS.get(strategy, strategy)
        color = "#00cc96" if avg_ret > 0 else "#ef553b"
        
        col.markdown(f"""
        <div class="feature-card" style="border-left: 3px solid {color}; padding: 15px;">
            <div style="font-size:0.95rem;font-weight:600;color:#f0f0ff;margin-bottom:6px;">
                {strategy_name}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:0.75rem;">
                <div style="color:#94a3b8;">次數</div>
                <div style="color:#e0e0e8;text-align:right;">{stats["count"]}</div>
                <div style="color:#94a3b8;">均報酬</div>
                <div style="color:{color};text-align:right;">{avg_ret:+.1f}%</div>
                <div style="color:#94a3b8;">勝率</div>
                <div style="color:{color};text-align:right;">{win_rate_s:.0f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()

# ════════════════════════════════════════════════════════════
# 核心功能
# ════════════════════════════════════════════════════════════
st.markdown("#### 🎯 核心功能")

features = [
    {
        "icon": "₿",
        "title": "加密貨幣回測",
        "desc": "支援 11 個交易所、主流幣/DeFi/Meme 全覆蓋，真實手續費模擬",
        "tags": ["現貨", "永續", "期權"],
        "link": _crypto_page,
    },
    {
        "icon": "🏛️",
        "title": "傳統市場回測",
        "desc": "美股、台股、ETF、期貨、指數，Yahoo Finance 數據源",
        "tags": ["股票", "ETF", "期貨", "指數"],
        "link": _trad_page,
    },
    {
        "icon": "📡",
        "title": "策略即時監控",
        "desc": "訂閱任意交易對×策略組合，即時信號、持倉追蹤、未實現 P&L",
        "tags": ["即時", "訂閱", "信號"],
        "link": _monitor_page,
    },
    {
        "icon": "📊",
        "title": "15 種專業策略",
        "desc": "雙均線、MACD、RSI、布林帶、一目均衡表等經典策略即開即用",
        "tags": ["趨勢", "擺盪", "突破"],
        "link": _crypto_page,
    },
    {
        "icon": "📜",
        "title": "回測歷史管理",
        "desc": "自動保存、備註標籤、策略收藏、績效對比、參數預設",
        "tags": ["歷史", "收藏", "對比"],
        "link": _history_page,
    },
    {
        "icon": "🛠️",
        "title": "管理員後台" if user and user["role"] == "admin" else "市場新聞",
        "desc": "用戶管理、安全日誌、數據快取、系統統計" if user and user["role"] == "admin" else "最新市場動態、加密新聞、產業資訊",
        "tags": ["管理", "安全", "監控"] if user and user["role"] == "admin" else ["新聞", "市場", "資訊"],
        "link": _admin_page if user and user["role"] == "admin" else _news_page,
    },
]

# 功能卡片
feat_cols = st.columns(3, gap="large")
for idx, f in enumerate(features):
    col = feat_cols[idx % 3]
    with col:
        tags_html = "".join([f'<span class="feature-tag">{t}</span>' for t in f["tags"]])
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{f["icon"]}</div>
            <div class="feature-title">{f["title"]}</div>
            <div class="feature-desc">{f["desc"]}</div>
            <div class="feature-tags">{tags_html}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"進入{f['title']} →", key=f"feat_{idx}", use_container_width=True):
            st.switch_page(f["link"])

# ════════════════════════════════════════════════════════════
# 市場行情
# ════════════════════════════════════════════════════════════
st.markdown("#### 📈 市場行情")

if yahoo_futures or yahoo_trending:
    tab1, tab2 = st.tabs(["📊 期貨報價", "🔥 熱門標的"])
    
    with tab1:
        if yahoo_futures:
            cols = st.columns(4)
            for i, item in enumerate(yahoo_futures):
                _chg = item["change"]
                _icon = "🟢" if _chg > 0 else "🔴" if _chg < 0 else "⚪"
                _delta_color = "normal" if _chg >= 0 else "inverse"
                cols[i % 4].metric(
                    f"{_icon} {item['name']}",
                    format_price(item["price"]),
                    delta=f"{_chg:+.2f}%",
                    delta_color=_delta_color,
                )
    
    with tab2:
        if yahoo_trending:
            cols = st.columns(4)
            for i, item in enumerate(yahoo_trending):
                _chg = item["change"]
                _icon = "🟢" if _chg > 0 else "🔴" if _chg < 0 else "⚪"
                _delta_color = "normal" if _chg >= 0 else "inverse"
                cols[i % 4].metric(
                    f"{_icon} {item['name']}",
                    format_price(item["price"]),
                    delta=f"{_chg:+.2f}%",
                    delta_color=_delta_color,
                )

# ════════════════════════════════════════════════════════════
# 情緒儀表板
# ════════════════════════════════════════════════════════════
st.markdown("#### 🌡️ 市場情緒儀表板")

sentiment_html = '<div class="sentiment-container">'

# 恐懼貪婪指數
try:
    from src.data.sources.api_hub import get_current_fear_greed
    fg = get_current_fear_greed()
    if fg:
        fg_val = fg["value"]
        fg_color = "#00ff00" if fg_val > 50 else "#ff4444" if fg_val < 30 else "#ffa500"
        fg_text = fg["classification"]
    else:
        fg_val, fg_color, fg_text = 50, "#666", "數據不可用"
except Exception:
    fg_val, fg_color, fg_text = 50, "#666", "數據不可用"

sentiment_html += f"""
<div class="sentiment-card">
    <div style="font-size:1.5rem;margin-bottom:10px;">🌡️ 加密恐懼貪婪</div>
    <div class="sentiment-value" style="color:{fg_color}">{fg_val if fg_val != 50 else '--'}</div>
    <div class="sentiment-label">{fg_text}</div>
    <div class="sentiment-gauge">
        <div class="sentiment-gauge-fill" style="width:{fg_val}%;background:{fg_color}"></div>
    </div>
</div>
"""

# VIX 指數
try:
    from src.data.sources.api_hub import fetch_cboe_vix
    vix = fetch_cboe_vix()
    if vix:
        vix_val = float(vix.get("close", 0))
        vix_color = "#00ff00" if vix_val < 20 else "#ff4444" if vix_val > 30 else "#ffa500"
        vix_text = "低波動" if vix_val < 20 else "高波動" if vix_val > 30 else "中等波動"
    else:
        vix_val, vix_color, vix_text = None, "#666", "數據不可用"
except Exception:
    vix_val, vix_color, vix_text = None, "#666", "數據不可用"

vix_display = f"{vix_val:.1f}" if vix_val else "--"
vix_gauge_width = min(vix_val, 80) if vix_val else 50
vix_label = vix_text if vix_val else "數據不可用"

sentiment_html += f"""
<div class="sentiment-card">
    <div style="font-size:1.5rem;margin-bottom:10px;">😨 VIX 波動率</div>
    <div class="sentiment-value" style="color:{vix_color}">{vix_display}</div>
    <div class="sentiment-label">{vix_label}</div>
    <div class="sentiment-gauge">
        <div class="sentiment-gauge-fill" style="width:{vix_gauge_width}%;background:{vix_color}"></div>
    </div>
</div>
"""

sentiment_html += '</div>'
st.markdown(sentiment_html, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 快速開始（已登入）
# ════════════════════════════════════════════════════════════
if user:
    st.markdown("#### 🚀 快速開始")
    qa_cols = st.columns(4)
    with qa_cols[0]:
        st.page_link(_crypto_page, label="₿ 加密回測", icon="💰", use_container_width=True)
    with qa_cols[1]:
        st.page_link(_trad_page, label="🏛️ 傳統回測", icon="🏛️", use_container_width=True)
    with qa_cols[2]:
        st.page_link(_monitor_page, label="📡 策略監控", icon="📡", use_container_width=True)
    with qa_cols[3]:
        st.page_link(_history_page, label="📜 歷史記錄", icon="📜", use_container_width=True)

# ════════════════════════════════════════════════════════════
# 頁尾
# ════════════════════════════════════════════════════════════
st.divider()
st.caption("""
⚠️ **免責聲明**：本平台僅供學習與研究，不構成投資建議。
數據與參考來源：[Yahoo Finance](https://finance.yahoo.com/)。
回測結果基於歷史數據，不代表未來表現。
""")
