# StocksX — 通用回測平台入口
"""
啟動方式：streamlit run app.py
多頁面架構：
  - 登入/註冊
  - 回測主頁
  - 回測歷史 & 收藏
  - 管理員後台
"""
import streamlit as st

st.set_page_config(page_title="StocksX — 通用回測平台", page_icon="📊", layout="wide")

st.markdown("""<style>
[data-testid="stMetric"] {background:#f8f9fb;border:1px solid #e0e3e8;border-radius:10px;padding:12px 16px;}
[data-testid="stMetric"] [data-testid="stMetricValue"] {font-size:1.3rem;}
div[data-testid="stExpander"] {border:1px solid #e0e3e8;border-radius:8px;}
</style>""", unsafe_allow_html=True)

user = st.session_state.get("user")

if not user:
    st.markdown("## 📊 StocksX — 通用回測平台")
    st.info("👈 請先登入或註冊帳號")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.markdown("#### 🎯 五大策略\n雙均線、買入持有、RSI、MACD、布林帶")
    col_b.markdown("#### 📈 多市場\n加密貨幣 + 美股 + 台股 + ETF + 期貨")
    col_c.markdown("#### 📜 歷史記錄\n儲存回測結果、收藏最優策略")
    col_d.markdown("#### 🛠️ 管理後台\n用戶管理、系統統計、數據管理")
    st.page_link("pages/1_login.py", label="🔐 前往登入 / 註冊", icon="🔐")
else:
    st.sidebar.markdown(f"### 👤 {user['display_name']}")
    st.sidebar.caption(f"角色：{'👑 管理員' if user['role'] == 'admin' else '👤 用戶'}")
    if st.sidebar.button("登出", use_container_width=True):
        st.session_state.pop("user", None)
        st.rerun()
    st.sidebar.divider()

    st.markdown(f"## 📊 歡迎回來，{user['display_name']}！")
    st.markdown("選擇功能開始使用：")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📊 執行回測")
        st.markdown("五大策略回測、K 線圖、權益曲線、統計分析")
        st.page_link("pages/2_backtest.py", label="前往回測", icon="📊")
    with col2:
        st.markdown("### 📜 歷史 & 收藏")
        st.markdown("查看回測記錄、管理收藏策略、偏好設定")
        st.page_link("pages/3_history.py", label="前往歷史", icon="📜")
    with col3:
        if user["role"] == "admin":
            st.markdown("### 🛠️ 管理後台")
            st.markdown("用戶管理、系統統計、數據快取管理")
            st.page_link("pages/4_admin.py", label="前往管理", icon="🛠️")
        else:
            st.markdown("### ⚙️ 設定")
            st.markdown("修改暱稱、密碼、預設回測參數")
            st.page_link("pages/3_history.py", label="前往設定", icon="⚙️")

st.caption("⚠️ 免責聲明：本平台僅供學習與研究，不構成投資建議。")
