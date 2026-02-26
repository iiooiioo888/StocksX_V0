# 回測歷史 & 收藏 & 策略預設 & 提醒
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
from io import BytesIO
from src.auth import UserDB
from src.ui_common import apply_theme, breadcrumb, require_login, sidebar_user_nav

st.set_page_config(page_title="StocksX — 歷史", page_icon="📜", layout="wide")
apply_theme()
breadcrumb("我的空間", "📜")

user = require_login()
db = UserDB()
sidebar_user_nav(user)

st.markdown(f"## 📜 我的空間 — {user['display_name']}")

tab_hist, tab_fav, tab_products, tab_preset, tab_alert, tab_settings = st.tabs(
    ["📋 回測歷史", "⭐ 收藏 & 對比", "📦 我的產品庫", "💾 策略預設", "🔔 提醒設定", "⚙️ 偏好"]
)

# ─── 回測歷史（含筆記/標籤） ───
with tab_hist:
    history = db.get_history(user["id"])
    if not history:
        st.info("尚無回測歷史。")
        st.page_link("pages/2_₿_加密回測.py", label="📊 前往回測", icon="📊")
    else:
        st.caption(f"共 {len(history)} 筆記錄")
        rows = []
        for h in history:
            m = h.get("metrics", {})
            rows.append({
                "ID": h["id"], "⭐": "⭐" if h.get("is_favorite") else "",
                "時間": datetime.fromtimestamp(h["created_at"], tz=timezone.utc).strftime("%m/%d %H:%M"),
                "標的": h["symbol"], "策略": h["strategy"], "週期": h["timeframe"],
                "報酬%": m.get("total_return_pct", 0), "夏普": m.get("sharpe_ratio", 0),
                "回撤%": m.get("max_drawdown_pct", 0), "交易": m.get("num_trades", 0),
                "標籤": h.get("tags", ""), "備註": h.get("notes", ""),
            })
        df = pd.DataFrame(rows)

        def _cr(val):
            try:
                v = float(val)
                return "color:#0d7a0d;font-weight:bold" if v > 0 else "color:#c00;font-weight:bold" if v < 0 else ""
            except (TypeError, ValueError):
                return ""

        st.dataframe(df.style.map(_cr, subset=["報酬%"]), use_container_width=True, hide_index=True)

        csv_buf = BytesIO()
        df.to_csv(csv_buf, index=False, encoding="utf-8-sig")
        st.download_button("📥 匯出歷史 CSV", csv_buf.getvalue(), "history.csv", "text/csv")

        st.divider()
        st.subheader("✏️ 操作")
        op_cols = st.columns(4)
        with op_cols[0]:
            op_id = st.number_input("記錄 ID", min_value=1, step=1, key="op_id")
        with op_cols[1]:
            if st.button("⭐ 切換收藏"):
                db.toggle_favorite(int(op_id))
                st.rerun()
        with op_cols[2]:
            if st.button("🗑️ 刪除"):
                db.delete_history(int(op_id))
                st.rerun()
        with op_cols[3]:
            if st.button("🔄 重新回測", key="rerun_btn"):
                for h in history:
                    if h["id"] == int(op_id):
                        st.session_state["_rerun_config"] = {
                            "symbol": h["symbol"], "exchange": h["exchange"],
                            "timeframe": h["timeframe"], "strategy": h["strategy"],
                            "params": h.get("params", {}),
                        }
                        st.switch_page("pages/2_₿_加密回測.py")

        st.divider()
        st.subheader("📝 編輯備註 & 標籤")
        note_id = st.number_input("記錄 ID", min_value=1, step=1, key="note_id")
        note_text = st.text_input("備註", key="note_text")
        note_tags = st.text_input("標籤（逗號分隔）", placeholder="例: 高夏普, BTC, 短線", key="note_tags")
        if st.button("💾 儲存備註"):
            db.update_notes(int(note_id), note_text, note_tags)
            st.success("✅ 已儲存")
            st.rerun()

