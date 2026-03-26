# 頁面共用 UI 邏輯 — 登入檢查、sidebar、麵包屑
from __future__ import annotations

import streamlit as st

from src.auth import UserDB
from src.config import APP_CSS

_db = UserDB()


def apply_theme():
    """套用全局 CSS 主題"""
    st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)


def breadcrumb(page_name: str, icon: str = "📊"):
    """顯示麵包屑導航"""
    st.markdown(f'<p style="font-size:0.85rem;color:#7070a0;">🏠 首頁 › {icon} {page_name}</p>', unsafe_allow_html=True)


def check_session() -> dict | None:
    """檢查登入狀態和 session 過期，回傳 user dict 或 None"""
    user = st.session_state.get("user")
    if user and not _db.validate_session(user):
        st.session_state.pop("user", None)
        st.warning("⏰ 登入已過期，請重新登入")
        return None
    return user


def require_login(page_name: str = "") -> dict:
    """要求登入，未登入則顯示提示並 stop"""
    user = check_session()
    if not user:
        st.warning("⚠️ 請先登入")
        st.page_link("pages/1_🔐_登入.py", label="🔐 前往登入", icon="🔐")
        st.stop()
    return user


def require_admin() -> dict:
    """要求管理員權限"""
    user = require_login()
    if user.get("role") != "admin":
        st.error("⛔ 僅管理員可訪問此頁面")
        st.stop()
    return user


def sidebar_user_nav(user: dict | None = None):
    """統一的 sidebar 用戶導航"""
    if not user:
        user = st.session_state.get("user")

    if user:
        st.sidebar.markdown(f"**👤 {user['display_name']}**")
        _c1, _c2, _c3, _c4 = st.sidebar.columns(4)
        _c1.page_link("pages/2_₿_加密回測.py", label="₿", use_container_width=True)
        _c2.page_link("pages/2_🏛️_傳統回測.py", label="🏛️", use_container_width=True)
        _c3.page_link("pages/3_📜_歷史.py", label="📜", use_container_width=True)
        _c4.page_link("pages/5_📡_交易監控.py", label="📡", use_container_width=True)
        if st.sidebar.button("🚪 登出", use_container_width=True, key=f"logout_{id(user)}"):
            st.session_state.pop("user", None)
            st.switch_page("pages/1_🔐_登入.py")
    else:
        st.sidebar.page_link("pages/1_🔐_登入.py", label="🔐 登入", use_container_width=True)
