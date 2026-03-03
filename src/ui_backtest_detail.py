# 回測詳細視圖模組
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List
from datetime import datetime, timezone


def render_backtest_detail(record: Dict[str, Any]):
    """
    渲染回測詳細視圖
    
    Args:
        record: 回測記錄字典
    """
    import streamlit as st
    
    metrics = record.get("metrics", {})
    params = record.get("params", {})
    
    # 基本資訊
    st.markdown("### 📊 回測詳細資訊")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("交易對", record.get("symbol", "N/A"))
    with col2:
        st.metric("策略", record.get("strategy", "N/A"))
    with col3:
        st.metric("時間框架", record.get("timeframe", "N/A"))
    with col4:
        st.metric("交易所", record.get("exchange", "N/A"))
    
    st.divider()
    
    # 詳細績效指標
    st.markdown("#### 📈 績效指標")
    
    perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
    
    with perf_col1:
        st.markdown("**報酬類指標**")
        st.metric("總報酬", f"{metrics.get('total_return_pct', 0):+.2f}%")
        st.metric("年化報酬", f"{metrics.get('annual_return_pct', 0):+.2f}%")
        st.metric("平均報酬", f"{metrics.get('avg_return_pct', 0):+.2f}%")
        st.metric("最佳單筆", f"{metrics.get('best_trade_pct', 0):+.2f}%")
    
    with perf_col2:
        st.markdown("**風險類指標**")
        st.metric("最大回撤", f"{metrics.get('max_drawdown_pct', 0):.2f}%")
        st.metric("波動率", f"{metrics.get('volatility_pct', 0):.2f}%")
        st.metric("VaR 95%", f"{metrics.get('var_95', 0):.2f}%")
        st.metric("CVaR 95%", f"{metrics.get('cvar_95', 0):.2f}%")
    
    with perf_col3:
        st.markdown("**風險調整指標**")
        st.metric("Sharpe", f"{metrics.get('sharpe', 0):.2f}")
        st.metric("Sortino", f"{metrics.get('sortino', 0):.2f}")
        st.metric("Calmar", f"{metrics.get('calmar', 0):.2f}")
        st.metric("Omega", f"{metrics.get('omega', 0):.2f}")
    
    with perf_col4:
        st.markdown("**交易統計**")
        st.metric("總交易次數", f"{metrics.get('total_trades', 0)}")
        st.metric("勝率", f"{metrics.get('win_rate', 0):.1f}%")
        st.metric("利潤因子", f"{metrics.get('profit_factor', 0):.2f}")
        st.metric("盈虧比", f"{metrics.get('profit_loss_ratio', 0):.2f}")
    
    st.divider()
    
    # 策略參數
    if params:
        st.markdown("#### ⚙️ 策略參數")
        param_cols = st.columns(3)
        for idx, (key, value) in enumerate(params.items()):
            with param_cols[idx % 3]:
                st.markdown(f"**{key}**: `{value}`")
    
    st.divider()
    
    # 交易明細
    trades = record.get("trades", [])
    if trades:
        st.markdown("#### 📋 交易明細")
        
        trade_data = []
        for trade in trades:
            trade_data.append({
                "時間": datetime.fromtimestamp(trade.get("timestamp", 0) / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "方向": "🟢 多頭" if trade.get("side", 0) == 1 else ("🔴 空頭" if trade.get("side", 0) == -1 else "⚪"),
                "操作": trade.get("action", ""),
                "價格": f"${trade.get('price', 0):,.2f}",
                "數量": f"{trade.get('quantity', 0):,.4f}",
                "P&L": f"${trade.get('pnl', 0):+.2f}" if trade.get("pnl") is not None else "-",
                "P&L%": f"{trade.get('pnl_pct', 0):+.2f}%" if trade.get("pnl_pct") is not None else "-",
                "手續費": f"${trade.get('fee', 0):.2f}",
                "備註": trade.get("note", "")
            })
        
        trade_df = pd.DataFrame(trade_data)
        
        # 自定義樣式
        def color_pnl(val):
            if isinstance(val, str):
                if val.startswith('$+'):
                    return 'color: #00cc96'
                elif val.startswith('$-'):
                    return 'color: #ef553b'
            return ''
        
        styled_df = trade_df.style.applymap(color_pnl, subset=['P&L', 'P&L%'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # 匯出按鈕
        csv = trade_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 匯出交易明細 (CSV)",
            data=csv,
            file_name=f"{record.get('symbol', 'backtest')}_trades_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.divider()
    
    # 權益曲線
    equity_curve = record.get("equity_curve", [])
    if equity_curve:
        st.markdown("#### 📊 權益曲線")
        
        timestamps = []
        equities = []
        for point in equity_curve:
            timestamps.append(datetime.fromtimestamp(point.get("timestamp", 0) / 1000, tz=timezone.utc))
            equities.append(point.get("equity", 0))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=equities,
            mode='lines',
            name='權益',
            line=dict(color='#6ea8fe', width=2),
            fill='tozeroy',
            fillcolor='rgba(110,168,254,0.2)'
        ))
        
        fig.update_layout(
            title="權益曲線",
            xaxis_title="時間",
            yaxis_title="權益 ($)",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,30,50,0.3)',
            font=dict(color='#e0e0e8'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # 每月報酬
    st.markdown("#### 📅 每月報酬")
    
    # 從權益曲線計算每月報酬
    if equity_curve:
        monthly_returns = calculate_monthly_returns(equity_curve)
        
        if monthly_returns:
            # 建立熱力圖數據
            monthly_data = pd.DataFrame(monthly_returns)
            
            fig = go.Figure(data=go.Heatmap(
                z=monthly_data.values,
                x=monthly_data.columns,
                y=monthly_data.index,
                colorscale='RdYlGn',
                zmid=0,
                text=monthly_data.values,
                texttemplate='%{text:.1f}%',
                textfont={"size": 10},
                hovertemplate='%{y} %{x}<br>報酬：%{z:.2f}%<extra></extra>'
            ))
            
            fig.update_layout(
                title="每月報酬熱力圖",
                xaxis_title="月份",
                yaxis_title="年份",
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(30,30,50,0.3)',
                font=dict(color='#e0e0e8')
            )
            
            st.plotly_chart(fig, use_container_width=True)


def calculate_monthly_returns(equity_curve: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    計算每月報酬
    
    Args:
        equity_curve: 權益曲線數據
    
    Returns:
        {year: {month: return_pct}}
    """
    from collections import defaultdict
    import numpy as np
    
    # 按年月分組
    monthly_equity = defaultdict(lambda: defaultdict(list))
    
    for point in equity_curve:
        timestamp = point.get("timestamp", 0)
        equity = point.get("equity", 0)
        
        dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        year = dt.year
        month = dt.month
        
        monthly_equity[year][month].append(equity)
    
    # 計算每月報酬
    monthly_returns = defaultdict(dict)
    
    for year in sorted(monthly_equity.keys()):
        for month in sorted(monthly_equity[year].keys()):
            equities = monthly_equity[year][month]
            if len(equities) > 1:
                start_equity = equities[0]
                end_equity = equities[-1]
                return_pct = (end_equity - start_equity) / start_equity * 100
                monthly_returns[year][month] = return_pct
    
    # 轉換為 DataFrame 格式
    if monthly_returns:
        df = pd.DataFrame(monthly_returns)
        df.index = df.index.map(lambda m: datetime(2000, m, 1).strftime('%b'))
        return df
    else:
        return {}


def render_backtest_comparison(records: List[Dict[str, Any]]):
    """
    渲染回測對比視圖
    
    Args:
        records: 回測記錄列表
    """
    import streamlit as st
    
    st.markdown("#### 📊 回測對比")
    
    if len(records) < 2:
        st.info("請選擇至少 2 筆記錄進行對比")
        return
    
    # 建立對比表格
    comparison_data = []
    
    for record in records:
        metrics = record.get("metrics", {})
        comparison_data.append({
            "交易對": record.get("symbol", ""),
            "策略": STRATEGY_LABELS.get(record.get("strategy", ""), record.get("strategy", "")),
            "時間框架": record.get("timeframe", ""),
            "總報酬 (%)": f"{metrics.get('total_return_pct', 0):+.2f}",
            "年化報酬 (%)": f"{metrics.get('annual_return_pct', 0):+.2f}",
            "Sharpe": f"{metrics.get('sharpe', 0):.2f}",
            "最大回撤 (%)": f"{metrics.get('max_drawdown_pct', 0):.2f}",
            "勝率 (%)": f"{metrics.get('win_rate', 0):.1f}",
            "利潤因子": f"{metrics.get('profit_factor', 0):.2f}",
            "總交易數": f"{metrics.get('total_trades', 0)}"
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True,
        height=200
    )
    
    # 權益曲線對比
    st.markdown("##### 權益曲線對比")
    
    fig = go.Figure()
    
    colors = ['#6ea8fe', '#ef553b', '#00cc96', '#ffa15a', '#ab63fa']
    
    for idx, record in enumerate(records):
        equity_curve = record.get("equity_curve", [])
        if equity_curve:
            timestamps = []
            equities = []
            for point in equity_curve:
                timestamps.append(datetime.fromtimestamp(point.get("timestamp", 0) / 1000, tz=timezone.utc))
                equities.append(point.get("equity", 0))
            
            color = colors[idx % len(colors)]
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=equities,
                mode='lines',
                name=f"{record.get('symbol', '')} - {STRATEGY_LABELS.get(record.get('strategy', ''), record.get('strategy', ''))}",
                line=dict(color=color, width=2)
            ))
    
    fig.update_layout(
        title="權益曲線對比",
        xaxis_title="時間",
        yaxis_title="權益 ($)",
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,30,50,0.3)',
        font=dict(color='#e0e0e8'),
        legend=dict(orientation="h", y=1.02)
    )
    
    st.plotly_chart(fig, use_container_width=True)
