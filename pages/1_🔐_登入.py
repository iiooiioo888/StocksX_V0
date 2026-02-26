# 登入 / 註冊頁面（安全強化版）
import streamlit as st
from src.auth import UserDB
from src.ui_common import apply_theme

st.set_page_config(page_title="StocksX — 登入", page_icon="🔐", layout="centered")
apply_theme()

db = UserDB()

if st.session_state.get("user"):
    u = st.session_state["user"]
    if not db.validate_session(u):
        st.session_state.pop("user", None)
        st.warning("⏰ 登入已過期，請重新登入")
        st.rerun()
    st.success(f"✅ 已登入：{u['display_name']}（{'👑 管理員' if u['role'] == 'admin' else '👤 用戶'}）")
    col1, col2 = st.columns(2)
    col1.page_link("pages/2_📊_回測.py", label="📊 前往回測", icon="📊")
    col2.page_link("pages/3_📜_歷史.py", label="📜 歷史記錄", icon="📜")
    if st.button("🚪 登出"):
        st.session_state.pop("user", None)
        st.rerun()
    st.stop()

st.markdown("## 🔐 StocksX 安全登入")

tab_login, tab_register = st.tabs(["登入", "註冊"])

with tab_login:
    with st.form("login_form"):
        username = st.text_input("帳號", max_chars=50)
        password = st.text_input("密碼", type="password", max_chars=100)
        submitted = st.form_submit_button("登入", type="primary", use_container_width=True)
        if submitted:
            if not db.check_rate_limit(f"login_{username}", max_calls=10, period=60):
                st.error("🚫 登入嘗試過於頻繁，請稍後再試")
            else:
                result = db.login(username, password)
                if isinstance(result, dict):
                    st.session_state["user"] = result
                    st.session_state["_login_time"] = __import__("time").time()
                    st.success(f"歡迎，{result['display_name']}！")
                    st.switch_page("pages/2_📊_回測.py")
                else:
                    st.error(f"🔒 {result}")
    st.caption("🔒 連續登入失敗 5 次將鎖定帳號 5 分鐘")

with tab_register:
    with st.form("register_form"):
        new_user = st.text_input("帳號（3-50 字元，字母數字底線）", max_chars=50, key="reg_user")
        new_name = st.text_input("暱稱", max_chars=100, key="reg_name")
        new_pw = st.text_input("密碼（至少 6 字元，需含字母和數字）", type="password", max_chars=100, key="reg_pw")
        new_pw2 = st.text_input("確認密碼", type="password", max_chars=100, key="reg_pw2")
        reg_submitted = st.form_submit_button("註冊", type="primary", use_container_width=True)
        if reg_submitted:
            if new_pw != new_pw2:
                st.error("兩次密碼不一致")
            elif not db.check_rate_limit("register", max_calls=5, period=300):
                st.error("🚫 註冊嘗試過於頻繁，請 5 分鐘後再試")
            else:
                result = db.register(new_user, new_pw, display_name=new_name)
                if isinstance(result, dict):
                    st.success("✅ 註冊成功！請切換到「登入」分頁")
                else:
                    st.error(f"❌ {result}")

st.divider()
st.caption("🔒 安全措施：PBKDF2 密碼雜湊 | 帳號鎖定保護 | 輸入消毒 | Session 過期")
