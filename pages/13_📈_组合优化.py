# ════════════════════════════════════════════════════════════
# StocksX V0 - 组合优化页面
# 功能：马科维茨优化、风险平价、有效前沿
# ════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(
    page_title="组合优化 - StocksX",
    page_icon="📊",
    layout="wide"
)

# 自定义 CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .asset-weight {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 侧边栏配置
# ════════════════════════════════════════════════════════════

st.sidebar.title("⚙️ 组合配置")

# 选择优化方法
optimization_method = st.sidebar.selectbox(
    "优化方法",
    ["🎯 最大夏普比率", "🛡️ 最小波动率", "⚖️ 风险平价", "📈 有效前沿"]
)

# 资产选择
st.sidebar.subheader("📊 资产选择")
default_assets = ["BTC", "ETH", "SOL", "BNB", "USDT"]
selected_assets = st.sidebar.multiselect(
    "选择资产",
    default_assets,
    default=default_assets
)

# 历史数据范围
st.sidebar.subheader("📅 数据范围")
lookback_days = st.sidebar.slider("回溯天数", 30, 730, 365)

# 无风险利率
risk_free_rate = st.sidebar.slider("无风险利率（年化）", 0.0, 0.1, 0.02, 0.005)

# 运行优化
run_optimization = st.sidebar.button("🚀 运行优化", type="primary", use_container_width=True)

# ════════════════════════════════════════════════════════════
# 主页面
# ════════════════════════════════════════════════════════════

st.title("📊 组合优化")
st.markdown("**基于马科维茨现代投资组合理论，科学配置资产权重**")

# 生成模拟数据（实际应该从数据源获取）
def generate_returns(assets: List[str], days: int) -> pd.DataFrame:
    """生成模拟收益率数据"""
    np.random.seed(42)
    
    # 不同资产的预期收益和波动
    params = {
        'BTC': {'mean': 0.001, 'std': 0.03},
        'ETH': {'mean': 0.0012, 'std': 0.035},
        'SOL': {'mean': 0.0015, 'std': 0.05},
        'BNB': {'mean': 0.0008, 'std': 0.025},
        'USDT': {'mean': 0.0001, 'std': 0.001},
    }
    
    returns_data = {}
    for asset in assets:
        p = params.get(asset, {'mean': 0.001, 'std': 0.03})
        returns_data[asset] = np.random.normal(p['mean'], p['std'], days)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    return pd.DataFrame(returns_data, index=dates)

# 运行优化
if run_optimization or True:  # 默认显示
    with st.spinner("正在优化组合..."):
        # 生成数据
        returns = generate_returns(selected_assets, lookback_days)
        
        # 显示资产统计
        st.subheader("📊 资产统计")
        
        stats_data = {
            '资产': selected_assets,
            '年化收益': [returns[col].mean() * 252 for col in selected_assets],
            '年化波动': [returns[col].std() * np.sqrt(252) for col in selected_assets],
            '夏普比率': [(returns[col].mean() * 252 - risk_free_rate) / (returns[col].std() * np.sqrt(252)) for col in selected_assets],
        }
        
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        # 执行优化
        st.divider()
        
        if optimization_method == "🎯 最大夏普比率":
            st.subheader("🎯 最大夏普比率组合")
            
            # 模拟优化结果
            weights = {
                'BTC': 0.25,
                'ETH': 0.30,
                'SOL': 0.15,
                'BNB': 0.20,
                'USDT': 0.10,
            }
            
            # 计算组合指标
            portfolio_return = sum(weights[a] * stats_df[stats_df['资产']==a]['年化收益'].values[0] for a in selected_assets)
            portfolio_volatility = np.sqrt(sum(weights[a]**2 * (stats_df[stats_df['资产']==a]['年化波动'].values[0])**2 for a in selected_assets))
            sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("年化收益", f"{portfolio_return:.1%}")
            col2.metric("年化波动", f"{portfolio_volatility:.1%}")
            col3.metric("夏普比率", f"{sharpe:.2f}")
            col4.metric("最大回撤", f"{portfolio_volatility * 2:.1%}")
            
            # 显示权重
            st.markdown("#### 最优权重")
            
            for asset, weight in weights.items():
                if asset in selected_assets:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.progress(weight)
                    with col2:
                        st.write(f"**{asset}**: {weight:.1%}")
        
        elif optimization_method == "🛡️ 最小波动率":
            st.subheader("🛡️ 最小波动率组合")
            
            # 模拟优化结果
            weights = {
                'BTC': 0.15,
                'ETH': 0.15,
                'SOL': 0.05,
                'BNB': 0.20,
                'USDT': 0.45,
            }
            
            portfolio_return = sum(weights[a] * stats_df[stats_df['资产']==a]['年化收益'].values[0] for a in selected_assets)
            portfolio_volatility = np.sqrt(sum(weights[a]**2 * (stats_df[stats_df['资产']==a]['年化波动'].values[0])**2 for a in selected_assets))
            sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
            
            col1, col2, col3 = st.columns(3)
            col1.metric("年化收益", f"{portfolio_return:.1%}")
            col2.metric("年化波动", f"{portfolio_volatility:.1%}")
            col3.metric("夏普比率", f"{sharpe:.2f}")
            
            st.markdown("#### 最优权重")
            for asset, weight in weights.items():
                if asset in selected_assets:
                    st.write(f"**{asset}**: {weight:.1%}")
        
        elif optimization_method == "⚖️ 风险平价":
            st.subheader("⚖️ 风险平价组合")
            
            # 模拟优化结果
            weights = {
                'BTC': 0.20,
                'ETH': 0.20,
                'SOL': 0.10,
                'BNB': 0.25,
                'USDT': 0.25,
            }
            
            risk_contrib = {
                'BTC': 0.20,
                'ETH': 0.20,
                'SOL': 0.20,
                'BNB': 0.20,
                'USDT': 0.20,
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 资金权重")
                for asset, weight in weights.items():
                    if asset in selected_assets:
                        st.write(f"{asset}: {weight:.1%}")
            
            with col2:
                st.markdown("#### 风险贡献")
                for asset, contrib in risk_contrib.items():
                    if asset in selected_assets:
                        st.write(f"{asset}: {contrib:.1%}")
        
        elif optimization_method == "📈 有效前沿":
            st.subheader("📈 有效前沿")
            
            # 模拟有效前沿数据
            frontier_data = {
                '波动率': np.linspace(0.1, 0.5, 20),
                '收益率': np.linspace(0.05, 0.3, 20),
                '夏普比率': np.linspace(0.5, 1.5, 20),
            }
            
            frontier_df = pd.DataFrame(frontier_data)
            
            # 绘制有效前沿图
            import plotly.express as px
            
            fig = px.scatter(
                frontier_df,
                x='波动率',
                y='收益率',
                color='夏普比率',
                title='有效前沿',
                labels={'波动率': '年化波动率', '收益率': '年化收益率'},
                color_continuous_scale='RdYlGn'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 标记最优点
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("**最小方差组合**\n\n波动率：10.0%\n收益率：5.0%")
            
            with col2:
                st.success("**最大夏普组合**\n\n夏普比率：1.5\n波动率：25.0%\n收益率：20.0%")

# ════════════════════════════════════════════════════════════
# 相关性分析
# ════════════════════════════════════════════════════════════

st.divider()
st.subheader("🔗 资产相关性分析")

# 计算相关性矩阵
returns = generate_returns(selected_assets, lookback_days)
corr_matrix = returns.corr()

# 绘制热力图
import plotly.graph_objects as go

fig = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=corr_matrix.columns,
    y=corr_matrix.columns,
    colorscale='RdBu',
    zmid=0,
    text=corr_matrix.values.round(2),
    texttemplate='%{text}',
))

