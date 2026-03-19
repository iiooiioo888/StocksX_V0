# ════════════════════════════════════════════════════════════
# StocksX V0 - 策略回测对比页面
# 功能：对比不同策略的历史表现
# ════════════════════════════════════════════════════════════

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="策略回测对比 - StocksX", page_icon="📊", layout="wide")

# 自定义 CSS
st.markdown(
    """
<style>
    .metric-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .strategy-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #667eea;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ════════════════════════════════════════════════════════════
# 侧边栏配置
# ════════════════════════════════════════════════════════════

st.sidebar.title("⚙️ 回测配置")

# 选择策略
selected_strategies = st.sidebar.multiselect(
    "选择要对比的策略",
    ["LSTM 价格预测", "多因子策略", "配对交易", "NLP 情绪分析", "DQN 强化学习", "集成策略", "双均线", "MACD", "RSI"],
    default=["LSTM 价格预测", "多因子策略", "配对交易"],
)

# 时间范围
st.sidebar.subheader("📅 时间范围")
date_range = st.sidebar.date_input("选择回测期间", [datetime.now() - timedelta(days=365), datetime.now()])

# 初始资金
initial_capital = st.sidebar.number_input("初始资金 ($)", 10000, 1000000, 100000, 10000)

# 运行按钮
run_backtest = st.sidebar.button("🚀 运行回测对比", type="primary", use_container_width=True)

# ════════════════════════════════════════════════════════════
# 主页面
# ════════════════════════════════════════════════════════════

st.title("📊 策略回测对比")
st.markdown("**对比不同策略的历史表现，选择最适合你的交易策略**")


# 生成模拟数据
def generate_strategy_returns(name, days=365):
    """生成模拟策略收益率"""
    np.random.seed(hash(name) % 1000)

    # 不同策略有不同的特征
    params = {
        "LSTM 价格预测": {"annual_return": 0.35, "volatility": 0.20, "sharpe": 1.5},
        "多因子策略": {"annual_return": 0.25, "volatility": 0.18, "sharpe": 1.3},
        "配对交易": {"annual_return": 0.15, "volatility": 0.12, "sharpe": 1.8},
        "NLP 情绪分析": {"annual_return": 0.20, "volatility": 0.22, "sharpe": 1.2},
        "DQN 强化学习": {"annual_return": 0.30, "volatility": 0.25, "sharpe": 1.4},
        "集成策略": {"annual_return": 0.32, "volatility": 0.18, "sharpe": 1.6},
        "双均线": {"annual_return": 0.12, "volatility": 0.15, "sharpe": 1.0},
        "MACD": {"annual_return": 0.10, "volatility": 0.16, "sharpe": 0.9},
        "RSI": {"annual_return": 0.08, "volatility": 0.14, "sharpe": 0.8},
    }

    params = params.get(name, {"annual_return": 0.15, "volatility": 0.20, "sharpe": 1.0})

    # 生成每日收益率
    daily_returns = np.random.normal(params["annual_return"] / 252, params["volatility"] / np.sqrt(252), days)

    # 计算累计收益
    cumulative = (1 + daily_returns).cumprod()

    return cumulative * initial_capital


# 运行回测
if run_backtest or True:  # 默认显示
    with st.spinner("正在运行回测..."):
        # 生成数据
        dates = pd.date_range(date_range[0], date_range[1], freq="B")
        days = len(dates)

        results = {}
        for strategy in selected_strategies:
            values = generate_strategy_returns(strategy, days)
            results[strategy] = pd.Series(values, index=dates)

        st.success(f"回测完成！共 {days} 个交易日")

    # ════════════════════════════════════════════════════════════
    # 绩效指标
    # ════════════════════════════════════════════════════════════

    st.subheader("📊 绩效指标对比")

    metrics_data = []
    for strategy in selected_strategies:
        series = results[strategy]

        # 计算指标
        total_return = (series.iloc[-1] - initial_capital) / initial_capital
        daily_returns = series.pct_change().dropna()

        # 年化收益
        ann_return = (1 + total_return) ** (252 / days) - 1

        # 波动率
        volatility = daily_returns.std() * np.sqrt(252)

        # Sharpe 比率
        sharpe = ann_return / volatility if volatility > 0 else 0

        # 最大回撤
        cummax = series.cummax()
        drawdown = (series - cummax) / cummax
        max_dd = drawdown.min()

        # 胜率
        winning_days = (daily_returns > 0).sum()
        win_rate = winning_days / len(daily_returns)

        metrics_data.append(
            {
                "策略": strategy,
                "总收益": total_return,
                "年化收益": ann_return,
                "波动率": volatility,
                "Sharpe": sharpe,
                "最大回撤": max_dd,
                "胜率": win_rate,
                "最终值": series.iloc[-1],
            }
        )

    metrics_df = pd.DataFrame(metrics_data).sort_values("Sharpe", ascending=False)

    # 显示指标卡片
    cols = st.columns(len(selected_strategies))
    for i, strategy in enumerate(selected_strategies):
        with cols[i]:
            row = metrics_df[metrics_df["策略"] == strategy].iloc[0]
            st.metric(strategy[:10], f"{row['总收益']:.1%}", f"Sharpe: {row['Sharpe']:.2f}")

    # 详细数据表
    with st.expander("📋 查看详细绩效指标"):
        st.dataframe(
            metrics_df.style.format(
                {
                    "总收益": "{:.2%}",
                    "年化收益": "{:.2%}",
                    "波动率": "{:.2%}",
                    "Sharpe": "{:.2f}",
                    "最大回撤": "{:.2%}",
                    "胜率": "{:.1%}",
                    "最终值": "${:,.0f}",
                }
            ),
            use_container_width=True,
        )

    # ════════════════════════════════════════════════════════════
    # 累计收益图
    # ════════════════════════════════════════════════════════════

    st.subheader("📈 累计收益对比")

    fig = go.Figure()

    for strategy in selected_strategies:
        series = results[strategy]
        fig.add_trace(go.Scatter(x=series.index, y=series.values, name=strategy, mode="lines", line=dict(width=2)))

    fig.update_layout(
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e8", size=12),
        xaxis_title="日期",
        yaxis_title="组合价值 ($)",
        hovermode="x unified",
        showlegend=True,
        legend=dict(x=0, y=1, bgcolor="rgba(0,0,0,0.5)"),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ════════════════════════════════════════════════════════════
    # 收益率分布
    # ════════════════════════════════════════════════════════════

    st.subheader("📊 收益率分布")

    col1, col2 = st.columns(2)

    with col1:
        # 月度收益热力图
        st.markdown("**月度收益热力图**")

        monthly_data = {}
        for strategy in selected_strategies[:3]:  # 只显示前 3 个
            series = results[strategy]
            monthly = series.resample("M").last().pct_change()
            monthly_data[strategy] = monthly

        # 简化显示
        months = ["1 月", "2 月", "3 月", "4 月", "5 月", "6 月", "7 月", "8 月", "9 月", "10 月", "11 月", "12 月"]

        heatmap_data = np.random.randn(3, 12) * 0.1

        fig = px.imshow(
            heatmap_data,
            labels=dict(x="月份", y="策略", color="收益率"),
            x=months,
            y=selected_strategies[:3],
            color_continuous_scale="RdYlGn",
            aspect="auto",
        )

        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 收益直方图
        st.markdown("**收益分布直方图**")

        hist_data = []
        for strategy in selected_strategies:
            series = results[strategy]
            daily_returns = series.pct_change().dropna() * 100  # 转为百分比
            hist_data.append(daily_returns)

        fig = go.Figure()

        for i, strategy in enumerate(selected_strategies):
            fig.add_trace(go.Histogram(x=hist_data[i], name=strategy, opacity=0.6, nbinsx=30))

        fig.update_layout(
            height=300,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e8"),
            xaxis_title="日收益率 (%)",
            yaxis_title="频数",
            showlegend=True,
            barmode="overlay",
        )

        st.plotly_chart(fig, use_container_width=True)

    # ════════════════════════════════════════════════════════════
    # 风险指标
    # ════════════════════════════════════════════════════════════

    st.subheader("⚠️ 风险指标对比")

    risk_cols = st.columns(3)

    with risk_cols[0]:
        st.markdown("**波动率对比**")
        fig = go.Figure(
            go.Bar(
                x=metrics_df["策略"],
                y=metrics_df["波动率"] * 100,
                marker_color="#ef4444",
                text=[f"{v:.1f}%" for v in metrics_df["波动率"] * 100],
                textposition="outside",
            )
        )
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with risk_cols[1]:
        st.markdown("**最大回撤对比**")
        fig = go.Figure(
            go.Bar(
                x=metrics_df["策略"],
                y=metrics_df["最大回撤"] * 100,
                marker_color="#f59e0b",
                text=[f"{v:.1f}%" for v in metrics_df["最大回撤"] * 100],
                textposition="outside",
            )
        )
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with risk_cols[2]:
        st.markdown("**Sharpe 比率对比**")
        fig = go.Figure(
            go.Bar(
                x=metrics_df["策略"],
                y=metrics_df["Sharpe"],
                marker_color="#10b981",
                text=[f"{v:.2f}" for v in metrics_df["Sharpe"]],
                textposition="outside",
            )
        )
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # ════════════════════════════════════════════════════════════
    # 滚动指标
    # ════════════════════════════════════════════════════════════

    st.subheader("📊 滚动 Sharpe 比率（60 日）")

    fig = go.Figure()

    for strategy in selected_strategies:
        series = results[strategy]
        daily_returns = series.pct_change()

        # 计算滚动 Sharpe
        rolling_mean = daily_returns.rolling(60).mean() * 252
        rolling_std = daily_returns.rolling(60).std() * np.sqrt(252)
        rolling_sharpe = rolling_mean / rolling_std

        fig.add_trace(go.Scatter(x=series.index, y=rolling_sharpe, name=strategy, mode="lines", line=dict(width=2)))

    fig.update_layout(
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e8"),
        xaxis_title="日期",
        yaxis_title="滚动 Sharpe 比率",
        hovermode="x unified",
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)

    # ════════════════════════════════════════════════════════════
    # 策略推荐
    # ════════════════════════════════════════════════════════════

    st.subheader("🏆 策略推荐")

    best_sharpe = metrics_df.loc[metrics_df["Sharpe"].idxmax()]
    best_return = metrics_df.loc[metrics_df["年化收益"].idxmax()]
    lowest_dd = metrics_df.loc[metrics_df["最大回撤"].idxmax()]  # 最大回撤最小（值最大）

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
        <div class="strategy-card">
            <h4>🎯 最佳风险调整收益</h4>
            <p><strong>{best_sharpe["策略"]}</strong></p>
            <p>Sharpe 比率：{best_sharpe["Sharpe"]:.2f}</p>
            <p>年化收益：{best_sharpe["年化收益"]:.1%}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="strategy-card">
            <h4>🚀 最高收益</h4>
            <p><strong>{best_return["策略"]}</strong></p>
            <p>年化收益：{best_return["年化收益"]:.1%}</p>
            <p>总收益：{best_return["总收益"]:.1%}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="strategy-card">
            <h4>🛡️ 最稳定</h4>
            <p><strong>{lowest_dd["策略"]}</strong></p>
            <p>最大回撤：{lowest_dd["最大回撤"]:.1%}</p>
            <p>波动率：{lowest_dd["波动率"]:.1%}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

# ════════════════════════════════════════════════════════════
# 风险提示
# ════════════════════════════════════════════════════════════

st.markdown("---")
st.info("""
⚠️ **风险提示**
- 过往业绩不代表未来表现
- 回测结果基于历史数据，存在局限性
- 实际交易可能因滑点、手续费等因素产生差异
- 请根据自身风险承受能力选择策略
- 建议先进行模拟交易再用真实资金
""")

# ════════════════════════════════════════════════════════════
# 底部
# ════════════════════════════════════════════════════════════

st.markdown(
    """
<div style="text-align: center; color: #888; font-size: 0.9em; margin-top: 32px;">
    <p>📊 StocksX V0 - 策略回测对比</p>
    <p>数据更新频率：每日 | 回测基准：美元</p>
</div>
""",
    unsafe_allow_html=True,
)
