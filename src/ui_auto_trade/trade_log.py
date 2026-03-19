"""
交易日誌 UI
============
顯示和分析交易記錄
"""

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.auth.user_db import UserDB


def render_trade_log_viewer(user_id: int):
    """
    渲染交易日誌查看器

    包含：
    - 交易記錄表格
    - 績效統計
    - 圖表分析
    - 匯出功能
    """
    db = UserDB()

    st.markdown("### 📜 交易日誌")

    # 獲取所有持倉
    watchlist = db.get_watchlist(user_id)

    if not watchlist:
        st.info("ℹ️ 尚無交易記錄")
        return

    # 側邊欄 - 篩選器
    with st.sidebar:
        st.markdown("#### 🔍 篩選器")

        # 時間範圍
        date_range = st.date_input(
            "時間範圍",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
        )

        # 交易對
        symbols = list(set(w["symbol"] for w in watchlist))
        selected_symbols = st.multiselect(
            "交易對",
            options=symbols,
            default=symbols,
        )

        # 交易類型
        trade_type = st.selectbox(
            "交易類型",
            options=["全部", "開倉", "平倉"],
            index=0,
        )

        # 損益篩選
        pnl_filter = st.radio(
            "損益",
            options=["全部", "獲利", "虧損"],
            index=0,
        )

    # 收集所有交易記錄
    all_trades = []

    for w in watchlist:
        if w["symbol"] not in selected_symbols:
            continue

        trades = db.get_trade_log(w["id"], limit=200)
        for t in trades:
            t["watch_symbol"] = w["symbol"]
            t["watch_strategy"] = w.get("strategy", "N/A")
            all_trades.append(t)

    if not all_trades:
        st.info("ℹ️ 無符合條件的交易記錄")
        return

    # 轉換為 DataFrame
    df = pd.DataFrame(all_trades)

    # 時間篩選
    if isinstance(date_range, tuple):
        start_date = datetime.combine(date_range[0], datetime.min.time()).timestamp()
        end_date = datetime.combine(date_range[1], datetime.max.time()).timestamp()

        df = df[(df["created_at"] >= start_date) & (df["created_at"] <= end_date)]

    # 交易類型篩選
    if trade_type != "全部":
        df = df[df["action"] == trade_type]

    # 損益篩選
    if pnl_filter == "獲利":
        df = df[df["pnl_amount"] > 0]
    elif pnl_filter == "虧損":
        df = df[df["pnl_amount"] < 0]

    # 排序
    df = df.sort_values("created_at", ascending=False)

    # 績效統計
    st.markdown("#### 📊 績效統計")

    total_trades = len(df)
    winning_trades = len(df[df["pnl_amount"] > 0])
    losing_trades = len(df[df["pnl_amount"] < 0])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    total_pnl = df["pnl_amount"].sum()
    total_fees = df.get("fee", pd.Series([0] * len(df))).sum()
    net_pnl = total_pnl - total_fees

    avg_win = df[df["pnl_amount"] > 0]["pnl_amount"].mean() if winning_trades > 0 else 0
    avg_loss = abs(df[df["pnl_amount"] < 0]["pnl_amount"].mean()) if losing_trades > 0 else 0

    if avg_loss > 0:
        profit_factor = avg_win / avg_loss
    else:
        profit_factor = 0

    stat_col1, stat_col2, stat_col3, stat_col4, stat_col5, stat_col6 = st.columns(6)

    with stat_col1:
        stat_col1.metric("總交易數", f"{total_trades}")

    with stat_col2:
        delta_color = "normal" if total_pnl >= 0 else "inverse"
        stat_col2.metric("總損益", f"${total_pnl:+,.2f}", delta=f"${net_pnl:+,.2f} 淨額", delta_color=delta_color)

    with stat_col3:
        stat_col3.metric("勝率", f"{win_rate:.1f}%")

    with stat_col4:
        stat_col4.metric("平均獲利", f"${avg_win:+,.2f}")

    with stat_col5:
        stat_col5.metric("平均虧損", f"${-avg_loss:,.2f}")

    with stat_col6:
        if profit_factor >= 2:
            stat_col6.success(f"✅ {profit_factor:.2f}")
        elif profit_factor >= 1:
            stat_col6.warning(f"⚠️ {profit_factor:.2f}")
        else:
            stat_col6.error(f"❌ {profit_factor:.2f}")
        stat_col6.markdown("**盈虧比**")

    st.divider()

    # 圖表分析
    st.markdown("#### 📈 圖表分析")

    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["損益趨勢", "收益分佈", "分類統計"])

    with chart_tab1:
        render_pnl_trend_chart(df)

    with chart_tab2:
        render_pnl_distribution_chart(df)

    with chart_tab3:
        render_category_stats(df)

    st.divider()

    # 交易記錄表格
    st.markdown("#### 📋 交易明細")

    # 格式化數據
    display_df = df.copy()
    display_df["時間"] = pd.to_datetime(display_df["created_at"], unit="s").dt.strftime("%Y-%m-%d %H:%M")
    display_df["損益"] = display_df["pnl_amount"].apply(lambda x: f"${x:+,.2f}")
    display_df["損益%"] = display_df["pnl_pct"].apply(lambda x: f"{x:+.2f}%")
    display_df["手續費"] = display_df.get("fee", pd.Series([0] * len(display_df))).apply(lambda x: f"${x:,.2f}")

    # 選擇顯示欄位
    display_cols = ["時間", "watch_symbol", "action", "side", "price", "損益", "損益%", "手續費", "reason"]

    # 顏色映射
    def color_pnl(val):
        if isinstance(val, str):
            if val.startswith("$+"):
                return "color: #00cc96"
            elif val.startswith("$-"):
                return "color: #ef553b"
        return ""

    # 顯示表格
    display_df = display_df[display_cols].rename(
        columns={
            "watch_symbol": "交易對",
            "action": "動作",
            "side": "方向",
            "price": "價格",
            "reason": "原因",
        }
    )

    # 方向映射
    display_df["方向"] = display_df["方向"].apply(lambda x: "🟢 多頭" if x == 1 else "🔴 空頭")

    st.dataframe(
        display_df.style.applymap(color_pnl, subset=["損益"]),
        use_container_width=True,
        hide_index=True,
    )

    # 匯出按鈕
    st.divider()

    export_col1, export_col2 = st.columns([3, 1])

    with export_col1:
        st.markdown(f"**顯示 {len(display_df)} 筆交易記錄**")

    with export_col2:
        csv = display_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 匯出 CSV",
            data=csv,
            file_name=f"trade_log_{user_id}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_pnl_trend_chart(df: pd.DataFrame):
    """渲染損益趨勢圖表"""

    # 計算累積損益
    df_sorted = df.sort_values("created_at", ascending=True)
    df_sorted["cumulative_pnl"] = df_sorted["pnl_amount"].cumsum()

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
    )

    # 累積損益線
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(df_sorted["created_at"], unit="s"),
            y=df_sorted["cumulative_pnl"],
            mode="lines",
            name="累積損益",
            line=dict(color="#00cc96", width=2),
            fill="tozeroy",
        ),
        row=1,
        col=1,
    )

    # 單筆損益柱狀
    colors = ["#00cc96" if pnl > 0 else "#ef553b" for pnl in df_sorted["pnl_amount"]]

    fig.add_trace(
        go.Bar(
            x=pd.to_datetime(df_sorted["created_at"], unit="s"),
            y=df_sorted["pnl_amount"],
            marker_color=colors,
            name="單筆損益",
            opacity=0.7,
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title="損益趨勢圖",
        xaxis_title="時間",
        yaxis_title="損益 (USDT)",
        height=500,
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_pnl_distribution_chart(df: pd.DataFrame):
    """渲染損益分佈圖表"""

    import plotly.express as px

    # 分佈直方圖
    fig = px.histogram(
        df,
        x="pnl_amount",
        nbins=30,
        title="損益分佈",
        labels={"pnl_amount": "損益 (USDT)"},
        color_discrete_sequence=["#00cc96"],
    )

    fig.update_layout(
        xaxis_title="損益 (USDT)",
        yaxis_title="交易次數",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    # 統計數據
    st.markdown("**📊 分佈統計**")

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

    stat_col1.metric("最大獲利", f"${df['pnl_amount'].max():+.2f}")
    stat_col2.metric("最大虧損", f"${df['pnl_amount'].min():+.2f}")
    stat_col3.metric("平均獲利", f"${df[df['pnl_amount'] > 0]['pnl_amount'].mean():+.2f}")
    stat_col4.metric("平均虧損", f"${df[df['pnl_amount'] < 0]['pnl_amount'].mean():+.2f}")


def render_category_stats(df: pd.DataFrame):
    """渲染分類統計"""

    st.markdown("**按交易對統計**")

    symbol_stats = (
        df.groupby("watch_symbol")
        .agg(
            {
                "pnl_amount": ["sum", "mean", "count"],
                "pnl_pct": "mean",
            }
        )
        .round(2)
    )

    symbol_stats.columns = ["總損益", "平均損益", "交易次數", "平均損益%"]
    symbol_stats = symbol_stats.sort_values("總損益", ascending=False)

    st.dataframe(symbol_stats, use_container_width=True)

    st.divider()

    st.markdown("**按策略統計**")

    strategy_stats = (
        df.groupby("watch_strategy")
        .agg(
            {
                "pnl_amount": ["sum", "mean", "count"],
                "pnl_pct": "mean",
            }
        )
        .round(2)
    )

    strategy_stats.columns = ["總損益", "平均損益", "交易次數", "平均損益%"]
    strategy_stats = strategy_stats.sort_values("總損益", ascending=False)

    st.dataframe(strategy_stats, use_container_width=True)

    st.divider()

    st.markdown("**按方向統計**")

    direction_stats = (
        df.groupby("side")
        .agg(
            {
                "pnl_amount": ["sum", "mean", "count"],
                "pnl_pct": "mean",
            }
        )
        .round(2)
    )

    direction_stats.columns = ["總損益", "平均損益", "交易次數", "平均損益%"]

    # 動態設置 index 名稱，避免長度不匹配
    index_names = {1: "多頭", -1: "空頭"}
    new_index = [index_names.get(idx, str(idx)) for idx in direction_stats.index]
    direction_stats.index = new_index

    st.dataframe(direction_stats, use_container_width=True)


def render_single_trade_detail(trade: dict):
    """
    渲染單一交易詳情

    Args:
        trade: 交易記錄字典
    """
    pnl = trade.get("pnl_amount", 0)
    pnl_pct = trade.get("pnl_pct", 0)

    pnl_color = "🟢" if pnl >= 0 else "🔴"

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border-left: 4px solid {"#00cc96" if pnl >= 0 else "#ef553b"};
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0;">
                        {pnl_color} {trade.get("symbol", "N/A")} - {trade.get("action", "N/A")}
                    </h4>
                    <span style="color: #64748b; font-size: 0.85rem;">
                        {"🟢 多頭" if trade.get("side", 0) == 1 else "🔴 空頭"} |
                        價格：${trade.get("price", 0):,.2f}
                    </span>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.3rem; font-weight: bold; color: {"#00cc96" if pnl >= 0 else "#ef553b"};">
                        {pnl_color} ${pnl:+,.2f}
                    </div>
                    <div style="color: #64748b; font-size: 0.85rem;">
                        {pnl_pct:+.2f}%
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
