# StocksX — 通用回測平台
# 現代化設計 v4.0 (Glassmorphism 主題)

import statistics

import streamlit as st

from src.auth import UserDB
from src.config import format_price
from src.data.market_overview import (
    fetch_market_data,
    fetch_yahoo_reference_futures,
    fetch_yahoo_reference_trending,
)
from src.ui_enhanced import (
    render_auto_refresh_market_data,
    render_global_search,
    render_quick_actions,
)
from src.ui_modern import (
    apply_modern_theme,
    render_feature_grid,
    render_glow_metric,
    render_gradient_divider,
    render_hero_banner,
)

st.set_page_config(
    page_title="StocksX — 通用回測平台", page_icon="📊", layout="wide", initial_sidebar_state="collapsed"
)

# 應用現代化主題
apply_modern_theme()

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
_health_page = "pages/7_🏥_健康檢查.py"
_live_page = "pages/8_⚡_即時監控.py"
_ai_strat_page = "pages/9_🧠_AI 策略.py"
_backtest_compare_page = "pages/10_📊_策略回测对比.py"

user = st.session_state.get("user")

# ════════════════════════════════════════════════════════════
# 載入市場數據（快取 + session 狀態保護）
# ════════════════════════════════════════════════════════════


@st.cache_data(ttl=60, show_spinner=False)
def get_market_data():
    return fetch_market_data()


@st.cache_data(ttl=60, show_spinner=False)
def get_yahoo_futures():
    return fetch_yahoo_reference_futures()


@st.cache_data(ttl=60, show_spinner=False)
def get_yahoo_trending():
    return fetch_yahoo_reference_trending()


market_data = get_market_data()
yahoo_futures = get_yahoo_futures()
yahoo_trending = get_yahoo_trending()
st.session_state["market_data_loaded"] = True

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
    st.markdown(
        '<div style="font-size:1.8rem;font-weight:800;background:linear-gradient(135deg, #667eea, #764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">📊 StocksX</div>',
        unsafe_allow_html=True,
    )

with nav_col2:
    render_global_search()

with nav_col3:
    if user:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;background:rgba(255,255,255,0.1);padding:8px 16px;border-radius:12px;">'
            f'<span style="font-size:1.2rem;">👤</span> '
            f'<span style="color:#e0e0e8;font-weight:500;">{user["display_name"]}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.page_link(_login_page, label="🔐 登入", icon="🔐")

st.divider()

# ════════════════════════════════════════════════════════════
# Hero Banner
# ════════════════════════════════════════════════════════════
if not user:
    render_hero_banner(
        title="StocksX 通用回測平台",
        subtitle="跨市場策略回測 · 15 種專業策略 · 即時監控 · 多資產支援",
        stats=[
            {"value": "15+", "label": "交易策略"},
            {"value": "500+", "label": "交易對"},
            {"value": "31", "label": "交易所費率"},
            {"value": "24/7", "label": "即時監控"},
        ],
    )
else:
    _db = UserDB()
    stats = _db.get_stats()
    history_count = len(_db.get_history(user["id"], limit=999))
    favorites_count = len(_db.get_favorites(user["id"]))

    render_hero_banner(
        title=f"歡迎回來，{user['display_name']}！",
        subtitle="👑 管理員控制台" if user["role"] == "admin" else "👤 個人交易儀表板",
        stats=[
            {"value": str(history_count), "label": "我的回測"},
            {"value": str(favorites_count), "label": "收藏策略"},
            {"value": str(stats["total_users"]), "label": "平台用戶"},
            {"value": str(stats["recent_backtests_24h"]), "label": "24H 回測"},
        ],
    )

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

    render_gradient_divider()

# ════════════════════════════════════════════════════════════
# 快捷操作
# ════════════════════════════════════════════════════════════
render_quick_actions()

render_gradient_divider()

# ════════════════════════════════════════════════════════════
# 核心功能
# ════════════════════════════════════════════════════════════
st.markdown("#### 🎯 核心功能")

