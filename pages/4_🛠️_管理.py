# 管理員後台
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from src.auth import UserDB
from src.ui_common import apply_theme, breadcrumb, require_admin, sidebar_user_nav

st.set_page_config(page_title="StocksX — 管理後台", page_icon="🛠️", layout="wide")
apply_theme()
breadcrumb("管理後台", "🛠️")

user = require_admin()
db = UserDB()
sidebar_user_nav(user)

st.markdown("## 🛠️ 管理後台")
st.caption(f"管理員：{user['display_name']}")

tab_stats, tab_users, tab_products_admin, tab_security, tab_data = st.tabs(["📊 系統統計", "👥 用戶管理", "📦 產品庫", "🔒 安全日誌", "🗄️ 數據管理"])

# ─── 系統統計 ───
with tab_stats:
    stats = db.get_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 總用戶數", stats["total_users"])
    c2.metric("✅ 活躍用戶", stats["active_users"])
    c3.metric("📊 總回測數", stats["total_backtests"])
    c4.metric("🔥 24h 回測", stats["recent_backtests_24h"])

    if stats["top_symbols"]:
        st.subheader("🏆 熱門標的 Top 10")
        df_top = pd.DataFrame(stats["top_symbols"])
        st.bar_chart(df_top.set_index("symbol")["count"])

    all_users = db.list_users()
    if all_users:
        st.subheader("📈 用戶活躍度")
        active_count = sum(1 for u in all_users if u["last_login"] > 0)
        never_login = sum(1 for u in all_users if u["last_login"] == 0)
        st.markdown(f"- 曾登入用戶：**{active_count}**\n- 從未登入：**{never_login}**")

