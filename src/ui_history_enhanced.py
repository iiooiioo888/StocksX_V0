# 歷史記錄增強模組 - 分頁、篩選、排序、對比、匯出
from __future__ import annotations

import json
import io
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go

import streamlit as st
from src.auth import UserDB
from src.config import STRATEGY_LABELS, STRATEGY_COLORS


# ════════════════════════════════════════════════════════════
# 分頁功能
# ════════════════════════════════════════════════════════════

def paginate_data(data: List[Dict], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    分頁數據
    
    Args:
        data: 原始數據列表
        page: 頁碼（從 1 開始）
        page_size: 每頁數量
    
    Returns:
        {
            "items": 當前頁數據,
            "total": 總數,
            "page": 當前頁碼,
            "page_size": 每頁數量,
            "total_pages": 總頁數
        }
    """
    total = len(data)
    total_pages = (total + page_size - 1) // page_size
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    
    return {
        "items": data[start_idx:end_idx],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages if total_pages > 0 else 1
    }


def render_pagination(total_pages: int, current_page: int, key_prefix: str = ""):
    """
    渲染分頁控制
    
    Args:
        total_pages: 總頁數
        current_page: 當前頁碼
        key_prefix: 按鍵前綴
    """
    if total_pages <= 1:
        return
    
    # 分頁控制
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ 上一頁", disabled=(current_page <= 1), key=f"{key_prefix}_prev"):
            st.session_state[f"{key_prefix}_page"] = current_page - 1
            st.rerun()
    
    with col2:
        # 頁碼選擇
        page_options = list(range(1, total_pages + 1))
        
        # 如果頁數太多，只显示部分
        if total_pages > 10:
            if current_page <= 5:
                page_options = list(range(1, 6)) + [f"...{total_pages}"]
            elif current_page >= total_pages - 4:
                page_options = [1, f"...{total_pages-4}"] + list(range(total_pages-4, total_pages+1))
            else:
                page_options = [1, f"...{current_page-1}"] + [current_page] + [f"...{current_page+1}"] + [total_pages]
        
        # 簡化處理
        page_options = list(range(1, min(total_pages + 1, 21)))  # 最多顯示 20 頁
        
        selected_page = st.selectbox(
            "頁碼",
            page_options,
            index=min(current_page - 1, len(page_options) - 1),
            key=f"{key_prefix}_page_select"
        )
        
        if selected_page != current_page:
            st.session_state[f"{key_prefix}_page"] = selected_page
            st.rerun()
    
    with col3:
        if st.button("下一頁 ➡️", disabled=(current_page >= total_pages), key=f"{key_prefix}_next"):
            st.session_state[f"{key_prefix}_page"] = current_page + 1
            st.rerun()
    
    # 顯示頁碼資訊
    st.caption(f"第 {current_page} / {total_pages} 頁")


# ════════════════════════════════════════════════════════════
# 篩選功能
# ════════════════════════════════════════════════════════════

def filter_history(
    data: List[Dict],
    strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    exchange: Optional[str] = None,
    timeframe: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_return: Optional[float] = None,
    is_favorite: Optional[bool] = None
) -> List[Dict]:
    """
    篩選歷史記錄
    
    Args:
        data: 原始數據
        strategy: 策略篩選
        symbol: 交易對篩選
        exchange: 交易所篩選
        timeframe: 時間框架篩選
        date_from: 開始日期
        date_to: 結束日期
        min_return: 最小報酬率
        is_favorite: 是否為收藏
    
    Returns:
        篩選後的數據
    """
    filtered = data
    
    if strategy:
        filtered = [item for item in filtered if item.get("strategy") == strategy]
    
    if symbol:
        filtered = [item for item in filtered if symbol.lower() in item.get("symbol", "").lower()]
    
    if exchange:
        filtered = [item for item in filtered if item.get("exchange") == exchange]
    
    if timeframe:
        filtered = [item for item in filtered if item.get("timeframe") == timeframe]
    
    if date_from:
        from_ts = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
        filtered = [item for item in filtered if item.get("created_at", 0) >= from_ts]
    
    if date_to:
        to_ts = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc).timestamp()
        filtered = [item for item in filtered if item.get("created_at", 0) <= to_ts]
    
    if min_return is not None:
        filtered = [
            item for item in filtered 
            if item.get("metrics", {}).get("total_return_pct", 0) >= min_return
        ]
    
    if is_favorite is not None:
        filtered = [item for item in filtered if item.get("is_favorite") == is_favorite]
    
    return filtered


def render_filters(key_prefix: str = "filter") -> Dict[str, Any]:
    """
    渲染篩選器
    
    Returns:
        篩選條件字典
    """
    from src.config import STRATEGY_LABELS
    
    with st.expander("🔍 篩選條件", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 策略篩選
            strategy_options = ["全部"] + list(STRATEGY_LABELS.keys())
            strategy_labels = ["全部"] + [STRATEGY_LABELS.get(k, k) for k in STRATEGY_LABELS.keys()]
            strategy_select = st.selectbox(
                "策略",
                index=0,
                options=strategy_options,
                format_func=lambda x: STRATEGY_LABELS.get(x, x),
                key=f"{key_prefix}_strategy"
            )
            
            # 交易對篩選
            symbol_filter = st.text_input("交易對", placeholder="例如：BTC", key=f"{key_prefix}_symbol")
            
            # 交易所篩選
            exchange_options = ["全部", "binance", "okx", "bybit", "yfinance"]
            exchange_filter = st.selectbox("交易所", exchange_options, key=f"{key_prefix}_exchange")
        
        with col2:
            # 時間框架篩選
            timeframe_options = ["全部", "1m", "5m", "15m", "1h", "4h", "1d"]
            timeframe_filter = st.selectbox("時間框架", timeframe_options, key=f"{key_prefix}_timeframe")
            
            # 日期範圍
            date_from = st.date_input("開始日期", value=None, key=f"{key_prefix}_date_from")
            date_to = st.date_input("結束日期", value=None, key=f"{key_prefix}_date_to")
            
            # 最小報酬率
            min_return = st.number_input(
                "最小報酬率 %",
                min_value=-100.0,
                max_value=1000.0,
                value=None,
                step=1.0,
                key=f"{key_prefix}_min_return"
            )
        
        with col3:
            # 收藏篩選
            favorite_filter = st.radio(
                "收藏",
                ["全部", "僅收藏", "未收藏"],
                index=0,
                key=f"{key_prefix}_favorite"
            )
            
            # 清空按鈕
            if st.button("🗑️ 清空篩選", use_container_width=True, key=f"{key_prefix}_clear"):
                # 清空所有篩選條件
                for key in st.session_state:
                    if key.startswith(f"{key_prefix}_"):
                        st.session_state[key] = None
                st.rerun()
        
        # 構建篩選條件
        filters = {
            "strategy": strategy_select if strategy_select != "全部" else None,
            "symbol": symbol_filter if symbol_filter else None,
            "exchange": exchange_filter if exchange_filter != "全部" else None,
            "timeframe": timeframe_filter if timeframe_filter != "全部" else None,
            "date_from": date_from.strftime("%Y-%m-%d") if date_from else None,
            "date_to": date_to.strftime("%Y-%m-%d") if date_to else None,
            "min_return": min_return if min_return is not None else None,
            "is_favorite": True if favorite_filter == "僅收藏" else (False if favorite_filter == "未收藏" else None)
        }
        
        return filters


# ════════════════════════════════════════════════════════════
# 排序功能
# ════════════════════════════════════════════════════════════

def sort_history(
    data: List[Dict],
    sort_by: str = "created_at",
    ascending: bool = False
) -> List[Dict]:
    """
    排序歷史記錄
    
    Args:
        data: 原始數據
        sort_by: 排序欄位
        ascending: 是否遞增
    
    Returns:
        排序後的數據
    """
    def get_sort_key(item):
        if sort_by == "created_at":
            return item.get("created_at", 0)
        elif sort_by == "return":
            return item.get("metrics", {}).get("total_return_pct", 0)
        elif sort_by == "sharpe":
            return item.get("metrics", {}).get("sharpe", 0)
        elif sort_by == "win_rate":
            trades = item.get("trades", [])
            if not trades:
                return 0
            wins = sum(1 for t in trades if t.get("pnl_pct", 0) > 0)
            return wins / len(trades)
        else:
            return 0
    
    return sorted(data, key=get_sort_key, reverse=not ascending)


def render_sort_controls(current_sort: str, current_order: bool, key_prefix: str = "sort") -> tuple:
    """
    渲染排序控制
    
    Returns:
        (sort_by, ascending)
    """
    col1, col2 = st.columns([2, 1])
    
    with col1:
        sort_options = {
            "created_at": "📅 日期",
            "return": "💰 報酬率",
            "sharpe": "📊 Sharpe",
            "win_rate": "🎯 勝率"
        }
        
        sort_by = st.selectbox(
            "排序欄位",
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
            index=list(sort_options.keys()).index(current_sort) if current_sort in sort_options else 0,
            key=f"{key_prefix}_select"
        )
    
    with col2:
        order = st.radio(
            "順序",
            ["遞減", "遞增"],
            index=0 if not current_order else 1,
            horizontal=True,
            key=f"{key_prefix}_order"
        )
        ascending = (order == "遞增")
    
    if sort_by != current_sort or ascending != current_order:
        st.session_state[f"{key_prefix}_by"] = sort_by
        st.session_state[f"{key_prefix}_asc"] = ascending
    
    return sort_by, ascending


# ════════════════════════════════════════════════════════════
# 多筆對比功能
# ════════════════════════════════════════════════════════════

def render_comparison_selector(
    data: List[Dict],
    max_select: int = 5,
    key_prefix: str = "compare"
) -> List[Dict]:
    """
    渲染對比選擇器
    
    Args:
        data: 歷史記錄數據
        max_select: 最大選擇數量
        key_prefix: 按鍵前綴
    
    Returns:
        選擇的記錄列表
    """
    st.markdown("#### 📊 多筆對比")
    
    if not data:
        st.info("尚無可對比的記錄")
        return []
    
    # 建立選項（顯示策略、交易對、日期、報酬率）
    options = []
    for item in data[:50]:  # 限制最多 50 筆可選
        label = (
            f"{STRATEGY_LABELS.get(item.get('strategy', ''), item.get('strategy'))} | "
            f"{item.get('symbol', '')} | "
            f"{datetime.fromtimestamp(item.get('created_at', 0), tz=timezone.utc).strftime('%Y-%m-%d')} | "
            f"報酬：{item.get('metrics', {}).get('total_return_pct', 0):+.1f}%"
        )
        options.append((label, item))
    
    # 多選
    selected_labels = st.multiselect(
        "選擇要對比的記錄（最多 5 筆）",
        options=[opt[0] for opt in options],
        default=[],
        max_selections=max_select,
        key=f"{key_prefix}_select"
    )
    
    # 取得選擇的記錄
    selected_items = [opt[1] for opt in options if opt[0] in selected_labels]
    
    if len(selected_items) >= 2:
        if st.button("🔍 開始對比", type="primary", key=f"{key_prefix}_start"):
            st.session_state[f"{key_prefix}_items"] = selected_items
            return selected_items
    elif len(selected_items) == 1:
        st.warning("請至少選擇 2 筆記錄進行對比")
    
    return st.session_state.get(f"{key_prefix}_items", [])


def render_comparison_chart(selected_items: List[Dict]):
    """
    渲染對比圖表（權益曲線對比）
    
    Args:
        selected_items: 選擇的記錄列表
    """
    if len(selected_items) < 2:
        return
    
    st.markdown("#### 📈 權益曲線對比")
    
    fig = go.Figure()
    
    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']
    
    for idx, item in enumerate(selected_items):
        equity_curve = item.get("equity_curve", [])
        if not equity_curve:
            continue
        
        # 準備數據
        timestamps = [
            datetime.fromtimestamp(e.get("timestamp", 0) / 1000, tz=timezone.utc).strftime("%m/%d")
            for e in equity_curve
        ]
        equities = [e.get("equity", 0) for e in equity_curve]
        
        strategy_name = STRATEGY_LABELS.get(item.get("strategy", ""), item.get("strategy", "Unknown"))
        symbol = item.get("symbol", "")
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=equities,
            mode='lines',
            name=f"{strategy_name} ({symbol})",
            line=dict(color=colors[idx % len(colors)], width=2),
            hovertemplate=f"<b>{strategy_name}</b><br>日期：%{{x}}<br>權益：%{{y:$,.0f}}<extra></extra>"
        ))
    
    fig.update_layout(
        title="📊 權益曲線對比",
        xaxis_title="日期",
        yaxis_title="權益 ($)",
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,30,50,0.3)',
        font=dict(color='#e0e0e8')
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_comparison_table(selected_items: List[Dict]):
    """
    渲染對比表格（績效指標對比）
    
    Args:
        selected_items: 選擇的記錄列表
    """
    if len(selected_items) < 2:
        return
    
    st.markdown("#### 📋 績效指標對比")
    
    # 建立對比數據
    comparison_data = []
    
    for item in selected_items:
        metrics = item.get("metrics", {})
        
        comparison_data.append({
            "策略": STRATEGY_LABELS.get(item.get("strategy", ""), item.get("strategy")),
            "交易對": item.get("symbol", ""),
            "時間框架": item.get("timeframe", ""),
            "總報酬 (%)": f"{metrics.get('total_return_pct', 0):+.2f}",
            "年化報酬 (%)": f"{metrics.get('annual_return_pct', 0):+.2f}",
            "Sharpe": f"{metrics.get('sharpe', 0):.2f}",
            "最大回撤 (%)": f"{metrics.get('max_drawdown_pct', 0):.2f}",
            "勝率 (%)": f"{metrics.get('win_rate', 0):.1f}",
            "利潤因子": f"{metrics.get('profit_factor', 0):.2f}",
            "交易次數": str(metrics.get('total_trades', 0))
        })
    
    # 顯示表格
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════
# 匯出功能
# ════════════════════════════════════════════════════════════

def export_to_csv(data: List[Dict], filename: str = "backtest_history.csv") -> bytes:
    """
    匯出為 CSV
    
    Args:
        data: 數據列表
        filename: 檔案名稱
    
    Returns:
        CSV 檔案 bytes
    """
    # 轉換為 DataFrame
    rows = []
    for item in data:
        metrics = item.get("metrics", {})
        rows.append({
            "ID": item.get("id"),
            "日期": datetime.fromtimestamp(item.get("created_at", 0), tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "策略": STRATEGY_LABELS.get(item.get("strategy", ""), item.get("strategy")),
            "交易對": item.get("symbol", ""),
            "交易所": item.get("exchange", ""),
            "時間框架": item.get("timeframe", ""),
            "總報酬 (%)": metrics.get("total_return_pct", 0),
            "年化報酬 (%)": metrics.get("annual_return_pct", 0),
            "Sharpe": metrics.get("sharpe", 0),
            "最大回撤 (%)": metrics.get("max_drawdown_pct", 0),
            "勝率 (%)": metrics.get("win_rate", 0),
            "利潤因子": metrics.get("profit_factor", 0),
            "交易次數": metrics.get("total_trades", 0),
            "備註": item.get("notes", ""),
            "收藏": "是" if item.get("is_favorite") else "否"
        })
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode('utf-8-sig')


def export_to_excel(data: List[Dict], filename: str = "backtest_history.xlsx") -> io.BytesIO:
    """
    匯出為 Excel
    
    Args:
        data: 數據列表
        filename: 檔案名稱
    
    Returns:
        Excel 檔案 buffer
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 主要數據
        rows = []
        for item in data:
            metrics = item.get("metrics", {})
            rows.append({
                "ID": item.get("id"),
                "日期": datetime.fromtimestamp(item.get("created_at", 0), tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "策略": STRATEGY_LABELS.get(item.get("strategy", ""), item.get("strategy")),
                "交易對": item.get("symbol", ""),
                "交易所": item.get("exchange", ""),
                "時間框架": item.get("timeframe", ""),
                "總報酬 (%)": metrics.get("total_return_pct", 0),
                "年化報酬 (%)": metrics.get("annual_return_pct", 0),
                "Sharpe": metrics.get("sharpe", 0),
                "最大回撤 (%)": metrics.get("max_drawdown_pct", 0),
                "勝率 (%)": metrics.get("win_rate", 0),
                "利潤因子": metrics.get("profit_factor", 0),
                "交易次數": metrics.get("total_trades", 0),
                "備註": item.get("notes", ""),
                "收藏": "是" if item.get("is_favorite") else "否"
            })
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name='回測歷史', index=False)
        
        # 統計摘要
        if data:
            stats_df = pd.DataFrame({
                '指標': ['總筆數', '平均報酬', '最佳報酬', '最差報酬', '平均 Sharpe', '平均勝率'],
                '數值': [
                    len(data),
                    sum(item.get("metrics", {}).get("total_return_pct", 0) for item in data) / len(data),
                    max(item.get("metrics", {}).get("total_return_pct", 0) for item in data),
                    min(item.get("metrics", {}).get("total_return_pct", 0) for item in data),
                    sum(item.get("metrics", {}).get("sharpe", 0) for item in data) / len(data),
                    sum(item.get("metrics", {}).get("win_rate", 0) for item in data) / len(data)
                ]
            })
            stats_df.to_excel(writer, sheet_name='統計摘要', index=False)
    
    output.seek(0)
    return output


def render_export_buttons(data: List[Dict], key_prefix: str = "export"):
    """
    渲染匯出按鈕
    
    Args:
        data: 要匯出的數據
        key_prefix: 按鍵前綴
    """
    st.markdown("#### 💾 匯出數據")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data = export_to_csv(data)
        st.download_button(
            label="📥 下載 CSV",
            data=csv_data,
            file_name="backtest_history.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"{key_prefix}_csv"
        )
    
    with col2:
        try:
            excel_data = export_to_excel(data)
            st.download_button(
                label="📥 下載 Excel",
                data=excel_data,
                file_name="backtest_history.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"{key_prefix}_excel"
            )
        except Exception as e:
            st.error(f"Excel 匯出失敗：{str(e)}")
    
    with col3:
        # PDF 匯出（需要額外依賴）
        st.info("PDF 匯出需安裝額外依賴")
        # 實際實作可使用 reportlab 或 weasyprint


# ════════════════════════════════════════════════════════════
# 統計分析
# ════════════════════════════════════════════════════════════

def render_statistics(data: List[Dict]):
    """
    渲染統計分析
    
    Args:
        data: 歷史記錄數據
    """
    if not data:
        return
    
    st.markdown("#### 📊 統計分析")
    
    # 計算統計指標
    total_count = len(data)
    returns = [item.get("metrics", {}).get("total_return_pct", 0) for item in data]
    
    profitable_count = sum(1 for r in returns if r > 0)
    win_rate = profitable_count / total_count * 100 if total_count > 0 else 0
    
    avg_return = sum(returns) / len(returns) if returns else 0
    best_return = max(returns) if returns else 0
    worst_return = min(returns) if returns else 0
    
    sharpe_values = [item.get("metrics", {}).get("sharpe", 0) for item in data]
    avg_sharpe = sum(sharpe_values) / len(sharpe_values) if sharpe_values else 0
    
    # 顯示統計
    stat_cols = st.columns(6)
    
    stat_cols[0].metric(
        "📊 總回測數",
        str(total_count),
        delta=f"{profitable_count} 筆獲利"
    )
    
    stat_cols[1].metric(
        "🎯 勝率",
        f"{win_rate:.1f}%",
        delta=f"平均 {avg_return:+.1f}%"
    )
    
    stat_cols[2].metric(
        "💰 最佳報酬",
        f"{best_return:+.1f}%",
        delta="單筆最佳"
    )
    
    stat_cols[3].metric(
        "💸 最差報酬",
        f"{worst_return:+.1f}%",
        delta="單筆最差",
        delta_color="inverse"
    )
    
    stat_cols[4].metric(
        "📈 平均 Sharpe",
        f"{avg_sharpe:.2f}",
        delta="風險調整後"
    )
    
    stat_cols[5].metric(
        "⭐ 收藏數量",
        str(sum(1 for item in data if item.get("is_favorite"))),
        delta="我的收藏"
    )
    
    # 報酬分佈圖
    if total_count >= 5:
        st.markdown("##### 💹 報酬分佈")
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=returns,
            nbinsx=20,
            marker_color=['#00cc96' if r > 0 else '#ef553b' for r in returns],
            opacity=0.75
        ))
        
        fig.update_layout(
            title="報酬分佈圖",
            xaxis_title="報酬率 (%)",
            yaxis_title="次數",
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,30,50,0.3)',
            font=dict(color='#e0e0e8')
        )
        
        st.plotly_chart(fig, use_container_width=True)
