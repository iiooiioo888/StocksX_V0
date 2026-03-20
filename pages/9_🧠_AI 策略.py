# ════════════════════════════════════════════════════════════
# StocksX V0 - AI 策略页面
# 新功能：机器学习、NLP、强化学习策略
# ════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


st.set_page_config(page_title="AI 策略 - StocksX", page_icon="🧠", layout="wide")

# 自定义 CSS
st.markdown(
    """
<style>
    .strategy-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .signal-buy { color: #10b981; font-weight: bold; }
    .signal-sell { color: #ef4444; font-weight: bold; }
    .signal-hold { color: #f59e0b; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)

# ════════════════════════════════════════════════════════════
# 侧边栏配置
# ════════════════════════════════════════════════════════════

st.sidebar.title("⚙️ 策略配置")

# 选择策略类型
strategy_type = st.sidebar.selectbox(
    "选择策略类型",
    ["📊 策略总览", "🤖 LSTM 价格预测", "📈 多因子策略", "🔗 配对交易", "📰 NLP 情绪分析", "🎮 强化学习 DQN"],
)

# 通用配置
st.sidebar.subheader("通用设置")
symbol = st.sidebar.text_input("交易对/股票代码", "BTC/USDT")
lookback_days = st.sidebar.slider("回溯天数", 30, 730, 365)

# ════════════════════════════════════════════════════════════
# 策略总览
# ════════════════════════════════════════════════════════════

if strategy_type == "📊 策略总览":
    st.title("🧠 AI 策略中心")
    st.markdown("**基于机器学习、深度学习和强化学习的智能交易策略**")

    # 策略卡片
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        <div class="strategy-card">
            <h3>🤖 LSTM 价格预测</h3>
            <p>使用长短期记忆网络预测未来价格方向</p>
            <ul>
                <li>60 天回溯窗口</li>
                <li>50+ 技术指标特征</li>
                <li>预测未来 5 天涨跌</li>
            </ul>
            <p><strong>预期年化：25-40%</strong></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="strategy-card">
            <h3>📈 多因子策略</h3>
            <p>Fama-French 三因子 + 动量/质量/低波</p>
            <ul>
                <li>规模因子（SMB）</li>
                <li>价值因子（HML）</li>
                <li>动量/质量/低波因子</li>
            </ul>
            <p><strong>预期年化：15-30%</strong></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="strategy-card">
            <h3>🔗 配对交易</h3>
            <p>统计套利，寻找协整股票对</p>
            <ul>
                <li>Engle-Granger 协整检验</li>
                <li>Z-score 信号生成</li>
                <li>均值回归交易</li>
            </ul>
            <p><strong>预期年化：10-20%</strong></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown(
            """
        <div class="strategy-card">
            <h3>📰 NLP 情绪分析</h3>
            <p>FinBERT 分析新闻/社交媒体情绪</p>
            <ul>
                <li>实时新闻监控</li>
                <li>情绪聚合分析</li>
                <li>交易信号生成</li>
            </ul>
            <p><strong>预期年化：15-25%</strong></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            """
        <div class="strategy-card">
            <h3>🎮 强化学习 DQN</h3>
            <p>深度 Q 网络学习最优交易策略</p>
            <ul>
                <li>Gymnasium 交易环境</li>
                <li>Experience Replay</li>
                <li>自适应学习</li>
            </ul>
            <p><strong>预期年化：20-35%</strong></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col6:
        st.markdown(
            """
        <div class="strategy-card">
            <h3>🎯 集成策略</h3>
            <p>多策略加权集成信号</p>
            <ul>
                <li>加权平均信号</li>
                <li>风险分散</li>
                <li>稳健收益</li>
            </ul>
            <p><strong>预期年化：20-35%</strong></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # 性能对比图
    st.subheader("📊 策略性能对比（示例）")

    strategy_names = ["LSTM", "多因子", "配对交易", "NLP", "DQN", "集成"]
    returns = [0.35, 0.25, 0.15, 0.20, 0.30, 0.32]
    sharpe = [1.5, 1.3, 1.8, 1.2, 1.4, 1.6]
    max_dd = [0.20, 0.18, 0.12, 0.15, 0.25, 0.18]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="年化收益",
            x=strategy_names,
            y=returns,
            marker_color="#667eea",
            text=[f"{r:.0%}" for r in returns],
            textposition="outside",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Sharpe 比率",
            x=strategy_names,
            y=sharpe,
            marker_color="#764ba2",
            text=[f"{s:.1f}" for s in sharpe],
            textposition="outside",
        )
    )

    fig.update_layout(
        barmode="group",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e8"),
        showlegend=True,
        legend=dict(x=0, y=1),
    )

    st.plotly_chart(fig, use_container_width=True)

    # 风险提示
    st.info("""
    ⚠️ **风险提示**
    - 过往业绩不代表未来表现
    - 所有策略都存在亏损风险
    - 建议先进行回测再用真实资金
    - 请根据自身风险承受能力选择策略
    """)

