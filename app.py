# StocksX — 通用回測平台
# 全新改版：Hero Banner + 卡片式佈局 + 專業儀表板

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
# CSS 樣式定義
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
/* ─── 全局設定 ─── */
.stApp {
    background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #0f1724 100%);
}

/* ─── Hero Banner ─── */
.hero-banner {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 12px;
    padding: 25px 35px;
    margin: 15px 0 20px 0;
    border: 1px solid #2a2a4a;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
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
    background: radial-gradient(circle, rgba(110,168,254,0.1) 0%, transparent 70%);
    animation: pulse 8s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.8; }
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6ea8fe, #a78bfa, #6ea8fe);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
}
.hero-subtitle {
    font-size: 0.95rem;
    color: #94a3b8;
    margin-bottom: 18px;
    position: relative;
    z-index: 1;
}
.hero-stats {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    position: relative;
    z-index: 1;
}
.hero-stat-item {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 12px 20px;
    min-width: 100px;
}
.hero-stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #6ea8fe;
}
.hero-stat-label {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: 4px;
}

/* ─── 導航欄 ─── */
.nav-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: rgba(26,26,46,0.8);
    backdrop-filter: blur(20px);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    margin-bottom: 20px;
}
.nav-logo {
    font-size: 1.3rem;
    font-weight: bold;
    color: #6ea8fe;
    display: flex;
    align-items: center;
    gap: 8px;
}
.nav-search input {
    width: 320px;
    background: rgba(30,30,55,0.9) !important;
    border: 1px solid #3a3a5c !important;
    border-radius: 8px;
    padding: 8px 12px !important;
    color: #e0e0e8 !important;
    font-size: 0.9rem;
}
.nav-user {
    display: flex;
    align-items: center;
    gap: 10px;
}

/* ─── 功能卡片 ─── */
.feature-card {
    background: linear-gradient(135deg, #1e1e3a, #252545);
    border: 1px solid #3a3a5c;
    border-radius: 12px;
    padding: 18px;
    transition: all 0.3s ease;
    height: 100%;
}
.stColumn > div:has(.feature-card) {
    height: 100%;
}
.feature-card:hover {
    transform: translateY(-3px);
    border-color: #6ea8fe;
    box-shadow: 0 6px 20px rgba(110,168,254,0.2);
}
.feature-icon {
    font-size: 2rem;
    margin-bottom: 10px;
}
.feature-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #f0f0ff;
    margin-bottom: 8px;
}
.feature-desc {
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.5;
}
.feature-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 12px;
}
.feature-tag {
    background: rgba(110,168,254,0.15);
    color: #6ea8fe;
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 0.7rem;
    font-weight: 500;
}

/* ─── 市場行情區塊 ─── */
.market-section {
    background: rgba(26,26,46,0.6);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
}
.market-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 15px;
}
.market-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #f0f0ff;
}

