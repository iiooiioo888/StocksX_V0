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

from src.data.market_overview import (
    fetch_market_data,
    fetch_yahoo_reference_futures,
    fetch_yahoo_reference_trending,
)

with st.spinner("載入市場行情…"):
    market_data = fetch_market_data()

# ─── 參考 Yahoo Finance：熱門標的與期貨報價 ───
with st.spinner("載入 Yahoo Finance 參考行情…"):
    yahoo_futures = fetch_yahoo_reference_futures()
    yahoo_trending = fetch_yahoo_reference_trending()

if yahoo_futures or yahoo_trending:
    st.markdown("### 📈 參考 [Yahoo Finance](https://finance.yahoo.com/)：熱門標的與期貨")
    col_futures, col_trending = st.columns(2)
    with col_futures:
        st.caption("期貨報價")
        _cols_per_row = 2
        for i in range(0, len(yahoo_futures), _cols_per_row):
            row = yahoo_futures[i : i + _cols_per_row]
            cols = st.columns(_cols_per_row)
            for c, item in zip(cols, row):
                _chg = item["change"]
                _icon = "🟢" if _chg > 0 else "🔴" if _chg < 0 else "⚪"
                c.metric(
                    f"{_icon} {item['name']}",
                    format_price(item["price"]),
                    delta=f"{_chg:+.2f}%",
                    delta_color="normal" if _chg >= 0 else "inverse",
                )
    with col_trending:
        st.caption("熱門標的")
        for i in range(0, len(yahoo_trending), _cols_per_row):
            row = yahoo_trending[i : i + _cols_per_row]
            cols = st.columns(_cols_per_row)
            for c, item in zip(cols, row):
                _chg = item["change"]
                _icon = "🟢" if _chg > 0 else "🔴" if _chg < 0 else "⚪"
                c.metric(
                    f"{_icon} {item['name']}",
                    format_price(item["price"]),
                    delta=f"{_chg:+.2f}%",
                    delta_color="normal" if _chg >= 0 else "inverse",
                )
    st.divider()

if market_data:
    # 一級：資產類別 | 二級：交易類型(現貨/期貨/期權) | 三級：板塊
    st.caption("🌍 一級：資產類別　｜　二級：交易類型　｜　三級：板塊")
    group_tabs = st.tabs(list(market_data.keys()))
    _cols_per_row = 4
    for gtab, (group_name, instruments) in zip(group_tabs, market_data.items()):
        with gtab:
            st.caption(f"{group_name} — 交易類型與板塊即時行情")
            instrument_tabs = st.tabs(list(instruments.keys()))
            for itab, (instrument_name, sectors) in zip(instrument_tabs, instruments.items()):
                with itab:
                    st.caption(f"交易類型：{instrument_name}")
                    sector_tabs = st.tabs(list(sectors.keys()))
                    for stab, (sector, items) in zip(sector_tabs, sectors.items()):
                        with stab:
                            for _row_start in range(0, len(items), _cols_per_row):
                                _row_items = items[_row_start:_row_start + _cols_per_row]
                                cols = st.columns(_cols_per_row)
                                for col, item in zip(cols, _row_items):
                                    _chg = item["change"]
                                    _icon = "🟢" if _chg > 0 else "🔴" if _chg < 0 else "⚪"
                                    _delta_color = "normal" if _chg >= 0 else "inverse"
                                    col.metric(
                                        f"{_icon} {item['name']}",
                                        format_price(item["price"]),
                                        delta=f"{_chg:+.2f}%",
                                        delta_color=_delta_color,
                                    )

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
        st.page_link(_crypto_page, label="₿ 加密貨幣", icon="💰")
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

st.caption(
    "⚠️ 免責聲明：本平台僅供學習與研究，不構成投資建議。"
    " 數據與參考來源：[Yahoo Finance](https://finance.yahoo.com/)。"
)
