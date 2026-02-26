# StocksX — 通用回測平台入口
"""
啟動方式：streamlit run app.py
"""
import streamlit as st
from src.auth import UserDB

st.set_page_config(page_title="StocksX — 通用回測平台", page_icon="📊", layout="wide")

st.markdown("""<style>
[data-testid="stMetric"] {background:#f8f9fb;border:1px solid #e0e3e8;border-radius:10px;padding:12px 16px;}
[data-testid="stMetric"] [data-testid="stMetricValue"] {font-size:1.3rem;}
div[data-testid="stExpander"] {border:1px solid #e0e3e8;border-radius:8px;}
.feature-card {background:linear-gradient(135deg,#f8f9fb,#eef1f5);border-radius:12px;padding:20px;height:160px;}
</style>""", unsafe_allow_html=True)

_login_page = "pages/1_🔐_登入.py"
_backtest_page = "pages/2_📊_回測.py"
_history_page = "pages/3_📜_歷史.py"
_admin_page = "pages/4_🛠️_管理.py"

user = st.session_state.get("user")

if not user:
    st.markdown("# 📊 StocksX — 通用回測平台")
    st.markdown("##### 加密貨幣 × 股票 × ETF × 期貨　五大策略一鍵回測")
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("#### 🎯 15 大策略\n雙均線、RSI、MACD、一目均衡表、SAR…")
    c2.markdown("#### 🌍 多市場\n加密貨幣 + 美股 + 台股 + ETF + 期貨")
    c3.markdown("#### 📰 即時新聞\nCoinDesk、Yahoo Finance、CNBC")
    c4.markdown("#### 🛠️ 管理後台\n用戶管理、系統統計")
    st.divider()
    st.page_link(_login_page, label="🔐 登入 / 註冊", icon="🔐")
else:
    db = UserDB()
    st.sidebar.markdown(f"### 👤 {user['display_name']}")
    st.sidebar.caption(f"{'👑 管理員' if user['role'] == 'admin' else '👤 用戶'}")
    if st.sidebar.button("🚪 登出", use_container_width=True):
        st.session_state.pop("user", None)
        st.rerun()
    st.sidebar.divider()

    st.markdown(f"## 👋 歡迎，{user['display_name']}！")

    # 快速統計
    history = db.get_history(user["id"], limit=5)
    stats = db.get_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📊 我的回測", len(db.get_history(user["id"], limit=999)))
    m2.metric("⭐ 收藏策略", len(db.get_favorites(user["id"])))
    m3.metric("👥 平台用戶", stats["total_users"])
    m4.metric("🔥 24h 回測", stats["recent_backtests_24h"])

    st.divider()

    # 快速導航
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 📊 執行回測")
        st.caption("五大策略 × 多市場")
        st.page_link(_backtest_page, label="前往回測", icon="📊")
    with col2:
        st.markdown("### 📡 策略監控")
        st.caption("訂閱策略即時信號")
        st.page_link("pages/5_📡_監控.py", label="前往監控", icon="📡")
    with col3:
        st.markdown("### 📜 歷史 & 收藏")
        st.caption("記錄、收藏、預設、提醒")
        st.page_link(_history_page, label="前往歷史", icon="📜")
    with col4:
        if user["role"] == "admin":
            st.markdown("### 🛠️ 管理後台")
            st.caption("用戶管理、系統統計")
            st.page_link(_admin_page, label="前往管理", icon="🛠️")
        else:
            st.markdown("### ⚙️ 設定")
            st.caption("修改暱稱、密碼")
            st.page_link(_history_page, label="前往設定", icon="⚙️")

    # 最近回測記錄
    if history:
        st.divider()
        st.markdown("### 📋 最近回測")
        for h in history[:5]:
            m = h.get("metrics", {})
            ret = m.get("total_return_pct", 0)
            icon = "🟢" if ret and ret > 0 else "🔴" if ret and ret < 0 else "⚪"
            st.markdown(f"{icon} **{h['symbol']}** × {h['strategy']} — 報酬 {ret}% | {h['timeframe']}")

st.caption("⚠️ 免責聲明：本平台僅供學習與研究，不構成投資建議。")