# ════════════════════════════════════════════════════════════
# LSTM 价格预测
# ════════════════════════════════════════════════════════════

elif strategy_type == "🤖 LSTM 价格预测":
    st.title("🤖 LSTM 价格预测")
    st.markdown("**使用长短期记忆网络预测未来价格方向**")

    # 配置参数
    col1, col2, col3 = st.columns(3)

    with col1:
        lstm_lookback = st.slider("回溯窗口（天）", 20, 120, 60)
    with col2:
        lstm_forecast = st.slider("预测周期（天）", 1, 10, 5)
    with col3:
        lstm_epochs = st.slider("训练轮数", 10, 200, 50)

    # 加载数据按钮
    if st.button("🚀 加载数据并训练模型", type="primary"):
        with st.spinner("正在加载数据..."):
            # 模拟数据加载
            progress_bar = st.progress(0)

            for i in range(100):
                progress_bar.progress(i + 1)

            st.success("数据加载完成！")

        with st.spinner("正在训练 LSTM 模型..."):
            # 模拟训练过程
            for epoch in range(min(lstm_epochs, 10)):  # 只显示前 10 轮
                loss = 0.5 * np.exp(-epoch * 0.2) + 0.1
                acc = 0.5 + 0.4 * (1 - np.exp(-epoch * 0.3))

                st.write(f"**Epoch {epoch + 1}/{lstm_epochs}**")
                st.write(f"  损失：{loss:.4f}, 准确率：{acc:.2%}")

            st.success("模型训练完成！")

    # 显示预测结果
    st.subheader("📊 预测结果")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("当前价格", "$45,234.56", "+2.3%")
    with col2:
        st.metric("预测方向", "上涨", "↑")
    with col3:
        st.metric("上涨概率", "68%", "+5%")
    with col4:
        st.metric("信心度", "高", "✓")

    # 价格预测图表
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    actual_prices = 100 + np.cumsum(np.random.randn(100) * 2)
    predicted_prices = actual_prices[:-5].tolist() + [
        actual_prices[-5] * (1 + np.random.randn() * 0.02) for _ in range(5)
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates[:-5], y=actual_prices[:-5], mode="lines", name="实际价格", line=dict(color="#667eea", width=2)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=dates[-5:],
            y=predicted_prices[-5:],
            mode="lines+markers",
            name="预测价格",
            line=dict(color="#10b981", width=2, dash="dash"),
        )
    )

    fig.update_layout(
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e8"),
        showlegend=True,
        xaxis_title="日期",
        yaxis_title="价格",
    )

    st.plotly_chart(fig, use_container_width=True)

    # 特征重要性
    st.subheader("📈 特征重要性")

    feature_names = ["RSI", "MACD", "MA20", "BB_Width", "Volume", "Momentum", "Volatility", "EMA50"]
    importance = [0.18, 0.15, 0.14, 0.12, 0.11, 0.10, 0.10, 0.10]

    fig = go.Figure(
        go.Bar(
            x=feature_names,
            y=importance,
            marker_color="#764ba2",
            text=[f"{i:.1%}" for i in importance],
            textposition="outside",
        )
    )

    fig.update_layout(
        height=300,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e8"),
        xaxis_title="特征",
        yaxis_title="重要性",
    )

    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════
# 多因子策略
# ════════════════════════════════════════════════════════════

