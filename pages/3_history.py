# 回測歷史 & 收藏
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from io import BytesIO
from src.auth import UserDB

st.set_page_config(page_title="StocksX — 歷史", page_icon="📜", layout="wide")

if not st.session_state.get("user"):
    st.warning("⚠️ 請先登入")
    st.page_link("pages/1_login.py", label="前往登入", icon="🔐")
    st.stop()

user = st.session_state["user"]
db = UserDB()

st.markdown(f"## 📜 回測歷史 — {user['display_name']}")

tab_hist, tab_fav, tab_settings = st.tabs(["📋 全部歷史", "⭐ 收藏策略", "⚙️ 偏好設定"])

with tab_hist:
    history = db.get_history(user["id"])
    if not history:
        st.info("尚無回測歷史。執行回測後會自動保存。")
    else:
        st.caption(f"共 {len(history)} 筆記錄")
        rows = []
        for h in history:
            m = h.get("metrics", {})
            rows.append({
                "ID": h["id"],
                "時間": datetime.fromtimestamp(h["created_at"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "標的": h["symbol"],
                "交易所": h["exchange"],
                "週期": h["timeframe"],
                "策略": h["strategy"],
                "報酬%": m.get("total_return_pct", "-"),
                "夏普": m.get("sharpe_ratio", "-"),
                "回撤%": m.get("max_drawdown_pct", "-"),
                "⭐": "⭐" if h.get("is_favorite") else "",
                "備註": h.get("notes", ""),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv_buf = BytesIO()
        df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
        st.download_button("📥 匯出歷史 CSV", csv_buf.getvalue(), "backtest_history.csv", "text/csv")

        col1, col2 = st.columns(2)
        with col1:
            fav_id = st.number_input("輸入 ID 加入/移除收藏", min_value=1, step=1, key="fav_id")
            if st.button("⭐ 切換收藏"):
                db.toggle_favorite(int(fav_id))
                st.rerun()
        with col2:
            del_id = st.number_input("輸入 ID 刪除記錄", min_value=1, step=1, key="del_id")
            if st.button("🗑️ 刪除", type="secondary"):
                db.delete_history(int(del_id))
                st.success("已刪除")
                st.rerun()

with tab_fav:
    favs = db.get_favorites(user["id"])
    if not favs:
        st.info("尚無收藏。在歷史記錄中點擊 ⭐ 加入收藏。")
    else:
        st.caption(f"共 {len(favs)} 筆收藏")
        for f in favs:
            m = f.get("metrics", {})
            with st.expander(f"⭐ {f['symbol']} × {f['strategy']} — 報酬 {m.get('total_return_pct', '?')}%"):
                cols = st.columns(5)
                cols[0].metric("報酬率", f"{m.get('total_return_pct', 0)}%")
                cols[1].metric("夏普", m.get("sharpe_ratio", 0))
                cols[2].metric("回撤", f"{m.get('max_drawdown_pct', 0)}%")
                cols[3].metric("交易數", m.get("num_trades", 0))
                cols[4].metric("勝率", f"{m.get('win_rate_pct', 0)}%")
                st.caption(f"交易所: {f['exchange']} | 週期: {f['timeframe']} | 參數: {f.get('params', {})}")
                st.caption(f"備註: {f.get('notes', '-')}")

with tab_settings:
    st.subheader("⚙️ 偏好設定")
    settings = db.get_settings(user["id"])
    new_name = st.text_input("暱稱", value=user.get("display_name", ""))
    default_equity = st.number_input("預設初始資金", value=float(settings.get("default_equity", 10000)), step=500.0)
    default_leverage = st.number_input("預設槓桿", value=float(settings.get("default_leverage", 1)), min_value=1.0, max_value=125.0)

    if st.button("💾 儲存設定", type="primary"):
        if new_name != user.get("display_name"):
            db.update_user(user["id"], display_name=new_name)
            st.session_state["user"]["display_name"] = new_name
        db.save_settings(user["id"], {"default_equity": default_equity, "default_leverage": default_leverage})
        st.success("設定已儲存")

    st.divider()
    st.subheader("🔑 修改密碼")
    with st.form("change_pw"):
        old_pw = st.text_input("目前密碼", type="password")
        new_pw = st.text_input("新密碼", type="password")
        new_pw2 = st.text_input("確認新密碼", type="password")
        if st.form_submit_button("修改密碼"):
            if not db.login(user["username"], old_pw):
                st.error("目前密碼錯誤")
            elif new_pw != new_pw2:
                st.error("兩次密碼不一致")
            elif len(new_pw) < 4:
                st.error("密碼至少 4 個字元")
            else:
                db.change_password(user["id"], new_pw)
                st.success("密碼已修改")
