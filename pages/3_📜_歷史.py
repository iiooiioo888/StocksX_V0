# 回測歷史（增強版 v5.0 - 詳細視圖）
# 功能：分頁、篩選、排序、對比、匯出、統計、詳細視圖

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.auth import UserDB
from src.config import STRATEGY_LABELS
from src.core import get_orchestrator
from src.ui_backtest_detail import render_backtest_detail
from src.ui_history_enhanced import (
    filter_history,
    paginate_data,
    render_comparison_chart,
    render_comparison_selector,
    render_comparison_table,
    render_export_buttons,
    render_filters,
    render_pagination,
    render_sort_controls,
    render_statistics,
    sort_history,
)

st.set_page_config(page_title="StocksX — 歷史記錄", page_icon="📜", layout="wide")

# ════════════════════════════════════════════════════════════
# CSS 樣式
# ════════════════════════════════════════════════════════════
CUSTOM_CSS = """
.stApp {background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #0f1724 100%);}

.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid rgba(110,168,254,0.1);
}

.page-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: #f0f0ff;
    margin: 0;
}

.page-subtitle {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-top: 5px;
}

/* 表格樣式優化 */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(110,168,254,0.1);
}

/* 績效顏色 */
.perf-positive {color: #00cc96 !important;}
.perf-negative {color: #ef553b !important;}
"""

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 頁面初始化
# ════════════════════════════════════════════════════════════
user = st.session_state.get("user")

if not user:
    st.warning("請先登入")
    st.page_link("pages/1_🔐_登入.py", label="前往登入")
    st.stop()

db = UserDB()