features = [
    {
        "icon": "₿",
        "title": "加密貨幣回測",
        "desc": "支援 11 個交易所、主流幣/DeFi/Meme 全覆蓋，真實手續費模擬",
        "tags": '<span class="status-badge status-info">現貨</span> <span class="status-badge status-info">永續</span>',
        "link": _crypto_page,
    },
    {
        "icon": "🏛️",
        "title": "傳統市場回測",
        "desc": "美股、台股、ETF、期貨、指數，Yahoo Finance 數據源",
        "tags": '<span class="status-badge status-info">股票</span> <span class="status-badge status-info">ETF</span>',
        "link": _trad_page,
    },
    {
        "icon": "📡",
        "title": "策略即時監控",
        "desc": "訂閱任意交易對×策略組合，即時信號、持倉追蹤、未實現 P&L",
        "tags": '<span class="status-badge status-success">即時</span> <span class="status-badge status-success">訂閱</span>',
        "link": _live_page,
    },
    {
        "icon": "🧠",
        "title": "🧠 AI 策略中心",
        "desc": "LSTM 預測、NLP 情緒、配對交易、強化學習等前沿 AI 策略",
        "tags": '<span class="status-badge status-success">機器學習</span> <span class="status-badge status-success">深度學習</span>',
        "link": _ai_strat_page,
    },
    {
        "icon": "📊",
        "title": "15 種專業策略",
        "desc": "雙均線、MACD、RSI、布林帶、一目均衡表等經典策略即開即用",
        "tags": '<span class="status-badge status-warning">趨勢</span> <span class="status-badge status-warning">擺盪</span>',
        "link": _crypto_page,
    },
    {
        "icon": "📈",
        "title": "策略回測對比",
        "desc": "對比不同策略歷史表現，Sharpe、回撤、勝率全方位分析",
        "tags": '<span class="status-badge status-info">對比</span> <span class="status-badge status-info">分析</span>',
        "link": _backtest_compare_page,
    },
    {
        "icon": "📜",
        "title": "回測歷史管理",
        "desc": "自動保存、備註標籤、策略收藏、績效對比、參數預設",
        "tags": '<span class="status-badge status-info">歷史</span> <span class="status-badge status-info">對比</span>',
        "link": _history_page,
    },
    {
        "icon": "🛠️",
        "title": "管理員後台" if user and user["role"] == "admin" else "📰 市場新聞",
        "desc": "用戶管理、安全日誌、數據快取、系統統計"
        if user and user["role"] == "admin"
        else "最新市場動態、加密新聞、產業資訊",
        "tags": '<span class="status-badge status-info">管理</span>'
        if user and user["role"] == "admin"
        else '<span class="status-badge status-info">新聞</span>',
        "link": _admin_page if user and user["role"] == "admin" else _news_page,
    },
]

render_feature_grid(features, columns=3)

render_gradient_divider()

# ════════════════════════════════════════════════════════════
# 市場行情
# ════════════════════════════════════════════════════════════
st.markdown("#### 📈 市場行情")

render_auto_refresh_market_data()

if yahoo_futures or yahoo_trending:
    tab1, tab2, tab3 = st.tabs(["📊 期貨報價", "🔥 熱門標的", "📰 加密貨幣"])

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

    with tab3:
        # 加密貨幣快速預覽
        try:
            from src.data.sources.api_hub import get_current_fear_greed

            fg = get_current_fear_greed()
            if fg:
                fg_col1, fg_col2 = st.columns(2)
                fg_col1.metric("🌡️ 恐懼貪婪指數", f"{fg['value']}", delta=fg["classification"])

            # 主流幣簡易報價（真實 API）
            st.caption("💰 主流幣簡易報價（24h）")
            from src.data.sources.api_hub import fetch_coingecko

            crypto_data = fetch_coingecko(
                "/simple/price",
                params={
                    "ids": "bitcoin,ethereum,solana",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                },
            )
            if crypto_data:
                crypto_map = {
                    "bitcoin": {"symbol": "BTC", "name": "Bitcoin"},
                    "ethereum": {"symbol": "ETH", "name": "Ethereum"},
                    "solana": {"symbol": "SOL", "name": "Solana"},
                }
                crypto_cols = st.columns(3)
                for idx, (cid, info) in enumerate(crypto_map.items()):
                    if cid in crypto_data:
                        price = crypto_data[cid].get("usd", 0)
                        change = crypto_data[cid].get("usd_24h_change", 0)
                        _icon = "🟢" if change > 0 else "🔴"
                        crypto_cols[idx].metric(f"{_icon} {info['symbol']}", f"${price:,.0f}", delta=f"{change:+.1f}%")
        except Exception:
            st.caption("加密貨幣數據載入中...")