/* ─── 情緒儀表板 ─── */
.sentiment-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
    margin: 20px 0;
}
.sentiment-card {
    background: linear-gradient(135deg, #2a1a3a, #352545);
    border: 1px solid #5a3a7c;
    border-radius: 12px;
    padding: 20px;
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
    height: 3px;
    background: linear-gradient(90deg, #6ea8fe, #a78bfa);
}
.sentiment-value {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1;
    margin: 10px 0;
}
.sentiment-label {
    font-size: 0.85rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.sentiment-gauge {
    width: 100%;
    height: 6px;
    background: rgba(255,255,255,0.1);
    border-radius: 3px;
    margin-top: 15px;
    overflow: hidden;
}
.sentiment-gauge-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
}

/* ─── 快速訪問按鈕 ─── */
.quick-action-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: linear-gradient(135deg, #1e1e3a, #252545);
    border: 1px solid #3a3a5c;
    border-radius: 12px;
    text-decoration: none;
    transition: all 0.3s ease;
    min-height: 100px;
}
.quick-action-btn:hover {
    border-color: #6ea8fe;
    background: linear-gradient(135deg, #252545, #2a2a50);
    transform: translateY(-2px);
}
.quick-action-icon {
    font-size: 1.8rem;
    margin-bottom: 8px;
}
.quick-action-label {
    color: #e0e0e8;
    font-weight: 500;
}

/* ─── 績效儀表板 ─── */
[data-testid="stMetric"] {
    animation: fadeInUp 0.5s ease forwards;
    background: linear-gradient(135deg, #1e1e3a, #252545);
    border: 1px solid #3a3a5c;
    border-radius: 10px;
    padding: 12px 15px;
}
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    color: #6ea8fe !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    color: #94a3b8 !important;
}

/* ─── 指標卡片動畫 ─── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ─── 響應式設計 ─── */
@media (max-width: 768px) {
    .hero-title { font-size: 2rem; }
    .hero-stats { flex-direction: column; gap: 15px; }
    .nav-search input { width: 200px; }
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
# 載入市場數據（增加快取，減少重複查詢）
# ════════════════════════════════════════════════════════════
from src.data.market_overview import (
    fetch_market_data,
    fetch_yahoo_reference_futures,
    fetch_yahoo_reference_trending,
)

# 使用快取，60 秒更新一次（原本無快取或 120 秒）
@st.cache_data(ttl=60, show_spinner=False)
def get_market_data():
    return fetch_market_data()

@st.cache_data(ttl=60, show_spinner=False)
def get_yahoo_futures():
    return fetch_yahoo_reference_futures()

@st.cache_data(ttl=60, show_spinner=False)
def get_yahoo_trending():
    return fetch_yahoo_reference_trending()

# 非阻塞式載入市場數據（使用 placeholder 延遲顯示）
market_placeholder = st.empty()
with market_placeholder:
    with st.spinner("載入市場行情…"):
        market_data = get_market_data()
        yahoo_futures = get_yahoo_futures()
        yahoo_trending = get_yahoo_trending()

# 已登入用戶才預先載入績效數據
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
        key="global_search"
    )

with nav_col3:
    if user:
        st.markdown(
            f'<div class="nav-user"><span style="color:#94a3b8">👤</span> {user["display_name"]}</div>',
            unsafe_allow_html=True
        )
    else:
        st.page_link(_login_page, label="🔐 登入", icon="🔐")

st.markdown('<div class="nav-container"></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# Hero Banner（僅未登入顯示完整版）
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
    # 已登入用戶顯示歡迎訊息
    db = UserDB()
    stats = db.get_stats()
    history_count = len(db.get_history(user["id"], limit=999))
    favorites_count = len(db.get_favorites(user["id"]))

    st.markdown(f"""
    <div class="hero-banner" style="background: linear-gradient(135deg, #1a2e3a 0%, #16313e 50%, #0f3440 100%);">
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
# 用戶績效儀表板（僅已登入用戶）- 使用快取優化
# ════════════════════════════════════════════════════════════
if user and history:
    # 績效計算（使用快取的數據）
    st.markdown("#### 📊 我的績效儀表板")
    
    # 一次性計算所有指標
    total_trades = len(history)
    returns = [h.get("metrics", {}).get("total_return_pct", 0) for h in history]
    profitable_count = sum(1 for r in returns if r > 0)
    win_rate = profitable_count / total_trades * 100 if total_trades > 0 else 0
    avg_return = sum(returns) / len(returns) if returns else 0
    best_trade = max(returns) if returns else 0
    worst_trade = min(returns) if returns else 0
    
    # 夏普比率（簡化）
    if len(returns) > 1:
        import statistics
        std_dev = statistics.stdev(returns)
        sharpe = (avg_return / std_dev) if std_dev > 0 else 0
    else:
        sharpe = 0
    
    # 績效卡片（使用快取的 favorites 長度）
    perf_cols = st.columns(5)
    perf_cols[0].metric("📈 總回測數", f"{total_trades}", delta=f"{win_rate:.1f}% 勝率")
    perf_cols[1].metric("💰 平均報酬", f"{avg_return:+.2f}%", delta=f"最佳：{best_trade:+.2f}%")
    perf_cols[2].metric("🏆 最佳交易", f"{best_trade:+.2f}%", delta=f"勝率 {win_rate:.1f}%")
    perf_cols[3].metric("📉 最大回撤", f"{worst_trade:.2f}%", delta=f"夏普：{sharpe:.2f}")
    perf_cols[4].metric("⭐ 收藏策略", f"{len(favorites)}", delta="個")
    
    st.divider()
    
    # 圖表區域 - 使用 config 優化渲染速度
    chart_config = {'displayModeBar': False, 'responsive': True}
    
    # 累積報酬曲線（簡化數據點）
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
            
            # 計算漲跌顏色
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
            
            # 簡化直方圖（減少 bin 數）
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
    
    # 熱門策略分析（只顯示前 5 個）
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
    )[:5]  # 只顯示前 5 個
    
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
# 主要功能卡片
# ════════════════════════════════════════════════════════════
st.markdown("#### 🎯 核心功能")

# 第一排 3 張卡片
col1, col2, col3 = st.columns(3, gap="small")

with col1:
    st.markdown("""
    <div class="feature-card" style="cursor: pointer;">
        <div class="feature-icon">₿</div>
        <div class="feature-title">加密貨幣回測</div>
        <div class="feature-desc">支援 11 個交易所、主流幣/DeFi/Meme 全覆蓋，真實手續費模擬</div>
        <div class="feature-tags"><span class="feature-tag">現貨</span><span class="feature-tag">永續</span><span class="feature-tag">期權</span></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("進入加密回測 →", key="btn_crypto", use_container_width=True):
        st.switch_page(_crypto_page)

with col2:
    st.markdown("""
    <div class="feature-card" style="cursor: pointer;">
        <div class="feature-icon">🏛️</div>
        <div class="feature-title">傳統市場回測</div>
        <div class="feature-desc">美股、台股、ETF、期貨、指數，Yahoo Finance 數據源</div>
        <div class="feature-tags"><span class="feature-tag">股票</span><span class="feature-tag">ETF</span><span class="feature-tag">期貨</span></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("進入傳統回測 →", key="btn_trad", use_container_width=True):
        st.switch_page(_trad_page)

with col3:
    st.markdown("""
    <div class="feature-card" style="cursor: pointer;">
        <div class="feature-icon">📡</div>
        <div class="feature-title">策略即時監控</div>
        <div class="feature-desc">訂閱任意交易對×策略組合，即時信號、持倉追蹤、未實現 P&L</div>
        <div class="feature-tags"><span class="feature-tag">即時</span><span class="feature-tag">訂閱</span><span class="feature-tag">信號</span></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("進入策略監控 →", key="btn_monitor", use_container_width=True):
        st.switch_page(_monitor_page)

# 第二排 3 張卡片
col4, col5, col6 = st.columns(3, gap="small")

with col4:
    st.markdown("""
    <div class="feature-card" style="cursor: pointer;">
        <div class="feature-icon">📊</div>
        <div class="feature-title">15 種專業策略</div>
        <div class="feature-desc">雙均線、MACD、RSI、布林帶、一目均衡表等經典策略即開即用</div>
        <div class="feature-tags"><span class="feature-tag">趨勢</span><span class="feature-tag">擺盪</span><span class="feature-tag">突破</span></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("查看策略 →", key="btn_strategies", use_container_width=True):
        st.switch_page(_crypto_page)

with col5:
    st.markdown("""
    <div class="feature-card" style="cursor: pointer;">
        <div class="feature-icon">📜</div>
        <div class="feature-title">回測歷史管理</div>
        <div class="feature-desc">自動保存、備註標籤、策略收藏、績效對比、參數預設</div>
        <div class="feature-tags"><span class="feature-tag">歷史</span><span class="feature-tag">收藏</span><span class="feature-tag">對比</span></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("查看歷史 →", key="btn_history", use_container_width=True):
        st.switch_page(_history_page)

with col6:
    target_page = _admin_page if user and user["role"] == "admin" else _news_page
    target_label = "管理員後台" if user and user["role"] == "admin" else "市場新聞"
    st.markdown(f"""
    <div class="feature-card" style="cursor: pointer;">
        <div class="feature-icon">🛠️</div>
        <div class="feature-title">{target_label}</div>
        <div class="feature-desc">{"用戶管理、安全日誌、數據快取、系統統計" if user and user["role"] == "admin" else "最新市場動態、加密新聞、產業資訊"}</div>
        <div class="feature-tags"><span class="feature-tag">管理</span><span class="feature-tag">安全</span><span class="feature-tag">監控</span></div>
    </div>
    """, unsafe_allow_html=True)
    btn_label = "進入管理後台 →" if user and user["role"] == "admin" else "查看新聞 →"
    if st.button(btn_label, key="btn_admin", use_container_width=True):
        st.switch_page(target_page)

# ════════════════════════════════════════════════════════════
# 市場行情總覽
# ════════════════════════════════════════════════════════════
st.markdown("#### 📈 市場行情")

# 期貨 & 熱門標的 Tabs
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
        fg_percent = f"{fg_val}%"
        fg_text = fg["classification"]
    else:
        fg_val, fg_color, fg_percent, fg_text = None, "#666", "--", "數據不可用"
except Exception:
    fg_val, fg_color, fg_percent, fg_text = None, "#666", "--", "數據不可用"

sentiment_html += f"""
<div class="sentiment-card">
    <div style="font-size:1.5rem;margin-bottom:10px;">🌡️ 加密恐懼貪婪</div>
    <div class="sentiment-value" style="color:{fg_color}">{fg_percent}</div>
    <div class="sentiment-label">{fg_text}</div>
    <div class="sentiment-gauge">
        <div class="sentiment-gauge-fill" style="width:{fg_val if fg_val else 50}%;background:{fg_color}"></div>
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
# 快速開始（已登入用戶）
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
