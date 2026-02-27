# StocksX — 通用回測平台入口
import streamlit as st
from src.auth import UserDB
from src.config import APP_CSS, format_price

st.set_page_config(page_title="StocksX — 通用回測平台", page_icon="📊", layout="wide")
st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

_login_page = "pages/1_🔐_登入.py"
_crypto_page = "pages/2_₿_加密回測.py"
_trad_page = "pages/2_🏛️_傳統回測.py"
_history_page = "pages/3_📜_歷史.py"
_admin_page = "pages/4_🛠️_管理.py"

user = st.session_state.get("user")

# ─── 市場行情（登入/未登入都顯示）───
st.markdown("# 📊 StocksX")

from src.data.market_overview import fetch_market_data

with st.spinner("載入市場行情…"):
    market_data = fetch_market_data()

if market_data:
    tabs = st.tabs(list(market_data.keys()))
    for tab, (sector, items) in zip(tabs, market_data.items()):
        with tab:
            cols = st.columns(len(items))
            for col, item in zip(cols, items):
                _chg = item["change"]
                _icon = "🟢" if _chg > 0 else "🔴" if _chg < 0 else "⚪"
                _delta_color = "normal" if _chg >= 0 else "inverse"
                col.metric(
                    f"{_icon} {item['name']}",
                    format_price(item["price"]),
                    delta=f"{_chg:+.2f}%",
                    delta_color=_delta_color,
                )

    # 板塊漲跌統計
    _sector_summary = []
    for sector, items in market_data.items():
        _avg = sum(i["change"] for i in items) / len(items) if items else 0
        _up = sum(1 for i in items if i["change"] > 0)
        _down = sum(1 for i in items if i["change"] < 0)
        _sector_summary.append({"板塊": sector, "平均漲跌%": round(_avg, 2), "漲": _up, "跌": _down})

    with st.expander("📊 板塊資金流向", expanded=False):
        import plotly.graph_objects as go
        from src.chart_theme import apply_dark_theme

        _names = [s["板塊"] for s in _sector_summary]
        _vals = [s["平均漲跌%"] for s in _sector_summary]
        _colors = ["#26A69A" if v >= 0 else "#EF5350" for v in _vals]
        fig = go.Figure(go.Bar(x=_names, y=_vals, marker_color=_colors,
                                text=[f"{v:+.2f}%" for v in _vals], textposition="outside"))
        fig.update_layout(height=250, yaxis_title="平均漲跌%", margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(apply_dark_theme(fig), use_container_width=True)

st.divider()

# ─── 未登入 ───
if not user:
    st.markdown("##### 加密貨幣 × 股票 × ETF × 期貨　15 大策略一鍵回測")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("#### 🎯 15 大策略\n雙均線、RSI、MACD、一目均衡表…")
    c2.markdown("#### 🌍 多市場\n加密貨幣 + 美股 + 台股 + ETF + 期貨")
    c3.markdown("#### 📡 即時監控\n訂閱策略、模擬交易記錄")
    c4.markdown("#### 🔒 安全系統\nPBKDF2 加密、帳號保護")
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

    # 用戶統計
    history = db.get_history(user["id"], limit=5)
    stats = db.get_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📊 我的回測", len(db.get_history(user["id"], limit=999)))
    m2.metric("⭐ 收藏策略", len(db.get_favorites(user["id"])))
    m3.metric("👥 平台用戶", stats["total_users"])
    m4.metric("🔥 24h 回測", stats["recent_backtests_24h"])

    st.divider()

    # 快速導航
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("### ₿ 加密回測")
        st.page_link(_crypto_page, label="₿ 加密貨幣", icon="₿")
    with col2:
        st.markdown("### 🏛️ 傳統回測")
        st.page_link(_trad_page, label="🏛️ 傳統市場", icon="🏛️")
    with col3:
        st.markdown("### 📡 策略監控")
        st.page_link("pages/5_📡_監控.py", label="📡 監控", icon="📡")
    with col4:
        st.markdown("### 📜 歷史")
        st.page_link(_history_page, label="📜 歷史", icon="📜")
    with col5:
        if user["role"] == "admin":
            st.markdown("### 🛠️ 管理")
            st.page_link(_admin_page, label="🛠️ 管理", icon="🛠️")
        else:
            st.markdown("### 📰 新聞")
            st.page_link("pages/6_📰_新聞.py", label="📰 新聞", icon="📰")

    # 最近回測
    if history:
        st.divider()
        st.markdown("### 📋 最近回測")
        for h in history[:5]:
            m = h.get("metrics", {})
            ret = m.get("total_return_pct", 0)
            icon = "🟢" if ret and ret > 0 else "🔴" if ret and ret < 0 else "⚪"
            st.markdown(f"{icon} **{h['symbol']}** × {h['strategy']} — {ret}% | {h['timeframe']}")

st.caption("⚠️ 免責聲明：本平台僅供學習與研究，不構成投資建議。數據來源：Yahoo Finance。")