# ════════════════════════════════════════════════════════════
# 頁面標題
# ════════════════════════════════════════════════════════════
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(
        """
    <div class="page-header">
        <div>
            <h1 class="page-title">📜 回測歷史</h1>
            <div class="page-subtitle">查看、篩選、對比您的回測記錄</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    if st.button("🔄 重新整理", use_container_width=True):
        # 清除快取
        st.cache_data.clear()
        st.rerun()


# ════════════════════════════════════════════════════════════
# 載入數據
# ════════════════════════════════════════════════════════════
@st.cache_data(ttl=30, show_spinner=False)
def load_history(user_id: int, limit: int = 500):
    """載入歷史記錄（快取 30 秒）"""
    return db.get_history(user_id, limit)


# 初始化頁碼
if "history_page" not in st.session_state:
    st.session_state["history_page"] = 1

# 載入數據
all_history = load_history(user["id"])

# ════════════════════════════════════════════════════════════
# 統計分析
# ════════════════════════════════════════════════════════════
render_statistics(all_history)

st.divider()

# ════════════════════════════════════════════════════════════
# 篩選器
# ════════════════════════════════════════════════════════════
filters = render_filters(key_prefix="history_filter")

# 應用篩選
filtered_history = filter_history(all_history, **filters)

# 顯示篩選結果
st.caption(f"找到 {len(filtered_history)} 筆記錄（總共 {len(all_history)} 筆）")

# ════════════════════════════════════════════════════════════
# 排序
# ════════════════════════════════════════════════════════════
# 初始化排序設定
if "history_sort_by" not in st.session_state:
    st.session_state["history_sort_by"] = "created_at"
if "history_sort_asc" not in st.session_state:
    st.session_state["history_sort_asc"] = False

sort_by, ascending = render_sort_controls(
    st.session_state["history_sort_by"], st.session_state["history_sort_asc"], key_prefix="history_sort"
)

st.session_state["history_sort_by"] = sort_by
st.session_state["history_sort_asc"] = ascending

# 應用排序
sorted_history = sort_history(filtered_history, sort_by, ascending)

# ════════════════════════════════════════════════════════════
# 分頁
# ════════════════════════════════════════════════════════════
PAGE_SIZE = 20

# 取得當前頁碼
current_page = st.session_state.get("history_page", 1)

# 分頁數據
paginated = paginate_data(sorted_history, current_page, PAGE_SIZE)

# 顯示分頁控制
render_pagination(paginated["total_pages"], paginated["page"], key_prefix="history")

st.divider()

# ════════════════════════════════════════════════════════════
# 歷史記錄表格
# ════════════════════════════════════════════════════════════
st.markdown(f"#### 📋 回測記錄（第 {paginated['page']} / {paginated['total_pages']} 頁）")

if paginated["items"]:
    # 準備表格數據
    table_data = []

    for item in paginated["items"]:
        metrics = item.get("metrics", {})

        # 報酬率顏色
        return_pct = metrics.get("total_return_pct", 0)
        return_class = "perf-positive" if return_pct > 0 else "perf-negative"

        table_data.append(
            {
                "ID": item.get("id"),
                "日期": datetime.fromtimestamp(item.get("created_at", 0), tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "策略": STRATEGY_LABELS.get(item.get("strategy", ""), item.get("strategy")),
                "交易對": f"{item.get('symbol', '')}",
                "時間框架": item.get("timeframe", ""),
                "報酬率": f"<span class='{return_class}'>{return_pct:+.2f}%</span>",
                "Sharpe": f"{metrics.get('sharpe', 0):.2f}",
                "最大回撤": f"{metrics.get('max_drawdown_pct', 0):.2f}%",
                "勝率": f"{metrics.get('win_rate', 0):.1f}%",
                "收藏": "⭐" if item.get("is_favorite") else "",
            }
        )

    # 顯示表格
    df = pd.DataFrame(table_data)

    # 使用 st.html 渲染 HTML（支援顏色）
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.TextColumn("ID", width="small"),
            "日期": st.column_config.TextColumn("日期", width="medium"),
            "策略": st.column_config.TextColumn("策略", width="medium"),
            "交易對": st.column_config.TextColumn("交易對", width="medium"),
            "時間框架": st.column_config.TextColumn("時間框架", width="small"),
            "報酬率": st.column_config.TextColumn("報酬率", width="small"),
            "Sharpe": st.column_config.TextColumn("Sharpe", width="small"),
            "最大回撤": st.column_config.TextColumn("最大回撤", width="small"),
            "勝率": st.column_config.TextColumn("勝率", width="small"),
            "收藏": st.column_config.TextColumn("收藏", width="small"),
        },
    )

    # 單筆操作
    st.markdown("##### 🔧 單筆操作")

    action_cols = st.columns(5)

    selected_id = action_cols[0].number_input(
        "記錄 ID",
        min_value=1,
        max_value=max(item.get("id", 1) for item in all_history),
        value=paginated["items"][0].get("id") if paginated["items"] else 1,
        key="action_id",
    )

    if action_cols[1].button("👁️ 查看詳情", use_container_width=True, key="view_detail_btn"):
        # 找到對應記錄
        detail_item = next((item for item in all_history if item.get("id") == selected_id), None)
        if detail_item:
            st.session_state["detail_item"] = detail_item
            st.rerun()

    if action_cols[2].button("⭐ 加入收藏", use_container_width=True, key="togglefav_btn"):
        db.toggle_favorite(selected_id)
        st.success("已更新收藏狀態")
        st.cache_data.clear()
        st.rerun()

# ════════════════════════════════════════════════════════════
# 詳細視圖
# ════════════════════════════════════════════════════════════
if st.session_state.get("detail_item"):
    detail_item = st.session_state["detail_item"]

    st.divider()

    # 返回按鈕
    if st.button("⬅️ 返回記錄列表", key="back_to_list"):
        st.session_state["detail_item"] = None
        st.rerun()

    st.divider()

    # 渲染詳細視圖
    render_backtest_detail(detail_item)
else:
    # 單筆操作（只在沒有顯示詳細視圖時顯示）
    st.markdown("##### 🔧 單筆操作")

    action_cols = st.columns(5)

    selected_id = action_cols[0].number_input(
        "記錄 ID",
        min_value=1,
        max_value=max(item.get("id", 1) for item in all_history),
        value=paginated["items"][0].get("id") if paginated["items"] else 1,
        key="action_id",
    )

    if action_cols[1].button("👁️ 查看詳情", use_container_width=True, key="view_detail_btn"):
        # 找到對應記錄
        detail_item = next((item for item in all_history if item.get("id") == selected_id), None)
        if detail_item:
            st.session_state["detail_item"] = detail_item
            st.rerun()

    if action_cols[2].button("⭐ 加入收藏", use_container_width=True, key="togglefav_btn"):
        db.toggle_favorite(selected_id)
        st.success("已更新收藏狀態")
        st.cache_data.clear()
        st.rerun()

    if action_cols[3].button("📝 編輯備註", use_container_width=True, key="edit_note_btn"):
        st.session_state["edit_note_id"] = selected_id
        st.rerun()

    if action_cols[4].button("🗑️ 刪除記錄", use_container_width=True, key="delete_btn", type="secondary"):
        db.delete_history(selected_id)
        st.success("已刪除記錄")
        st.cache_data.clear()
        st.rerun()

    # 編輯備註對話框
    if st.session_state.get("edit_note_id"):
        note_item = next((item for item in all_history if item.get("id") == st.session_state["edit_note_id"]), None)
        if note_item:
            with st.form("edit_note_form"):
                new_note = st.text_area("備註", value=note_item.get("notes", ""), height=100)
                if st.form_submit_button("💾 儲存"):
                    db.update_notes(st.session_state["edit_note_id"], new_note)
                    st.success("已更新")
                    st.cache_data.clear()
                    st.session_state["edit_note_id"] = None
                    st.rerun()

st.divider()

# ════════════════════════════════════════════════════════════
# 多筆對比
# ════════════════════════════════════════════════════════════
selected_items = render_comparison_selector(sorted_history, max_select=5, key_prefix="history_compare")

if selected_items:
    render_comparison_chart(selected_items)
    render_comparison_table(selected_items)

st.divider()

# ════════════════════════════════════════════════════════════
# 匯出功能
# ════════════════════════════════════════════════════════════
render_export_buttons(sorted_history, key_prefix="history_export")

# ════════════════════════════════════════════════════════════
# 詳情視窗
# ════════════════════════════════════════════════════════════
if st.session_state.get("detail_item"):
    item = st.session_state["detail_item"]

    with st.expander(f"📊 記錄詳情 (ID: {item.get('id')})", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**基本資訊**")
            st.write(f"- 策略：{STRATEGY_LABELS.get(item.get('strategy', ''), item.get('strategy'))}")
            st.write(f"- 交易對：{item.get('symbol', '')}")
            st.write(f"- 交易所：{item.get('exchange', '')}")
            st.write(f"- 時間框架：{item.get('timeframe', '')}")
            st.write(
                f"- 建立時間：{datetime.fromtimestamp(item.get('created_at', 0), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
            )

        with col2:
            st.markdown("**績效指標**")
            metrics = item.get("metrics", {})
            st.write(f"- 總報酬：{metrics.get('total_return_pct', 0):+.2f}%")
            st.write(f"- 年化報酬：{metrics.get('annual_return_pct', 0):+.2f}%")
            st.write(f"- Sharpe: {metrics.get('sharpe', 0):.2f}")
            st.write(f"- 最大回撤：{metrics.get('max_drawdown_pct', 0):.2f}%")
            st.write(f"- 勝率：{metrics.get('win_rate', 0):.1f}%")
            st.write(f"- 利潤因子：{metrics.get('profit_factor', 0):.2f}")

        # 備註
        st.markdown("**備註**")
        st.write(item.get("notes", "無"))

        # 參數
        st.markdown("**策略參數**")
        st.json(item.get("params", {}))