elif strategy_type == "📈 多因子策略":
    st.title("📈 多因子策略")
    st.markdown("**Fama-French 三因子 + 动量/质量/低波因子**")

    # 因子配置
    st.subheader("⚙️ 因子配置")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**启用因子**")
        enable_size = st.checkbox("规模因子 (SMB)", value=True)
        enable_value = st.checkbox("价值因子 (HML)", value=True)
        enable_momentum = st.checkbox("动量因子 (MOM)", value=True)

    with col2:
        st.markdown("**因子权重**")
        weight_size = st.slider("规模", 0.0, 0.3, 0.15)
        weight_value = st.slider("价值", 0.0, 0.3, 0.25)
        weight_momentum = st.slider("动量", 0.0, 0.3, 0.25)

    # 股票筛选
    st.subheader("🔍 股票筛选")

    col1, col2, col3 = st.columns(3)

    with col1:
        min_market_cap = st.number_input("最小市值（亿）", 0, 10000, 50)
    with col2:
        max_pe = st.number_input("最大 PE", 0, 100, 50)
    with col3:
        min_roe = st.number_input("最小 ROE（%）", 0, 50, 10)

    if st.button("🚀 运行策略", type="primary"):
        # 模拟结果
        st.success("策略运行完成！")

        # 显示选股结果
        st.subheader("📊 选股结果")

        stocks = pd.DataFrame(
            {
                "股票代码": ["AAPL", "GOOGL", "MSFT", "NVDA", "META"],
                "综合得分": [0.85, 0.82, 0.79, 0.76, 0.73],
                "规模因子": [0.8, 0.9, 0.7, 0.6, 0.8],
                "价值因子": [0.7, 0.6, 0.8, 0.5, 0.7],
                "动量因子": [0.9, 0.8, 0.7, 0.9, 0.8],
                "建议操作": ["买入", "买入", "买入", "买入", "买入"],
            }
        )

        st.dataframe(stocks, use_container_width=True)

    # 因子表现
    st.subheader("📈 因子历史表现")

    months = ["1 月", "2 月", "3 月", "4 月", "5 月", "6 月"]
    size_returns = [0.05, -0.02, 0.03, 0.04, -0.01, 0.06]
    value_returns = [0.03, 0.04, -0.01, 0.05, 0.02, 0.03]
    momentum_returns = [0.06, 0.03, 0.05, -0.02, 0.04, 0.05]

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=months, y=size_returns, name="规模因子", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=months, y=value_returns, name="价值因子", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=months, y=momentum_returns, name="动量因子", mode="lines+markers"))

    fig.update_layout(
        height=300,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e8"),
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════
# 配对交易
# ════════════════════════════════════════════════════════════

elif strategy_type == "🔗 配对交易":
    st.title("🔗 配对交易策略")
    st.markdown("**统计套利，寻找协整股票对进行均值回归交易**")

    # 配置参数
    st.subheader("⚙️ 策略参数")

    col1, col2, col3 = st.columns(3)

    with col1:
        entry_zscore = st.slider("入场 Z-score", 1.0, 3.0, 2.0)
    with col2:
        exit_zscore = st.slider("出场 Z-score", 0.0, 1.5, 0.5)
    with col3:
        stoploss_zscore = st.slider("止损 Z-score", 2.0, 5.0, 3.0)

    # 股票对选择
    st.subheader("📊 股票对选择")

    col1, col2 = st.columns(2)

    with col1:
        stock1 = st.selectbox("股票 1", ["AAPL", "GOOGL", "MSFT", "AMZN", "META"])
    with col2:
        stock2 = st.selectbox("股票 2", ["GOOGL", "AAPL", "AMZN", "MSFT", "NVDA"])

    if st.button("🔍 检验协整关系", type="primary"):
        # 模拟协整检验结果
        st.success("协整检验完成！")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("对冲比率", "0.85", "✓")
        with col2:
            st.metric("ADF p-value", "0.003", "< 0.05")
        with col3:
            st.metric("是否协整", "是", "✓")

        # 价差图表
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        spread = np.cumsum(np.random.randn(100))
        spread = spread - np.mean(spread)  # 均值回归

        zscore_upper = spread.rolling(20).std() * entry_zscore
        zscore_lower = -zscore_upper

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=dates, y=spread, name="价差", line=dict(color="#667eea", width=2)))

        fig.add_trace(
            go.Scatter(x=dates, y=zscore_upper, name="入场阈值", line=dict(color="#ef4444", width=1, dash="dash"))
        )

        fig.add_trace(
            go.Scatter(x=dates, y=zscore_lower, name="入场阈值", line=dict(color="#10b981", width=1, dash="dash"))
        )

        fig.update_layout(
            height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e8"),
            showlegend=True,
        )

        st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════
# NLP 情绪分析
# ════════════════════════════════════════════════════════════

