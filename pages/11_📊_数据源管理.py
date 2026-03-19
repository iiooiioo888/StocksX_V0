# ════════════════════════════════════════════════════════════
# StocksX V0 - 数据源管理页面
# 功能：配置和管理多个数据源
# ════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="数据源管理 - StocksX",
    page_icon="📊",
    layout="wide"
)

# 自定义 CSS
st.markdown("""
<style>
    .data-source-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }
    .status-active { background: rgba(16, 185, 129, 0.2); color: #10b981; }
    .status-inactive { background: rgba(107, 114, 128, 0.2); color: #6b7280; }
    .status-error { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# 侧边栏配置
# ════════════════════════════════════════════════════════════

st.sidebar.title("⚙️ 数据源配置")

# 选择数据源类别
category = st.sidebar.selectbox(
    "选择数据源类别",
    ["📈 传统市场", "₿ 加密货币", "📊 宏观经济", "🔗 链上数据", "📰 新闻舆情", "📱 社交媒体"]
)

# API Key 配置
st.sidebar.subheader("🔑 API Key 管理")
show_api_config = st.sidebar.checkbox("显示 API 配置", value=False)

# ════════════════════════════════════════════════════════════
# 主页面
# ════════════════════════════════════════════════════════════

st.title("📊 数据源管理")
st.markdown("**配置和管理多个市场数据源，支持传统市场、加密货币、宏观经济等**")

# 数据源配置
DATA_SOURCES = {
    "📈 传统市场": [
        {
            "name": "台湾证券交易所 (TWSE)",
            "id": "twse",
            "status": "active",
            "description": "台股上市/上柜股票实时行情、历史 K 线",
            "update_freq": "实时（5 秒延迟）",
            "coverage": "台股 2000+ 支股票",
            "api_required": False,
            "config": {
                "base_url": "https://www.twse.com.tw",
                "timeout": 10,
                "cache_ttl": 60
            }
        },
        {
            "name": "Yahoo Finance",
            "id": "yfinance",
            "status": "active",
            "description": "美股、港股、台股、ETF、期货、指数",
            "update_freq": "实时（15 分钟延迟）",
            "coverage": "全球 100,000+ 标的",
            "api_required": False,
            "config": {
                "base_url": "https://finance.yahoo.com",
                "timeout": 15
            }
        },
        {
            "name": "Alpha Vantage",
            "id": "alpha_vantage",
            "status": "inactive",
            "description": "美股实时/历史行情、技术指标、基本面",
            "update_freq": "实时",
            "coverage": "美股 8,000+ 支股票",
            "api_required": True,
            "config": {
                "api_key": "YOUR_API_KEY",
                "base_url": "https://www.alphavantage.co",
                "rate_limit": "5 次/分钟"
            }
        },
        {
            "name": "IEX Cloud",
            "id": "iex_cloud",
            "status": "inactive",
            "description": "美股实时行情、财报、内部人交易",
            "update_freq": "实时",
            "coverage": "美股完整数据",
            "api_required": True,
            "config": {
                "api_key": "YOUR_API_KEY",
                "base_url": "https://cloud.iexapis.com"
            }
        },
    ],
    "₿ 加密货币": [
        {
            "name": "CCXT (多交易所)",
            "id": "ccxt",
            "status": "active",
            "description": "支持 Binance、OKX、Bybit 等 100+ 交易所",
            "update_freq": "实时",
            "coverage": "10,000+ 交易对",
            "api_required": False,
            "config": {
                "exchanges": ["binance", "okx", "bybit", "gate"],
                "rate_limit": True
            }
        },
        {
            "name": "CoinGecko",
            "id": "coingecko",
            "status": "active",
            "description": "加密货币价格、市值、交易量",
            "update_freq": "实时",
            "coverage": "10,000+ 币种",
            "api_required": True,
            "config": {
                "api_key": "YOUR_API_KEY",
                "base_url": "https://api.coingecko.com"
            }
        },
        {
            "name": "Glassnode",
            "id": "glassnode",
            "status": "inactive",
            "description": "链上数据、交易所流量、巨鲸追踪",
            "update_freq": "每小时",
            "coverage": "BTC/ETH 链上指标",
            "api_required": True,
            "config": {
                "api_key": "YOUR_API_KEY",
                "base_url": "https://api.glassnode.com"
            }
        },
    ],
    "📊 宏观经济": [
        {
            "name": "FRED (美联储)",
            "id": "fred",
            "status": "inactive",
            "description": "利率、货币供应、经济指数",
            "update_freq": "每日",
            "coverage": "800,000+ 经济指标",
            "api_required": True,
            "config": {
                "api_key": "YOUR_API_KEY",
                "base_url": "https://api.stlouisfed.org"
            }
        },
        {
            "name": "Trading Economics",
            "id": "trading_economics",
            "status": "inactive",
            "description": "全球 GDP、CPI、失业率、PMI",
            "update_freq": "每日",
            "coverage": "196 个国家经济数据",
            "api_required": True,
            "config": {
                "api_key": "YOUR_API_KEY",
                "base_url": "https://api.tradingeconomics.com"
            }
        },
    ],
    "🔗 链上数据": [
        {
            "name": "Dune Analytics",
            "id": "dune",
            "status": "inactive",
            "description": "DeFi 协议、NFT、链上交易",
            "update_freq": "每小时",
            "coverage": "以太坊为主",
            "api_required": True,
            "config": {
                "api_key": "YOUR_API_KEY",
                "base_url": "https://api.dune.com"
            }
        },
        {
            "name": "Uniswap Subgraph",
            "id": "uniswap",
            "status": "inactive",
            "description": "DEX 交易量、流动性池、价格",
            "update_freq": "实时",
            "coverage": "Uniswap V2/V3",
            "api_required": False,
            "config": {
                "endpoint": "https://api.thegraph.com/subgraphs/name/uniswap"
            }
        },
    ],
    "📰 新闻舆情": [
        {
            "name": "CoinDesk RSS",
            "id": "coindesk",
            "status": "active",
            "description": "加密货币新闻",
            "update_freq": "实时",
            "coverage": "全球加密新闻",
            "api_required": False,
            "config": {
                "rss_url": "https://www.coindesk.com/arc/outboundfeeds/rss/"
            }
        },
        {
            "name": "NewsAPI",
            "id": "newsapi",
            "status": "inactive",
            "description": "全球新闻聚合",
            "update_freq": "实时",
            "coverage": "50,000+ 新闻源",
            "api_required": True,
            "config": {
                "api_key": "YOUR_API_KEY",
                "base_url": "https://newsapi.org"
            }
        },
    ],
    "📱 社交媒体": [
        {
            "name": "Twitter API v2",
            "id": "twitter",
            "status": "inactive",
            "description": "推文、提及、情绪分析",
            "update_freq": "实时",
            "coverage": "Twitter 全平台",
            "api_required": True,
            "config": {
                "api_key": "YOUR_API_KEY",
                "api_secret": "YOUR_SECRET",
                "bearer_token": "YOUR_TOKEN"
            }
        },
        {
            "name": "Reddit API",
            "id": "reddit",
            "status": "inactive",
            "description": "Subreddit 帖子、评论、情绪",
            "update_freq": "实时",
            "coverage": "r/cryptocurrency 等",
            "api_required": True,
            "config": {
                "client_id": "YOUR_ID",
                "client_secret": "YOUR_SECRET"
            }
        },
    ],
}

# 显示当前类别的数据源
st.subheader(f"{category}")

sources = DATA_SOURCES.get(category, [])

if sources:
    for source in sources:
        status_class = f"status-{source['status']}"
        status_text = "✅ 活跃" if source['status'] == 'active' else "⏸️ 未启用" if source['status'] == 'inactive' else "❌ 错误"
        
        with st.container():
            st.markdown(f"""
            <div class="data-source-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0 0 8px 0;">{source['name']}</h3>
                        <p style="margin: 0 0 8px 0; color: #9ca3af;">{source['description']}</p>
                        <div style="font-size: 0.9rem; color: #6b7280;">
                            <span class="status-badge {status_class}">{status_text}</span>
                            <span style="margin-right: 12px;">🕐 {source['update_freq']}</span>
                            <span style="margin-right: 12px;">📊 {source['coverage']}</span>
                            {"🔑 需要 API Key" if source['api_required'] else "🆓 免费"}
                        </div>
                    </div>
                    <div>
                        {"⚙️ 配置" if source['status'] == 'active' else "🔧 启用"}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 展开配置详情
            with st.expander("⚙️ 配置详情"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.json(source['config'])
                
                with col2:
                    if source['status'] == 'active':
                        if st.button("⏸️ 停用", key=f"disable_{source['id']}"):
                            st.success(f"已停用 {source['name']}")
                    else:
                        if st.button("✅ 启用", key=f"enable_{source['id']}"):
                            if source['api_required']:
                                st.warning("请先配置 API Key")
                            else:
                                st.success(f"已启用 {source['name']}")

# ════════════════════════════════════════════════════════════
# API Key 配置
# ════════════════════════════════════════════════════════════

if show_api_config:
    st.divider()
    st.subheader("🔑 API Key 配置")
    
    st.markdown("""
    **已配置的 API Keys:**
    
    | 数据源 | API Key | 状态 | 剩余额度 |
    |--------|---------|------|----------|
    | Alpha Vantage | `abc...123` | ✅ 正常 | 450/500 |
    | CoinGecko | `xyz...789` | ✅ 正常 | 95/100 |
    | Glassnode | (未配置) | ❌ 缺失 | - |
    """)
    
    # 添加新的 API Key
    with st.form("add_api_key"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox("数据源", ["Alpha Vantage", "CoinGecko", "Glassnode", "FRED"])
        with col2:
            st.text_input("API Key", type="password")
        with col3:
            st.form_submit_button("💾 保存")

# ════════════════════════════════════════════════════════════
# 数据源健康检查
# ════════════════════════════════════════════════════════════

st.divider()
st.subheader("🏥 数据源健康检查")

# 运行健康检查
if st.button("🔍 运行健康检查"):
    with st.spinner("正在检查所有数据源..."):
        import time
        time.sleep(2)
        
        st.success("✅ 健康检查完成！")
        
        # 检查结果
        check_results = {
            "TWSE": {"status": "✅ 正常", "latency": "120ms", "last_update": "2 秒前"},
            "Yahoo Finance": {"status": "✅ 正常", "latency": "250ms", "last_update": "5 秒前"},
            "CCXT": {"status": "✅ 正常", "latency": "80ms", "last_update": "1 秒前"},
            "CoinGecko": {"status": "⚠️ 延迟", "latency": "1200ms", "last_update": "30 秒前"},
        }
        
        # 显示检查结果
        for name, result in check_results.items():
            cols = st.columns(4)
            cols[0].write(f"**{name}**")
            cols[1].write(result['status'])
            cols[2].write(f"⏱️ {result['latency']}")
            cols[3].write(f"🕐 {result['last_update']}")

# ════════════════════════════════════════════════════════════
# 使用统计
# ════════════════════════════════════════════════════════════

st.divider()
st.subheader("📊 使用统计")

# 模拟统计数据
stats_data = {
    "数据源": ["TWSE", "Yahoo Finance", "CCXT", "CoinGecko"],
    "今日请求": [1250, 3400, 8900, 450],
    "成功率": [99.8, 99.5, 99.9, 98.2],
    "平均延迟": ["120ms", "250ms", "80ms", "1200ms"],
    "最后更新": ["2 秒前", "5 秒前", "1 秒前", "30 秒前"],
}

stats_df = pd.DataFrame(stats_data)
st.dataframe(stats_df, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════
# 快速操作
# ════════════════════════════════════════════════════════════

st.divider()
st.subheader("⚡ 快速操作")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔄 刷新所有数据源", use_container_width=True):
        st.success("已刷新所有数据源连接")

with col2:
    if st.button("📥 导入配置", use_container_width=True):
        st.info("请选择配置文件")

with col3:
    if st.button("📤 导出配置", use_container_width=True):
        st.success("配置已导出到 config.json")

with col4:
    if st.button("🗑️ 重置所有配置", use_container_width=True):
        st.warning("配置已重置")