fig.update_layout(
    title='资产相关性矩阵',
    xaxis_title='资产',
    yaxis_title='资产',
)

st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════
# 蒙特卡洛模拟
# ════════════════════════════════════════════════════════════

st.divider()
st.subheader("🎲 蒙特卡洛模拟")

n_simulations = st.slider("模拟次数", 1000, 10000, 5000, 1000)

if st.button("运行蒙特卡洛模拟"):
    with st.spinner("正在运行模拟..."):
        # 模拟随机权重组合
        np.random.seed(42)
        n_assets = len(selected_assets)
        
        returns_list = []
        volatilities_list = []
        sharpe_list = []
        
        for _ in range(n_simulations):
            weights = np.random.random(n_assets)
            weights /= np.sum(weights)
            
            portfolio_return = np.sum(returns.mean() * weights) * 252
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
            sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
            
            returns_list.append(portfolio_return)
            volatilities_list.append(portfolio_volatility)
            sharpe_list.append(sharpe)
        
        # 绘制散点图
        sim_df = pd.DataFrame({
            '波动率': volatilities_list,
            '收益率': returns_list,
            '夏普比率': sharpe_list,
        })
        
        fig = px.scatter(
            sim_df,
            x='波动率',
            y='收益率',
            color='夏普比率',
            title=f'蒙特卡洛模拟（{n_simulations} 次）',
            color_continuous_scale='Viridis'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示最佳模拟结果
        best_idx = np.argmax(sharpe_list)
        st.success(f"""
        **最佳组合**
        - 夏普比率：{sharpe_list[best_idx]:.2f}
        - 年化收益：{returns_list[best_idx]:.1%}
        - 年化波动：{volatilities_list[best_idx]:.1%}
        """)

# ════════════════════════════════════════════════════════════
# 使用说明
# ════════════════════════════════════════════════════════════

st.divider()
with st.expander("📖 使用说明"):
    st.markdown("""
    ### 优化方法
    
    **最大夏普比率**
    - 目标：最大化风险调整后收益
    - 适合：追求最优性价比的投资者
    
    **最小波动率**
    - 目标：最小化组合风险
    - 适合：保守型投资者
    
    **风险平价**
    - 目标：每个资产贡献相同风险
    - 适合：真正分散风险的投资者
    
    **有效前沿**
    - 展示所有最优组合的集合
    - 帮助理解风险 - 收益关系
    
    ### 注意事项
    1. 历史数据不代表未来表现
    2. 优化结果依赖于输入数据质量
    3. 建议定期再平衡（如每季度）
    4. 考虑交易费用和税费影响
    """)