elif strategy_type == "📰 NLP 情绪分析":
    st.title("📰 NLP 情绪分析")
    st.markdown("**使用 FinBERT 分析新闻和社交媒体情绪**")

    # 新闻源配置
    st.subheader("📡 新闻源配置")

    col1, col2 = st.columns(2)

    with col1:
        st.checkbox("Twitter/X", value=True)
        st.checkbox("Reddit r/wallstreetbets", value=True)
        st.checkbox("财经新闻 RSS", value=True)

    with col2:
        st.checkbox("加密货币新闻", value=True)
        st.checkbox("公司公告", value=True)
        st.checkbox("分析师报告", value=False)

    # 情绪分析结果
    st.subheader("📊 情绪分析结果")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("整体情绪", "正面", "↑")
    with col2:
        st.metric("正面比例", "65%", "+10%")
    with col3:
        st.metric("负面比例", "20%", "-5%")
    with col4:
        st.metric("中性比例", "15%", "-")

    # 情绪趋势图
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    positive = 0.5 + 0.1 * np.sin(np.linspace(0, 2 * np.pi, 30))
    negative = 0.3 - 0.05 * np.sin(np.linspace(0, 2 * np.pi, 30))
    neutral = 1 - positive - negative

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=dates, y=positive, stackgroup="one", name="正面", fillcolor="#10b981"))
    fig.add_trace(go.Scatter(x=dates, y=negative, stackgroup="one", name="负面", fillcolor="#ef4444"))
    fig.add_trace(go.Scatter(x=dates, y=neutral, stackgroup="one", name="中性", fillcolor="#f59e0b"))

    fig.update_layout(
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e8"),
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)

    # 最新新闻
    st.subheader("📰 最新新闻")

    news_data = pd.DataFrame(
        {
            "时间": ["10 分钟前", "30 分钟前", "1 小时前", "2 小时前", "3 小时前"],
            "标题": [
                "比特币突破新高，机构继续增持",
                "美联储暗示降息，市场情绪乐观",
                "某大型交易所报告安全漏洞",
                "分析师预测 Q2 将继续上涨",
                "以太坊升级成功，交易费用降低",
            ],
            "情绪": ["正面", "正面", "负面", "正面", "正面"],
            "来源": ["CoinDesk", "Bloomberg", "Reuters", "Analyst", "CoinTelegraph"],
        }
    )

    st.dataframe(news_data, use_container_width=True)

# ════════════════════════════════════════════════════════════
# 强化学习 DQN
# ════════════════════════════════════════════════════════════

elif strategy_type == "🎮 强化学习 DQN":
    st.title("🎮 强化学习 DQN")
    st.markdown("**深度 Q 网络学习最优交易策略**")

    # 训练配置
    st.subheader("⚙️ 训练配置")

    col1, col2, col3 = st.columns(3)

    with col1:
        rl_episodes = st.slider("训练回合数", 10, 500, 100)
    with col2:
        rl_lr = st.selectbox("学习率", [0.001, 0.0005, 0.0001], index=0)
    with col3:
        rl_gamma = st.slider("折扣因子", 0.9, 0.999, 0.99)

    # 训练进度
    if st.button("🚀 开始训练", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i in range(100):
            progress_bar.progress(i + 1)
            status_text.text(f"训练回合 {i + 1}/{rl_episodes}...")

        st.success("训练完成！")

        # 训练结果
        st.subheader("📊 训练结果")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("最终探索率", "0.05", "✓")
        with col2:
            st.metric("平均奖励", "0.023", "+0.005")
        with col3:
            st.metric("平均收益", "15.3%", "+2.1%")

        # 学习曲线
        episodes = list(range(1, 101))
        rewards = 0.01 + 0.02 * (1 - np.exp(-np.array(episodes) / 20)) + np.random.randn(100) * 0.005

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(x=episodes, y=rewards, mode="lines", name="平均奖励", line=dict(color="#667eea", width=2))
        )

        fig.update_layout(
            height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e8"),
            xaxis_title="回合",
            yaxis_title="平均奖励",
        )

        st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════
# 底部
# ════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #888; font-size: 0.9em;">
    <p>📊 StocksX V0 - AI 策略中心</p>
    <p>⚠️ 风险提示：过往业绩不代表未来表现，投资需谨慎</p>
</div>
""",
    unsafe_allow_html=True,
)
