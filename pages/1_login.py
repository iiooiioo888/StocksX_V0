# 登入 / 註冊頁面
import streamlit as st
from src.auth import UserDB

st.set_page_config(page_title="StocksX — 登入", page_icon="🔐", layout="centered")

db = UserDB()

if st.session_state.get("user"):
    st.success(f"✅ 已登入：{st.session_state['user']['display_name']}（{st.session_state['user']['role']}）")
    if st.button("登出", type="primary"):
        st.session_state.pop("user", None)
        st.rerun()
    st.page_link("pages/2_backtest.py", label="前往回測", icon="📊")
    st.stop()

st.markdown("## 🔐 StocksX 登入")

tab_login, tab_register = st.tabs(["登入", "註冊"])

with tab_login:
    with st.form("login_form"):
        username = st.text_input("帳號", key="login_user")
        password = st.text_input("密碼", type="password", key="login_pw")
        submitted = st.form_submit_button("登入", type="primary", use_container_width=True)
        if submitted:
            if not username or not password:
                st.error("請輸入帳號和密碼")
            else:
                user = db.login(username, password)
                if user:
                    st.session_state["user"] = user
                    st.success(f"歡迎回來，{user['display_name']}！")
                    st.rerun()
                else:
                    st.error("帳號或密碼錯誤")
    st.caption("預設管理員：admin / admin123")

with tab_register:
    with st.form("register_form"):
        new_user = st.text_input("帳號", key="reg_user")
        new_name = st.text_input("暱稱", key="reg_name")
        new_pw = st.text_input("密碼", type="password", key="reg_pw")
        new_pw2 = st.text_input("確認密碼", type="password", key="reg_pw2")
        reg_submitted = st.form_submit_button("註冊", type="primary", use_container_width=True)
        if reg_submitted:
            if not new_user or not new_pw:
                st.error("帳號和密碼為必填")
            elif new_pw != new_pw2:
                st.error("兩次密碼不一致")
            elif len(new_pw) < 4:
                st.error("密碼至少 4 個字元")
            else:
                result = db.register(new_user, new_pw, display_name=new_name)
                if result:
                    st.success("註冊成功！請切換到「登入」分頁登入。")
                else:
                    st.error("帳號已存在")