# ─── 收藏 & 對比圖 ───
with tab_fav:
    favs = db.get_favorites(user["id"])
    if not favs:
        st.info("尚無收藏。在歷史記錄中點擊 ⭐ 加入。")
    else:
        st.caption(f"共 {len(favs)} 筆收藏")

        # 收藏策略對比圖
        if len(favs) >= 2:
            st.subheader("📊 收藏策略對比")
            fig_cmp = go.Figure()
            cmp_colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#FF6692"]
            cmp_rows = []
            for i, f in enumerate(favs):
                m = f.get("metrics", {})
                label = f"{f['symbol']} × {f['strategy']}"
                cmp_rows.append({
                    "策略": label,
                    "報酬%": m.get("total_return_pct", 0),
                    "夏普": m.get("sharpe_ratio", 0),
                    "回撤%": m.get("max_drawdown_pct", 0),
                    "勝率%": m.get("win_rate_pct", 0),
                })
            df_cmp = pd.DataFrame(cmp_rows)

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(name="報酬%", x=df_cmp["策略"], y=df_cmp["報酬%"],
                                     marker_color=[cmp_colors[i % len(cmp_colors)] for i in range(len(df_cmp))]))
            fig_bar.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), yaxis_title="報酬率 %",
                                  title_text="收藏策略報酬率對比", title_font_size=14)
            st.plotly_chart(fig_bar, use_container_width=True)

            st.dataframe(df_cmp.style.map(_cr, subset=["報酬%", "夏普"]), use_container_width=True, hide_index=True)

        for f in favs:
            m = f.get("metrics", {})
            ret = m.get("total_return_pct", "?")
            icon = "🟢" if ret and ret > 0 else "🔴"
            with st.expander(f"{icon} {f['symbol']} × {f['strategy']} — {ret}%"):
                cols = st.columns(5)
                cols[0].metric("報酬率", f"{m.get('total_return_pct', 0)}%")
                cols[1].metric("夏普", m.get("sharpe_ratio", 0))
                cols[2].metric("回撤", f"{m.get('max_drawdown_pct', 0)}%")
                cols[3].metric("交易數", m.get("num_trades", 0))
                cols[4].metric("勝率", f"{m.get('win_rate_pct', 0)}%")
                st.caption(f"交易所: {f['exchange']} | 週期: {f['timeframe']} | 參數: {f.get('params', {})}")
                if f.get("tags"):
                    st.markdown(f"🏷️ 標籤：{f['tags']}")
                if f.get("notes"):
                    st.markdown(f"📝 {f['notes']}")

# ─── 策略預設 ───
with tab_products:
    st.subheader("📦 我的產品庫")
    st.caption("管理你關注的交易對和股票，訂閱時可直接選擇")

    _my_products = db.get_products(user["id"])
    _sys_count = sum(1 for p in _my_products if p.get("is_system"))
    _user_count = sum(1 for p in _my_products if not p.get("is_system"))
    st.metric("產品總數", f"{len(_my_products)} 個（系統 {_sys_count} + 自訂 {_user_count}）")

    with st.form("add_product"):
        st.markdown("**➕ 新增自訂產品**")
        _ap1, _ap2 = st.columns(2)
        with _ap1:
            _ap_symbol = st.text_input("代碼", placeholder="例: DOGE/USDT:USDT 或 TSLA", key="ap_sym")
            _ap_name = st.text_input("名稱", placeholder="例: Dogecoin 永續", key="ap_name")
            _ap_market = st.selectbox("市場", ["crypto", "traditional"], key="ap_mkt")
        with _ap2:
            _ap_exchange = st.text_input("交易所", value="binance", key="ap_ex")
            _ap_cat = st.text_input("分類", placeholder="例: Meme, 美股, ETF", key="ap_cat")
        if st.form_submit_button("➕ 新增", type="primary"):
            if _ap_symbol:
                result = db.add_product(_ap_symbol, _ap_name, _ap_exchange, _ap_market, _ap_cat, user["id"])
                if isinstance(result, int):
                    st.success(f"✅ 已新增 {_ap_symbol}")
                    st.rerun()
                else:
                    st.error(result)

    if _my_products:
        _user_prods = [p for p in _my_products if not p.get("is_system")]
        if _user_prods:
            st.markdown("**我的自訂產品：**")
            for p in _user_prods:
                _pc1, _pc2, _pc3 = st.columns([3, 1, 1])
                _pc1.markdown(f"**{p['symbol']}** — {p['name']}　`{p['category']}`　{p['exchange']}")
                if _pc3.button("🗑️", key=f"del_prod_{p['id']}"):
                    db.delete_product(p["id"])
                    st.rerun()

        with st.expander("📋 系統預設產品", expanded=False):
            _sys_prods = [p for p in _my_products if p.get("is_system")]
            _sys_df = pd.DataFrame([{"代碼": p["symbol"], "名稱": p["name"], "分類": p["category"],
                                     "交易所": p["exchange"]} for p in _sys_prods])
            st.dataframe(_sys_df, use_container_width=True, hide_index=True)

