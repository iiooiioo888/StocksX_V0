# 回測歷史 & 收藏 & 策略預設 & 提醒（現代化緊湊版 v2）
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
from io import BytesIO
from src.auth import UserDB
from src.config import STRATEGY_LABELS, STRATEGY_COLORS

st.set_page_config(page_title="StocksX — 歷史", page_icon="📜", layout="wide")

# ════════════════════════════════════════════════════════════
# CSS 樣式 - 現代化緊湊版
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
/* 全局 */
.stApp {background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #0f1724 100%);}

/* 頁面標題 */
.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 15px;
    padding-bottom: 12px;
    border-bottom: 1px solid #2a2a4a;
}
.page-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f0f0ff;
}

/* 標籤樣式 */
.tag {
    display: inline-block;
    padding: 2px 6px;
    margin: 1px;
    background: rgba(110,168,254,0.12);
    color: #6ea8fe;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
}

/* 指標卡片 */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1a1a2e, #1f1f3a);
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 10px 12px;
}
[data-testid="stMetricValue"] {font-size: 1.2rem !important; color: #6ea8fe !important;}
[data-testid="stMetricLabel"] {font-size: 0.7rem !important; color: #64748b !important;}

/* 績效顏色 */
.perf-positive {color: #00cc96 !important;}
.perf-negative {color: #ef553b !important;}

/* Tab 優化 */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(26,26,46,0.5);
    border-radius: 8px;
    padding: 3px;
    border: 1px solid #2a2a4a;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4a6cf7, #6366f1) !important;
    color: white !important;
}

/* 按鈕優化 */
.stButton > button {
    border-radius: 6px !important;
    font-size: 0.8rem !important;
    padding: 5px 10px !important;
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(110,168,254,0.3);
}

/* 展開區塊 */
.streamlit-expanderHeader {
    background: rgba(26,26,46,0.4) !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
}

/* 表格 */
.dataframe {
    font-size: 0.8rem;
    background: rgba(26,26,46,0.3) !important;
}

/* 輸入框 */
.stTextInput input, .stNumberInput input {
    font-size: 0.85rem !important;
    padding: 6px 10px !important;
}

/* 側邊欄 */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
    border-right: 1px solid #2a2a4a;
}
"""

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 頁面導航與用戶驗證
# ════════════════════════════════════════════════════════════
from src.ui_common import require_login

user = require_login()
db = UserDB()

# 頁面標題
st.markdown("""
<div class="page-header">
    <div class="page-title">📜 我的空間</div>
    <div style="font-size:0.85rem;color:#94a3b8;">
        🏠 <a href="/" style="color:#6ea8fe;text-decoration:none;">首頁</a> › 我的空間
    </div>
</div>
""", unsafe_allow_html=True)

# 側邊欄用戶資訊
with st.sidebar:
    st.markdown(f"### 👤 {user['display_name']}")
    st.caption(f"{'👑 管理員' if user['role'] == 'admin' else '👤 用戶'}")
    st.divider()
    stats = db.get_stats()
    st.metric("📊 我的回測", len(db.get_history(user["id"], limit=999)))
    st.metric("⭐ 收藏策略", len(db.get_favorites(user["id"])))
    if st.button("🚪 登出", use_container_width=True):
        st.session_state.pop("user", None)
        st.switch_page("app.py")

# 主標籤頁 - 緊湊版
tabs = st.tabs([
    "📋 回測歷史",
    "⭐ 收藏", 
    "📦 產品庫",
    "💾 策略預設",
    "🔔 提醒",
    "⚙️ 設定"
])

# ════════════════════════════════════════════════════════════
# Tab 1: 回測歷史
# ════════════════════════════════════════════════════════════
with tabs[0]:
    history = db.get_history(user["id"], limit=100)
    
    if not history:
        st.info("📭 尚無回測歷史")
        st.page_link("pages/2_₿_加密回測.py", label="📊 開始第一次回測", icon="📊", use_container_width=True)
    else:
        # 頂部工具列 - 緊湊版
        tool_col1, tool_col2, tool_col3 = st.columns([3, 1, 1])
        with tool_col1:
            search_query = st.text_input("🔍", placeholder="搜索標的、策略、標籤...", label_visibility="collapsed")
        with tool_col2:
            sort_by = st.selectbox("排序", ["時間", "報酬%", "夏普", "回撤%"], label_visibility="collapsed")
        with tool_col3:
            if st.button("📥 CSV", use_container_width=True):
                rows = []
                for h in history:
                    m = h.get("metrics", {})
                    rows.append({
                        "ID": h["id"],
                        "時間": datetime.fromtimestamp(h["created_at"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                        "標的": h["symbol"],
                        "策略": h["strategy"],
                        "週期": h["timeframe"],
                        "報酬%": m.get("total_return_pct", 0),
                        "夏普": m.get("sharpe_ratio", 0),
                        "回撤%": m.get("max_drawdown_pct", 0),
                        "交易數": m.get("num_trades", 0),
                        "標籤": h.get("tags", ""),
                        "備註": h.get("notes", ""),
                    })
                df_export = pd.DataFrame(rows)
                csv_buf = BytesIO()
                df_export.to_csv(csv_buf, index=False, encoding="utf-8-sig")
                st.download_button("📥 下載", csv_buf.getvalue(), "history.csv", "text/csv")
        
        st.divider()
        
        # 篩選與排序
        if search_query:
            history = [h for h in history if 
                      search_query.lower() in h["symbol"].lower() or
                      search_query.lower() in h["strategy"].lower() or
                      search_query.lower() in (h.get("tags") or "").lower() or
                      search_query.lower() in (h.get("notes") or "").lower()]
        
        # 排序
        sort_map = {"時間": "created_at", "報酬%": "total_return_pct", "夏普": "sharpe_ratio", "回撤%": "max_drawdown_pct"}
        sort_key = sort_map.get(sort_by, "created_at")
        reverse = sort_by != "回撤%"
        
        if sort_key == "created_at":
            history.sort(key=lambda x: x.get(sort_key, 0), reverse=reverse)
        else:
            history.sort(key=lambda x: x.get("metrics", {}).get(sort_key, 0), reverse=reverse)
        
        st.caption(f"共 {len(history)} 筆記錄")
        
        # 卡片式佈局 - 每排 3 個（更緊湊）
        for i in range(0, len(history), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j >= len(history):
                    break
                h = history[i + j]
                m = h.get("metrics", {})
                ret = m.get("total_return_pct", 0)
                
                strategy_name = STRATEGY_LABELS.get(h["strategy"], h["strategy"])
                time_str = datetime.fromtimestamp(h["created_at"], tz=timezone.utc).strftime("%m/%d %H:%M")

                with col:
                    # 卡片標題區
                    title_col1, title_col2 = st.columns([3, 2])
                    with title_col1:
                        fav_icon = "⭐" if h.get("is_favorite") else ""
                        symbol_display = h['symbol'].strip()
                        st.markdown(f"**{fav_icon} {symbol_display}**")
                        st.caption(f"{strategy_name[:12]} · {h['timeframe']}")
                    with title_col2:
                        ret_color = "🟢" if ret > 0 else "🔴" if ret < 0 else "⚪"
                        st.markdown(f"### {ret:+.2f}% {ret_color}")
                    
                    st.divider()
                    
                    # 指標區 - 使用 5 個小 column（更清晰）
                    metric_cols = st.columns(5)
                    with metric_cols[0]:
                        st.markdown(f"<div style='text-align:center;'><div style='font-size:1rem;font-weight:700;color:#6ea8fe;'>{m.get('sharpe_ratio', 0):.2f}</div><div style='font-size:0.65rem;color:#64748b;margin-top:2px;'>夏普</div></div>", unsafe_allow_html=True)
                    with metric_cols[1]:
                        st.markdown(f"<div style='text-align:center;'><div style='font-size:1rem;font-weight:700;color:#6ea8fe;'>{m.get('max_drawdown_pct', 0):.1f}%</div><div style='font-size:0.65rem;color:#64748b;margin-top:2px;'>回撤</div></div>", unsafe_allow_html=True)
                    with metric_cols[2]:
                        st.markdown(f"<div style='text-align:center;'><div style='font-size:1rem;font-weight:700;color:#6ea8fe;'>{m.get('num_trades', 0)}</div><div style='font-size:0.65rem;color:#64748b;margin-top:2px;'>交易</div></div>", unsafe_allow_html=True)
                    with metric_cols[3]:
                        st.markdown(f"<div style='text-align:center;'><div style='font-size:1rem;font-weight:700;color:#6ea8fe;'>{m.get('win_rate_pct', 0):.0f}%</div><div style='font-size:0.65rem;color:#64748b;margin-top:2px;'>勝率</div></div>", unsafe_allow_html=True)
                    with metric_cols[4]:
                        profit_val = m.get('total_profit', 0)
                        profit_color = "#00cc96" if profit_val >= 0 else "#ef553b"
                        st.markdown(f"<div style='text-align:center;'><div style='font-size:1rem;font-weight:700;color:{profit_color};'>{profit_val:.0f}</div><div style='font-size:0.65rem;color:#64748b;margin-top:2px;'>利潤</div></div>", unsafe_allow_html=True)
                    
                    # 標籤區
                    if h.get("tags"):
                        tags_text = " | ".join([t.strip() for t in h.get("tags", "").split(",") if t.strip()])
                        if tags_text:
                            st.markdown(f"<div style='font-size:0.75rem;color:#94a3b8;margin:6px 0;'>🏷️ {tags_text}</div>", unsafe_allow_html=True)
                    
                    # 備註區（截斷顯示）
                    if h.get("notes"):
                        notes = h.get("notes", "")
                        notes_display = notes[:35] + "..." if len(notes) > 35 else notes
                        st.markdown(f"<div style='font-size:0.75rem;color:#94a3b8;margin:4px 0;'>📝 {notes_display}</div>", unsafe_allow_html=True)
                    
                    # 時間區
                    st.caption(f"🕐 {time_str}")
                    
                    # 操作按鈕
                    st.divider()
                    btn_cols = st.columns(3)
                    with btn_cols[0]:
                        if st.button("✏️ 編輯", key=f"edit_{h['id']}", use_container_width=True):
                            st.session_state["edit_id"] = h["id"]
                            st.session_state["edit_notes"] = h.get("notes", "")
                            st.session_state["edit_tags"] = h.get("tags", "")
                            st.rerun()
                    with btn_cols[1]:
                        fav_text = "⭐ 收藏" if not h.get("is_favorite") else "已收藏"
                        if st.button(fav_text, key=f"fav_{h['id']}", use_container_width=True):
                            db.toggle_favorite(h["id"])
                            st.rerun()
                    with btn_cols[2]:
                        # 刪除按鈕 - 二次確認
                        del_key = f"del_{h['id']}"
                        if del_key not in st.session_state:
                            st.session_state[del_key] = False
                        
                        if not st.session_state[del_key]:
                            if st.button("🗑️ 刪除", key=del_key, use_container_width=True, type="secondary"):
                                st.session_state[del_key] = True
                                st.session_state["confirm_del_id"] = h["id"]
                                st.session_state["confirm_del_symbol"] = h["symbol"]
                                st.rerun()
                        else:
                            if st.button("❓ 確定？", key=f"confirm_{h['id']}", use_container_width=True, type="primary"):
                                db.delete_history(h["id"])
                                st.session_state.pop(del_key, None)
                                st.session_state.pop("confirm_del_id", None)
                                st.session_state.pop("confirm_del_symbol", None)
                                st.success(f"✅ 已刪除 {h['symbol']}")
                                st.rerun()
                            if st.button("❌ 取消", key=f"cancel_{h['id']}", use_container_width=True):
                                st.session_state[del_key] = False
                                st.rerun()
        
        # 編輯備註彈窗
        if "edit_id" in st.session_state:
            st.divider()
            st.markdown("### ✏️ 編輯備註 & 標籤")
            st.info(f"編輯記錄 ID: {st.session_state['edit_id']}")
            edit_col1, edit_col2 = st.columns(2)
            with edit_col1:
                new_notes = st.text_input("備註", value=st.session_state.get("edit_notes", ""), key="new_notes")
            with edit_col2:
                new_tags = st.text_input("標籤", value=st.session_state.get("edit_tags", ""),
                                        placeholder="例：高夏普，BTC, 短線", key="new_tags")

            action_cols = st.columns(3)
            with action_cols[0]:
                if st.button("💾 儲存", use_container_width=True, key="save_notes"):
                    db.update_notes(st.session_state["edit_id"], new_notes, new_tags)
                    st.session_state.pop("edit_id", None)
                    st.success("✅ 已儲存")
                    st.rerun()
            with action_cols[1]:
                if st.button("❌ 取消", use_container_width=True, key="cancel_edit"):
                    st.session_state.pop("edit_id", None)
                    st.rerun()
            with action_cols[2]:
                if st.button("🗑️ 刪除記錄", use_container_width=True, key="del_edit", type="secondary"):
                    # 二次確認
                    if "confirm_edit_delete" not in st.session_state:
                        st.session_state["confirm_edit_delete"] = False
                    
                    if not st.session_state["confirm_edit_delete"]:
                        st.session_state["confirm_edit_delete"] = True
                        st.warning(f"⚠️ 確定要刪除記錄 ID {st.session_state['edit_id']} 嗎？")
                        st.stop()
                    else:
                        db.delete_history(st.session_state["edit_id"])
                        st.session_state.pop("edit_id", None)
                        st.session_state.pop("edit_notes", None)
                        st.session_state.pop("edit_tags", None)
                        st.session_state.pop("confirm_edit_delete", None)
                        st.success("✅ 已刪除")
                        st.rerun()
            
            if st.session_state.get("confirm_edit_delete"):
                action_cols_2 = st.columns(2)
                with action_cols_2[0]:
                    if st.button("✅ 確定刪除", use_container_width=True, key="confirm_edit_yes", type="primary"):
                        db.delete_history(st.session_state["edit_id"])
                        st.session_state.pop("edit_id", None)
                        st.session_state.pop("edit_notes", None)
                        st.session_state.pop("edit_tags", None)
                        st.session_state.pop("confirm_edit_delete", None)
                        st.success("✅ 已刪除")
                        st.rerun()
                with action_cols_2[1]:
                    if st.button("❌ 取消", use_container_width=True, key="confirm_edit_no"):
                        st.session_state.pop("confirm_edit_delete", None)
                        st.rerun()
        
        # 批量操作
        st.divider()
        st.markdown("#### 📦 批量操作")
        batch_cols = st.columns(4)
        with batch_cols[0]:
            batch_ids = st.text_input("記錄 ID（逗號分隔）", placeholder="1,2,3")
        with batch_cols[1]:
            if st.button("⭐ 批量收藏", use_container_width=True):
                if batch_ids:
                    for id_str in batch_ids.split(","):
                        try:
                            db.toggle_favorite(int(id_str.strip()))
                        except:
                            pass
                    st.rerun()
        with batch_cols[2]:
            if st.button("🗑️ 批量刪除", use_container_width=True):
                if batch_ids:
                    # 二次確認
                    if "confirm_batch_delete" not in st.session_state:
                        st.session_state["confirm_batch_delete"] = False
                    
                    if not st.session_state["confirm_batch_delete"]:
                        st.session_state["confirm_batch_delete"] = True
                        st.session_state["batch_delete_ids"] = batch_ids
                        st.warning("⚠️ 確定要刪除這些記錄嗎？此操作無法復原！")
                        st.stop()
                    else:
                        count = 0
                        for id_str in st.session_state["batch_delete_ids"].split(","):
                            try:
                                db.delete_history(int(id_str.strip()))
                                count += 1
                            except:
                                pass
                        st.session_state.pop("confirm_batch_delete", None)
                        st.session_state.pop("batch_delete_ids", None)
                        st.success(f"✅ 已刪除 {count} 筆記錄")
                        st.rerun()
        with batch_cols[3]:
            if st.button("🔄 批量回測", use_container_width=True):
                if batch_ids:
                    for id_str in batch_ids.split(","):
                        try:
                            hid = int(id_str.strip())
                            for h in history:
                                if h["id"] == hid:
                                    st.session_state["_rerun_config"] = {
                                        "symbol": h["symbol"],
                                        "exchange": h["exchange"],
                                        "timeframe": h["timeframe"],
                                        "strategy": h["strategy"],
                                        "params": h.get("params", {}),
                                    }
                                    st.switch_page("pages/2_₿_加密回測.py")
                        except:
                            pass
        
        # 📈 報酬趨勢圖表
        st.divider()
        st.markdown("#### 📈 報酬趨勢分析")
        
        # 依標的分組統計
        symbol_stats = {}
        for h in history:
            sym = h["symbol"]
            if sym not in symbol_stats:
                symbol_stats[sym] = []
            symbol_stats[sym].append({
                "time": h["created_at"],
                "return": h.get("metrics", {}).get("total_return_pct", 0),
                "strategy": h.get("strategy", "")
            })
        
        # 每個標的按時間排序
        for sym in symbol_stats:
            symbol_stats[sym].sort(key=lambda x: x["time"])
        
        # 顯示前 6 個標的的趨勢圖
        top_symbols = sorted(symbol_stats.items(), key=lambda x: len(x[1]), reverse=True)[:6]
        
        if top_symbols:
            chart_config = {'displayModeBar': False, 'responsive': True}
            
            # 使用 tabs 顯示不同標的
            symbol_tabs = st.tabs([f"{sym[:10]} ({len(data)}次)" for sym, data in top_symbols])
            
            for tab, (sym, data) in zip(symbol_tabs, top_symbols):
                with tab:
                    # 累積報酬曲線
                    cumulative = []
                    total = 0
                    timestamps = []
                    strategies = []
                    
                    for d in data:
                        total += d["return"]
                        cumulative.append(total)
                        timestamps.append(datetime.fromtimestamp(d["time"], tz=timezone.utc).strftime("%m/%d"))
                        strategies.append(STRATEGY_LABELS.get(d["strategy"], d["strategy"][:10]))
                    
                    # 繪製折線圖
                    import plotly.graph_objects as go
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=timestamps,
                        y=cumulative,
                        mode='lines+markers',
                        line=dict(color='#6ea8fe', width=2.5),
                        marker=dict(size=6),
                        text=[f"{s}<br>{y:+.2f}%" for s, y in zip(strategies, cumulative)],
                        hoverinfo='text'
                    ))
                    
                    # 添加零軸線
                    fig.add_shape(
                        type="line",
                        x0=timestamps[0], x1=timestamps[-1],
                        y0=0, y1=0,
                        line=dict(color="#64748b", width=1, dash="dash")
                    )
                    
                    final_ret = cumulative[-1] if cumulative else 0
                    line_color = "#00cc96" if final_ret >= 0 else "#ef553b"
                    
                    fig.update_layout(
                        title=dict(text=f"📈 {sym} 累積報酬趨勢", font_size=14, font=dict(color='#e0e0e8')),
                        xaxis=dict(tickfont=dict(color='#94a3b8')),
                        yaxis=dict(
                            title="累積報酬 %",
                            gridcolor='rgba(50,50,90,0.3)',
                            tickfont=dict(color='#94a3b8')
                        ),
                        height=280,
                        margin=dict(l=40, r=20, t=35, b=40),
                        showlegend=False,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(30,30,50,0.3)',
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, key=f"trend_{sym}", config=chart_config)
                    
                    # 顯示統計數據
                    stat_cols = st.columns(4)
                    stat_cols[0].metric("總報酬", f"{final_ret:+.2f}%")
                    stat_cols[1].metric("平均報酬", f"{sum(cumulative)/len(cumulative):.2f}%" if cumulative else "0%")
                    stat_cols[2].metric("最大獲利", f"{max(cumulative):.2f}%" if cumulative else "0%")
                    stat_cols[3].metric("最大虧損", f"{min(cumulative):.2f}%" if cumulative else "0%")

# ════════════════════════════════════════════════════════════
# Tab 2: 收藏 & 對比
# ════════════════════════════════════════════════════════════
with tabs[1]:
    favs = db.get_favorites(user["id"])

    if not favs:
        st.info("⭐ 尚無收藏。在歷史記錄中點擊 ⭐ 加入。")
    else:
        st.caption(f"共 {len(favs)} 筆收藏")
        
        # 對比圖表
        if len(favs) >= 2:
            st.markdown("#### 📊 收藏策略對比")
            
            cmp_data = []
            for f in favs:
                m = f.get("metrics", {})
                cmp_data.append({
                    "策略": f"{f['symbol']} × {f['strategy']}",
                    "報酬%": m.get("total_return_pct", 0),
                    "夏普": m.get("sharpe_ratio", 0),
                    "回撤%": m.get("max_drawdown_pct", 0),
                })
            df_cmp = pd.DataFrame(cmp_data)
            
            chart_config = {'displayModeBar': False, 'responsive': True}
            chart_cols = st.columns(2)
            
            with chart_cols[0]:
                import plotly.graph_objects as go
                
                colors = ["#00cc96" if v > 0 else "#ef553b" for v in df_cmp["報酬%"]]
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    x=df_cmp["策略"],
                    y=df_cmp["報酬%"],
                    marker_color=colors,
                    text=df_cmp["報酬%"].apply(lambda x: f"{x:+.2f}%"),
                    textposition="outside",
                    hoverinfo='xy'
                ))
                fig_bar.update_layout(
                    title=dict(text="報酬率對比", font_size=13, font=dict(color='#e0e0e8')),
                    height=260,
                    margin=dict(l=30, r=20, t=30, b=50),
                    yaxis=dict(title="報酬率 %", gridcolor='rgba(50,50,90,0.3)', tickfont=dict(color='#94a3b8')),
                    xaxis=dict(tickfont=dict(color='#94a3b8'), tickangle=45),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(30,30,50,0.3)',
                )
                st.plotly_chart(fig_bar, use_container_width=True, key="fav_bar_chart", config=chart_config)
            
            with chart_cols[1]:
                import plotly.graph_objects as go
                
                fig_radar = go.Figure()
                plotly_colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#FF6692']
                
                for i, f in enumerate(favs[:6]):
                    m = f.get("metrics", {})
                    label = f"{f['symbol'][:8]} · {f['strategy'][:6]}"
                    fig_radar.add_trace(go.Scatterpolar(
                        r=[
                            max(-100, min(100, m.get("total_return_pct", 0))),
                            max(0, min(5, m.get("sharpe_ratio", 0))) * 20,
                            max(-100, min(0, -m.get("max_drawdown_pct", 0))),
                            max(0, min(100, m.get("win_rate_pct", 0))),
                        ],
                        theta=["報酬", "夏普", "回撤", "勝率"],
                        name=label,
                        fill="toself",
                        line=dict(color=plotly_colors[i % len(plotly_colors)], width=2),
                        opacity=0.7
                    ))
                fig_radar.update_layout(
                    title=dict(text="多維度雷達圖", font_size=13, font=dict(color='#e0e0e8')),
                    height=260,
                    margin=dict(l=30, r=30, t=30, b=20),
                    polar=dict(
                        radialaxis=dict(visible=True, gridcolor='rgba(50,50,90,0.3)', tickfont=dict(color='#94a3b8')),
                        bgcolor='rgba(30,30,50,0.3)'
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(font=dict(color='#94a3b8', size=8), bgcolor='rgba(0,0,0,0.3)')
                )
                st.plotly_chart(fig_radar, use_container_width=True, key="fav_radar", config=chart_config)
        
        st.divider()
        
        # 收藏卡片列表
        for f in favs:
            m = f.get("metrics", {})
            ret = m.get("total_return_pct", 0)
            strategy_name = STRATEGY_LABELS.get(f["strategy"], f["strategy"])
            
            # 清理標題
            clean_symbol = f["symbol"].strip()
            expander_title = f'**{clean_symbol}** × {strategy_name[:15]} — {"🟢" if ret > 0 else "🔴" if ret < 0 else "⚪"} {ret:+.2f}%'
            
            with st.expander(expander_title, expanded=False):
                # 指標區
                metric_cols = st.columns(5)
                with metric_cols[0]:
                    st.markdown(f"<div style='text-align:center;'><div style='font-size:1.1rem;font-weight:700;color:#6ea8fe;'>{m.get("total_return_pct", 0):+.2f}%</div><div style='font-size:0.7rem;color:#64748b;margin-top:3px;'>報酬</div></div>", unsafe_allow_html=True)
                with metric_cols[1]:
                    st.markdown(f"<div style='text-align:center;'><div style='font-size:1.1rem;font-weight:700;color:#6ea8fe;'>{m.get('sharpe_ratio', 0):.2f}</div><div style='font-size:0.7rem;color:#64748b;margin-top:3px;'>夏普</div></div>", unsafe_allow_html=True)
                with metric_cols[2]:
                    st.markdown(f"<div style='text-align:center;'><div style='font-size:1.1rem;font-weight:700;color:#6ea8fe;'>{m.get('max_drawdown_pct', 0):.1f}%</div><div style='font-size:0.7rem;color:#64748b;margin-top:3px;'>回撤</div></div>", unsafe_allow_html=True)
                with metric_cols[3]:
                    st.markdown(f"<div style='text-align:center;'><div style='font-size:1.1rem;font-weight:700;color:#6ea8fe;'>{m.get('num_trades', 0)}</div><div style='font-size:0.7rem;color:#64748b;margin-top:3px;'>交易</div></div>", unsafe_allow_html=True)
                with metric_cols[4]:
                    st.markdown(f"<div style='text-align:center;'><div style='font-size:1.1rem;font-weight:700;color:#6ea8fe;'>{m.get('win_rate_pct', 0):.0f}%</div><div style='font-size:0.7rem;color:#64748b;margin-top:3px;'>勝率</div></div>", unsafe_allow_html=True)
                
                st.divider()
                
                st.caption(f"🏦 交易所：{f['exchange']}  |  📅 週期：{f['timeframe']}")
                
                if f.get("params"):
                    with st.popover("📋 參數"):
                        st.json(f.get("params", {}))
                
                if f.get("tags") or f.get("notes"):
                    info_cols = st.columns(2)
                    with info_cols[0]:
                        if f.get("tags"):
                            st.markdown("**🏷️ 標籤**")
                            for tag in f["tags"].split(","):
                                if tag.strip():
                                    st.markdown(f'<span class="tag">{tag.strip()}</span>', unsafe_allow_html=True)
                    with info_cols[1]:
                        if f.get("notes"):
                            st.markdown("**📝 備註**")
                            st.caption(f.get("notes", ""))
                
                action_cols = st.columns(3)
                with action_cols[0]:
                    if st.button("📊 重新回測", key=f"rerun_fav_{f['id']}", use_container_width=True):
                        st.session_state["_rerun_config"] = {
                            "symbol": f["symbol"],
                            "exchange": f["exchange"],
                            "timeframe": f["timeframe"],
                            "strategy": f["strategy"],
                            "params": f.get("params", {}),
                        }
                        st.switch_page("pages/2_₿_加密回測.py")
                with action_cols[1]:
                    if st.button("⭐ 取消收藏", key=f"unfav_{f['id']}", use_container_width=True):
                        db.toggle_favorite(f["id"])
                        st.rerun()
                with action_cols[2]:
                    # 刪除按鈕 - 二次確認
                    del_key = f"del_fav_{f['id']}"
                    if del_key not in st.session_state:
                        st.session_state[del_key] = False
                    
                    if not st.session_state[del_key]:
                        if st.button("🗑️ 刪除", key=del_key, use_container_width=True, type="secondary"):
                            st.session_state[del_key] = True
                            st.session_state[f"confirm_del_{f['id']}"] = True
                            st.rerun()
                    else:
                        if st.button("❓ 確定？", key=f"confirm_del_{f['id']}", use_container_width=True, type="primary"):
                            db.delete_history(f["id"])
                            st.session_state.pop(del_key, None)
                            st.session_state.pop(f"confirm_del_{f['id']}", None)
                            st.success(f"✅ 已刪除 {clean_symbol}")
                            st.rerun()
                        if st.button("❌ 取消", key=f"cancel_del_{f['id']}", use_container_width=True):
                            st.session_state[del_key] = False
                            st.rerun()

# ════════════════════════════════════════════════════════════
# Tab 3: 產品庫
# ════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("#### 📦 產品庫")
    st.caption("管理關注的交易對和股票")
    
    products = db.get_products(user["id"])
    sys_count = sum(1 for p in products if p.get("is_system"))
    user_count = sum(1 for p in products if not p.get("is_system"))
    
    stat_cols = st.columns(3)
    stat_cols[0].metric("總數", f"{len(products)}")
    stat_cols[1].metric("系統", f"{sys_count}")
    stat_cols[2].metric("自訂", f"{user_count}")
    
    st.divider()
    
    # 新增產品表單
    with st.expander("➕ 新增產品", expanded=False):
        with st.form("add_product"):
            p_cols = st.columns(4)
            with p_cols[0]:
                p_symbol = st.text_input("代碼", placeholder="DOGE/USDT")
                p_name = st.text_input("名稱", placeholder="Dogecoin")
            with p_cols[1]:
                p_market = st.selectbox("市場", ["crypto", "traditional"])
                p_exchange = st.text_input("交易所", value="binance")
            with p_cols[2]:
                p_category = st.text_input("分類", placeholder="Meme")
            with p_cols[3]:
                st.markdown("<div style='padding-top:20px;'></div>", unsafe_allow_html=True)
                if st.form_submit_button("💾 儲存", use_container_width=True):
                    if p_symbol:
                        result = db.add_product(p_symbol, p_name, p_exchange, p_market, p_category, user["id"])
                        if isinstance(result, int):
                            st.success(f"✅ 已新增 {p_symbol}")
                            st.rerun()
                        else:
                            st.error(result)
    
    # 產品列表
    if products:
        user_prods = [p for p in products if not p.get("is_system")]
        if user_prods:
            st.markdown("##### 自訂產品")
            for p in user_prods:
                prod_cols = st.columns([4, 2, 1])
                prod_cols[0].markdown(f"**{p['symbol']}** — {p['name']}　`{p['category']}`")
                prod_cols[1].caption(f"交易所：{p['exchange']}")
                if prod_cols[2].button("🗑️", key=f"del_prod_{p['id']}", type="secondary"):
                    db.delete_product(p["id"])
                    st.rerun()
        
        sys_prods = [p for p in products if p.get("is_system")]
        if sys_prods:
            with st.expander("📋 系統預設", expanded=False):
                sys_df = pd.DataFrame([{
                    "代碼": p["symbol"],
                    "名稱": p["name"],
                    "分類": p["category"],
                    "交易所": p["exchange"]
                } for p in sys_prods])
                st.dataframe(sys_df, use_container_width=True, hide_index=True, height=250)

# ════════════════════════════════════════════════════════════
# Tab 4: 策略預設
# ════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("#### 💾 策略預設")
    st.caption("儲存常用參數組合")
    
    presets = db.get_presets(user["id"])
    
    with st.expander("➕ 新增預設", expanded=False):
        with st.form("save_preset"):
            preset_name = st.text_input("名稱", placeholder="BTC 短線 MACD")
            pc1, pc2 = st.columns(2)
            with pc1:
                p_symbol = st.text_input("標的", value="BTC/USDT:USDT")
                p_exchange = st.text_input("交易所", value="okx")
                p_timeframe = st.selectbox("週期", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3)
            with pc2:
                p_strategy = st.selectbox("策略", list(STRATEGY_LABELS.keys()), format_func=lambda x: STRATEGY_LABELS.get(x, x))
                p_equity = st.number_input("資金", value=10000.0, step=500.0)
                p_leverage = st.number_input("槓桿", value=1.0, min_value=1.0, max_value=125.0)
            
            if st.form_submit_button("💾 儲存", use_container_width=True):
                if preset_name:
                    config = {
                        "symbol": p_symbol,
                        "exchange": p_exchange,
                        "timeframe": p_timeframe,
                        "strategy": p_strategy,
                        "initial_equity": p_equity,
                        "leverage": p_leverage
                    }
                    db.save_preset(user["id"], preset_name, config)
                    st.success(f"✅「{preset_name}」已儲存")
                    st.rerun()
    
    if presets:
        st.divider()
        preset_cols = st.columns(3)
        for idx, p in enumerate(presets):
            col = preset_cols[idx % 3]
            c = p["config"]
            with col:
                with st.expander(f"📋 {p['name']}"):
                    st.json(c)
                    if st.button("📊 載入回測", key=f"load_{p['id']}", use_container_width=True):
                        st.session_state["_rerun_config"] = c
                        st.switch_page("pages/2_₿_加密回測.py")
                    if st.button("🗑️ 刪除", key=f"del_preset_{p['id']}", use_container_width=True):
                        db.delete_preset(p["id"])
                        st.rerun()

# ════════════════════════════════════════════════════════════
# Tab 5: 提醒設定
# ════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("#### 🔔 提醒")
    st.caption("回測達標自動通知")
    
    alerts = db.get_alerts(user["id"])
    
    with st.expander("➕ 新增提醒", expanded=False):
        with st.form("add_alert"):
            a_cols = st.columns(3)
            with a_cols[0]:
                a_symbol = st.text_input("標的", value="", placeholder="留空=全部")
            with a_cols[1]:
                a_type = st.selectbox("條件", [
                    ("報酬 ≥", "return_above"),
                    ("報酬 ≤", "return_below"),
                    ("回撤 ≥", "drawdown_above"),
                    ("夏普 ≥", "sharpe_above"),
                ], format_func=lambda x: x[0])
            with a_cols[2]:
                a_threshold = st.number_input("閾值 %", value=10.0, step=1.0)
            a_msg = st.text_input("提醒訊息", placeholder="達標通知！")
            
            if st.form_submit_button("➕ 新增", use_container_width=True):
                db.add_alert(user["id"], a_symbol or "*", a_type[1], a_threshold, a_msg)
                st.success("✅ 已新增")
                st.rerun()
    
    if alerts:
        st.divider()
        condition_labels = {
            "return_above": "報酬 ≥",
            "return_below": "報酬 ≤",
            "drawdown_above": "回撤 ≥",
            "sharpe_above": "夏普 ≥"
        }
        
        for a in alerts:
            cond = condition_labels.get(a["condition_type"], a["condition_type"])
            alert_cols = st.columns([4, 1])
            alert_cols[0].markdown(f"🔔 **{a['symbol']}** — {cond} **{a['threshold']}%**" +
                                  (f" 💬 {a['message']}" if a["message"] else ""))
            if alert_cols[1].button("🗑️", key=f"del_alert_{a['id']}", type="secondary"):
                db.delete_alert(a["id"])
                st.rerun()

# ════════════════════════════════════════════════════════════
# Tab 6: 偏好設定
# ════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("#### ⚙️ 設定")
    
    settings = db.get_settings(user["id"])
    
    setting_cols = st.columns(2)
    with setting_cols[0]:
        new_name = st.text_input("暱稱", value=user.get("display_name", ""))
        default_equity = st.number_input("預設資金", value=float(settings.get("default_equity", 10000)), step=500.0)
    with setting_cols[1]:
        default_leverage = st.number_input("預設槓桿", value=float(settings.get("default_leverage", 1)),
                                           min_value=1.0, max_value=125.0)
    
    if st.button("💾 儲存", type="primary"):
        if new_name != user.get("display_name"):
            db.update_user(user["id"], display_name=new_name)
            st.session_state["user"]["display_name"] = new_name
        db.save_settings(user["id"], {"default_equity": default_equity, "default_leverage": default_leverage})
        st.success("✅ 已儲存")
    
    st.divider()
    
    st.markdown("#### 🔑 修改密碼")
    with st.form("change_pw"):
        pw_cols = st.columns(3)
        with pw_cols[0]:
            old_pw = st.text_input("目前密碼", type="password")
        with pw_cols[1]:
            new_pw = st.text_input("新密碼", type="password")
        with pw_cols[2]:
            new_pw2 = st.text_input("確認", type="password")
        
        if st.form_submit_button("修改密碼", use_container_width=True):
            if not db.login(user["username"], old_pw):
                st.error("目前密碼錯誤")
            elif new_pw != new_pw2:
                st.error("密碼不一致")
            elif len(new_pw) < 4:
                st.error("密碼至少 4 個字元")
            else:
                db.change_password(user["id"], new_pw)
                st.success("✅ 已修改")