# ─── 用戶管理 ───
with tab_users:
    users = db.list_users()
    rows = []
    for u in users:
        rows.append({
            "ID": u["id"],
            "帳號": u["username"],
            "暱稱": u["display_name"],
            "角色": "👑 管理員" if u["role"] == "admin" else "👤 用戶",
            "狀態": "✅ 啟用" if u["is_active"] else "⛔ 停用",
            "註冊時間": datetime.fromtimestamp(u["created_at"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "最後登入": datetime.fromtimestamp(u["last_login"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if u["last_login"] else "從未",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.subheader("➕ 新增用戶")
        with st.form("add_user"):
            nu = st.text_input("帳號", key="admin_new_user")
            nn = st.text_input("暱稱", key="admin_new_name")
            np_ = st.text_input("密碼", type="password", key="admin_new_pw")
            nr = st.selectbox("角色", ["user", "admin"], key="admin_new_role")
            if st.form_submit_button("新增"):
                if nu and np_:
                    result = db.register(nu, np_, display_name=nn, role=nr)
                    if result:
                        st.success(f"用戶 {nu} 已建立")
                        st.rerun()
                    else:
                        st.error("帳號已存在")

    with col_b:
        st.subheader("✏️ 修改用戶")
        edit_id = st.number_input("用戶 ID", min_value=1, step=1, key="edit_uid")
        edit_role = st.selectbox("新角色", ["user", "admin"], key="edit_role")
        edit_active = st.selectbox("狀態", [("啟用", 1), ("停用", 0)], format_func=lambda x: x[0], key="edit_active")
        if st.button("💾 更新"):
            db.update_user(int(edit_id), role=edit_role, is_active=edit_active[1])
            st.success("已更新")
            st.rerun()

    with col_c:
        st.subheader("🔑 重設密碼")
        reset_id = st.number_input("用戶 ID", min_value=1, step=1, key="reset_uid")
        reset_pw = st.text_input("新密碼", type="password", key="reset_pw")
        if st.button("🔑 重設"):
            if reset_pw and len(reset_pw) >= 4:
                db.change_password(int(reset_id), reset_pw)
                st.success("密碼已重設")
            else:
                st.error("密碼至少 4 個字元")

    st.divider()
    st.subheader("⚠️ 刪除用戶")
    del_uid = st.number_input("用戶 ID（不可刪除管理員自己）", min_value=1, step=1, key="del_uid_admin")
    if st.button("🗑️ 永久刪除", type="secondary"):
        if int(del_uid) == user["id"]:
            st.error("不能刪除自己")
        else:
            db.delete_user(int(del_uid))
            st.success("用戶及其所有數據已刪除")
            st.rerun()

# ─── 數據管理 ───
with tab_products_admin:
    st.subheader("📦 系統產品庫管理")

    all_prods = db.get_all_products_admin()
    sys_prods = [p for p in all_prods if p.get("is_system")]
    user_prods = [p for p in all_prods if not p.get("is_system")]
    active_prods = [p for p in all_prods if p.get("is_active")]

    m1, m2, m3 = st.columns(3)
    m1.metric("系統產品", len(sys_prods))
    m2.metric("用戶自訂", len(user_prods))
    m3.metric("啟用中", len(active_prods))

    with st.form("admin_add_product"):
        st.markdown("**➕ 新增系統產品**")
        _apc1, _apc2 = st.columns(2)
        with _apc1:
            _admin_sym = st.text_input("代碼", key="admin_p_sym")
            _admin_name = st.text_input("名稱", key="admin_p_name")
            _admin_market = st.selectbox("市場", ["crypto", "traditional"], key="admin_p_mkt")
        with _apc2:
            _admin_ex = st.text_input("交易所", value="binance", key="admin_p_ex")
            _admin_cat = st.text_input("分類", key="admin_p_cat")
        if st.form_submit_button("➕ 新增系統產品", type="primary"):
            if _admin_sym:
                result = db.add_product(_admin_sym, _admin_name, _admin_ex, _admin_market, _admin_cat, user_id=0, is_system=True)
                if isinstance(result, int):
                    st.success(f"✅ 已新增 {_admin_sym}")
                    st.rerun()
                else:
                    st.error(result)

    st.divider()
    st.markdown("**所有產品：**")
    prod_rows = []
    for p in all_prods:
        prod_rows.append({
            "ID": p["id"], "代碼": p["symbol"], "名稱": p["name"],
            "類型": "🔧 系統" if p["is_system"] else f"👤 用戶#{p['user_id']}",
            "市場": p["market_type"], "分類": p["category"], "交易所": p["exchange"],
            "狀態": "✅" if p["is_active"] else "⛔",
        })
    st.dataframe(pd.DataFrame(prod_rows), use_container_width=True, hide_index=True)

    del_prod_id = st.number_input("刪除產品 ID", min_value=1, step=1, key="admin_del_prod")
    if st.button("🗑️ 停用產品"):
        db.delete_product(int(del_prod_id))
        st.success("已停用")
        st.rerun()

with tab_security:
    st.subheader("🔒 登入安全日誌")
    login_logs = db.get_login_log(limit=100)
    if login_logs:
        log_rows = []
        for lg in login_logs:
            log_rows.append({
                "時間": datetime.fromtimestamp(lg["created_at"], tz=timezone.utc).strftime("%m/%d %H:%M:%S"),
                "帳號": lg["username"],
                "結果": "✅ 成功" if lg["success"] else "❌ 失敗",
                "原因": lg.get("reason", ""),
                "IP": lg.get("ip", ""),
            })
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
        fail_count = sum(1 for lg in login_logs if not lg["success"])
        st.metric("最近 100 筆中失敗次數", fail_count)
    else:
        st.info("尚無登入記錄")

with tab_data:
    st.subheader("🗄️ 數據快取管理")
    import os
    import glob

    cache_dir = "cache"
    if os.path.exists(cache_dir):
        files = glob.glob(os.path.join(cache_dir, "*"))
        if files:
            file_rows = []
            total_size = 0
            for f in files:
                size = os.path.getsize(f)
                total_size += size
                file_rows.append({
                    "檔案": os.path.basename(f),
                    "大小": f"{size / 1024:.1f} KB" if size < 1048576 else f"{size / 1048576:.1f} MB",
                    "修改時間": datetime.fromtimestamp(os.path.getmtime(f), tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                })
            st.dataframe(pd.DataFrame(file_rows), use_container_width=True, hide_index=True)
            st.metric("總快取大小", f"{total_size / 1048576:.2f} MB")

            if st.button("🗑️ 清除 K 線快取（不影響用戶數據）"):
                for f in files:
                    if "crypto_cache" in f:
                        os.remove(f)
                st.success("K 線快取已清除")
                st.rerun()
        else:
            st.info("快取目錄為空")
    else:
        st.info("快取目錄不存在")

    st.divider()
    st.subheader("📊 全平台回測記錄")
    all_history_cur = db._conn.execute(
        """SELECT h.*, u.username FROM backtest_history h
           JOIN users u ON h.user_id = u.id ORDER BY h.created_at DESC LIMIT 100"""
    )
    all_history = [dict(r) for r in all_history_cur.fetchall()]
    if all_history:
        ah_rows = []
        for h in all_history:
            ah_rows.append({
                "用戶": h["username"],
                "標的": h["symbol"],
                "策略": h["strategy"],
                "週期": h["timeframe"],
                "時間": datetime.fromtimestamp(h["created_at"], tz=timezone.utc).strftime("%m/%d %H:%M"),
            })
        st.dataframe(pd.DataFrame(ah_rows), use_container_width=True, hide_index=True)
    else:
        st.info("尚無回測記錄")