with tab_preset:
    st.subheader("💾 我的策略預設")
    st.caption("儲存常用的回測參數組合，一鍵載入使用")

    presets = db.get_presets(user["id"])

    with st.form("save_preset"):
        st.markdown("**新增預設**")
        preset_name = st.text_input("預設名稱", placeholder="例: BTC 短線 MACD")
        pc1, pc2 = st.columns(2)
        with pc1:
            p_symbol = st.text_input("標的", value="BTC/USDT:USDT", key="p_sym")
            p_exchange = st.text_input("交易所", value="okx", key="p_ex")
            p_timeframe = st.selectbox("週期", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3, key="p_tf")
        with pc2:
            p_strategy = st.selectbox("策略", ["sma_cross", "buy_and_hold", "rsi_signal", "macd_cross", "bollinger_signal"], key="p_strat")
            p_equity = st.number_input("初始資金", value=10000.0, step=500.0, key="p_eq")
            p_leverage = st.number_input("槓桿", value=1.0, min_value=1.0, max_value=125.0, key="p_lev")
        if st.form_submit_button("💾 儲存預設", type="primary"):
            if preset_name:
                config = {"symbol": p_symbol, "exchange": p_exchange, "timeframe": p_timeframe,
                          "strategy": p_strategy, "initial_equity": p_equity, "leverage": p_leverage}
                db.save_preset(user["id"], preset_name, config)
                st.success(f"✅ 預設「{preset_name}」已儲存")
                st.rerun()
            else:
                st.error("請輸入預設名稱")

    if presets:
        st.divider()
        for p in presets:
            c = p["config"]
            with st.expander(f"📋 {p['name']}"):
                st.json(c)
                pc1, pc2 = st.columns(2)
                with pc1:
                    if st.button("📊 載入並回測", key=f"load_{p['id']}"):
                        st.session_state["_rerun_config"] = c
                        st.switch_page("pages/2_₿_加密回測.py")
                with pc2:
                    if st.button("🗑️ 刪除", key=f"del_preset_{p['id']}"):
                        db.delete_preset(p["id"])
                        st.rerun()
    else:
        st.info("尚無儲存的預設。填寫上方表單新增。")

# ─── 提醒設定 ───
with tab_alert:
    st.subheader("🔔 回測提醒")
    st.caption("設定條件，當回測結果達到閾值時自動提示")

    alerts = db.get_alerts(user["id"])

    with st.form("add_alert"):
        st.markdown("**新增提醒**")
        a1, a2, a3 = st.columns(3)
        with a1:
            a_symbol = st.text_input("標的（留空=全部）", value="", key="a_sym")
        with a2:
            a_type = st.selectbox("條件", [
                ("報酬率 ≥", "return_above"), ("報酬率 ≤", "return_below"),
                ("回撤 ≥", "drawdown_above"), ("夏普 ≥", "sharpe_above"),
            ], format_func=lambda x: x[0], key="a_type")
        with a3:
            a_threshold = st.number_input("閾值 (%)", value=10.0, step=1.0, key="a_thr")
        a_msg = st.text_input("自訂提醒訊息", placeholder="例: BTC 短線策略報酬率達標！", key="a_msg")
        if st.form_submit_button("➕ 新增提醒", type="primary"):
            db.add_alert(user["id"], a_symbol or "*", a_type[1], a_threshold, a_msg)
            st.success("✅ 提醒已新增")
            st.rerun()

    if alerts:
        st.divider()
        condition_labels = {"return_above": "報酬 ≥", "return_below": "報酬 ≤",
                           "drawdown_above": "回撤 ≥", "sharpe_above": "夏普 ≥"}
        for a in alerts:
            cond = condition_labels.get(a["condition_type"], a["condition_type"])
            cols = st.columns([3, 1])
            cols[0].markdown(f"🔔 **{a['symbol']}** — {cond} **{a['threshold']}%**"
                            + (f"　📝 {a['message']}" if a["message"] else ""))
            if cols[1].button("🗑️", key=f"del_alert_{a['id']}"):
                db.delete_alert(a["id"])
                st.rerun()
    else:
        st.info("尚無提醒。設定條件後，回測結果達標時會自動通知。")

# ─── 偏好設定 ───
with tab_settings:
    st.subheader("⚙️ 偏好設定")
    settings = db.get_settings(user["id"])
    new_name = st.text_input("暱稱", value=user.get("display_name", ""))
    default_equity = st.number_input("預設初始資金", value=float(settings.get("default_equity", 10000)), step=500.0)
    default_leverage = st.number_input("預設槓桿", value=float(settings.get("default_leverage", 1)),
                                       min_value=1.0, max_value=125.0)
    if st.button("💾 儲存設定", type="primary"):
        if new_name != user.get("display_name"):
            db.update_user(user["id"], display_name=new_name)
            st.session_state["user"]["display_name"] = new_name
        db.save_settings(user["id"], {"default_equity": default_equity, "default_leverage": default_leverage})
        st.success("✅ 設定已儲存")

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
                st.success("✅ 密碼已修改")