render_gradient_divider()

# ════════════════════════════════════════════════════════════
# 情緒儀表板（增強版）
# ════════════════════════════════════════════════════════════
st.markdown("#### 🌡️ 市場情緒儀表板")

sentiment_cols = st.columns(4)

# 恐懼貪婪指數
try:
    from src.data.sources.api_hub import get_current_fear_greed

    fg = get_current_fear_greed()
    if fg:
        fg_val = fg["value"]
        fg_color = "#00cc96" if fg_val >= 50 else "#ef553b"
        fg_emoji = (
            "🤑" if fg_val >= 75 else "😊" if fg_val >= 55 else "😐" if fg_val >= 45 else "😟" if fg_val >= 25 else "😱"
        )
        fg_label = fg["classification"]

        with sentiment_cols[0]:
            render_glow_metric("恐懼貪婪指數", f"{fg_emoji} {fg_val}", fg_label)
    else:
        raise Exception("數據不可用")
except Exception:
    with sentiment_cols[0]:
        render_glow_metric("恐懼貪婪指數", "--", "數據載入中")

# VIX 波動率指數
try:
    from src.data.sources.api_hub import fetch_cboe_vix

    vix = fetch_cboe_vix()
    if vix:
        vix_val = vix.get("close", 0)
        vix_color = "#ef553b" if vix_val > 20 else "#00cc96"
        vix_emoji = "📈" if vix_val > 20 else "📉"

        with sentiment_cols[1]:
            render_glow_metric("VIX 波動率", f"{vix_emoji} {vix_val:.1f}", "高波動" if vix_val > 20 else "低波動")
    else:
        raise Exception("數據不可用")
except Exception:
    with sentiment_cols[1]:
        render_glow_metric("VIX 波動率", "--", "數據載入中")

# 比特幣主導性
try:
    from src.data.sources.api_hub import fetch_coingecko

    btc_dom_data = fetch_coingecko("/global")
    if btc_dom_data and "data" in btc_dom_data:
        btc_dom = btc_dom_data["data"].get("btc_market_cap_dominance", 0)

        with sentiment_cols[2]:
            render_glow_metric("BTC 主導性", f"₿ {btc_dom:.1f}%", "市場份額")
    else:
        raise Exception("數據不可用")
except Exception:
    with sentiment_cols[2]:
        render_glow_metric("BTC 主導性", "--", "數據載入中")

# 市場趨勢
try:
    if yahoo_futures:
        bullish_count = sum(1 for f in yahoo_futures if f["change"] > 0)
        total = len(yahoo_futures)
        trend_pct = bullish_count / total * 100 if total > 0 else 50
        trend_color = "#00cc96" if trend_pct > 50 else "#ef553b"
        trend_emoji = "🐂" if trend_pct > 50 else "🐻"

        with sentiment_cols[3]:
            render_glow_metric(
                "市場趨勢",
                f"{trend_emoji} {trend_pct:.0f}%",
                f"{'多頭' if trend_pct > 50 else '空頭'} ({bullish_count}/{total})",
            )
    else:
        raise Exception("數據不可用")
except Exception:
    with sentiment_cols[3]:
        render_glow_metric("市場趨勢", "--", "數據載入中")

render_gradient_divider()

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
        st.page_link(_live_page, label="📡 即時監控", icon="📡", use_container_width=True)
    with qa_cols[3]:
        st.page_link(_history_page, label="📜 歷史記錄", icon="📜", use_container_width=True)

# ════════════════════════════════════════════════════════════
# 頁尾
# ════════════════════════════════════════════════════════════
render_gradient_divider()
st.markdown(
    """
<div style="text-align:center;color:#64748b;font-size:0.85rem;padding:20px 0;">
    <p>⚠️ <strong>免責聲明</strong>：本平台僅供學習與研究，不構成投資建議。</p>
    <p>數據與參考來源：Yahoo Finance | 回測結果基於歷史數據，不代表未來表現。</p>
    <p style="margin-top:10px;">© 2024–2026 StocksX. All rights reserved.</p>
</div>
""",
    unsafe_allow_html=True,
)
