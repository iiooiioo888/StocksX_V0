# 共用配置 — 策略標籤、顏色、市場分類
from __future__ import annotations

STRATEGY_LABELS = {
    "sma_cross": "雙均線交叉", "buy_and_hold": "買入持有",
    "rsi_signal": "RSI", "macd_cross": "MACD 交叉", "bollinger_signal": "布林帶",
    "ema_cross": "EMA 交叉", "donchian_channel": "唐奇安通道",
    "supertrend": "超級趨勢", "dual_thrust": "雙推力", "vwap_reversion": "VWAP 回歸",
    "ichimoku": "一目均衡表", "stochastic": "KD 隨機指標",
    "williams_r": "威廉指標", "adx_trend": "ADX 趨勢", "parabolic_sar": "拋物線 SAR",
}

STRATEGY_COLORS = {
    "sma_cross": "#636EFA", "buy_and_hold": "#00CC96", "rsi_signal": "#EF553B",
    "macd_cross": "#AB63FA", "bollinger_signal": "#FFA15A", "ema_cross": "#19D3F3",
    "donchian_channel": "#FF6692", "supertrend": "#B6E880", "dual_thrust": "#FF97FF",
    "vwap_reversion": "#FECB52", "ichimoku": "#17BECF", "stochastic": "#7F7F7F",
    "williams_r": "#E377C2", "adx_trend": "#8C564B", "parabolic_sar": "#2CA02C",
}

CRYPTO_CATEGORIES = {
    "🔥 主流永續": [
        "BTC/USDT:USDT", "ETH/USDT:USDT", "BNB/USDT:USDT", "SOL/USDT:USDT",
        "XRP/USDT:USDT", "DOGE/USDT:USDT", "ADA/USDT:USDT", "AVAX/USDT:USDT",
        "LINK/USDT:USDT", "DOT/USDT:USDT", "LTC/USDT:USDT",
    ],
    "💎 主流現貨": [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
        "DOGE/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "LTC/USDT",
    ],
    "🌐 DeFi": ["UNI/USDT", "AAVE/USDT", "LINK/USDT", "ATOM/USDT", "INJ/USDT"],
    "🚀 Layer2 / 新幣": [
        "ARB/USDT", "OP/USDT", "SUI/USDT", "SEI/USDT", "TIA/USDT",
        "APT/USDT", "NEAR/USDT", "WLD/USDT", "JUP/USDT", "STRK/USDT",
    ],
    "🐸 Meme": ["DOGE/USDT", "SHIB/USDT", "PEPE/USDT", "BONK/USDT", "WIF/USDT", "FLOKI/USDT"],
}

TRADITIONAL_CATEGORIES = {
    "📈 美股": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "INTC",
               "NFLX", "CRM", "ORCL", "ADBE", "PYPL", "COIN", "MSTR", "PLTR", "UBER"],
    "🇹🇼 台股": ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2881.TW", "2882.TW",
               "2303.TW", "3711.TW", "2412.TW", "1301.TW"],
    "🏦 ETF": ["SPY", "QQQ", "IWM", "DIA", "VTI", "GLD", "SLV", "USO", "TLT", "HYG",
              "ARKK", "SOXX", "XLF", "XLE", "XLK", "0050.TW", "00878.TW", "00919.TW"],
    "🛢️ 期貨 / 商品": ["GC=F", "SI=F", "CL=F", "NG=F", "ES=F", "NQ=F", "YM=F", "RTY=F"],
    "🌍 指數": ["^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^GDAXI", "^N225", "^HSI", "^TWII"],
}

EXCHANGE_OPTIONS = {
    "okx": "OKX", "bitget": "Bitget", "gate": "Gate.io", "kucoin": "KuCoin（僅現貨）",
    "mexc": "MEXC", "htx": "HTX (火幣)", "bingx": "BingX", "woo": "WOO X",
    "binance": "Binance（受地區限制）", "bybit": "Bybit（受地區限制）",
    "cryptocom": "Crypto.com（僅現貨）",
}

APP_CSS = """
/* 全局背景 */
.stApp {background: linear-gradient(160deg, #0f0f1a 0%, #1a1a2e 40%, #16213e 100%);}
section[data-testid="stSidebar"] {background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%); border-right: 1px solid #2a2a4a;}
section[data-testid="stSidebar"] * {color: #e0e0e8 !important;}
section[data-testid="stSidebar"] .stSelectbox label, section[data-testid="stSidebar"] .stRadio label {color: #b0b0c8 !important;}

/* 主要文字 */
.stApp, .stApp p, .stApp span, .stApp li {color: #e0e0e8;}
.stApp h1, .stApp h2, .stApp h3 {color: #f0f0ff;}
.stApp a {color: #6ea8fe;}

/* 指標卡片 */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e1e3a, #252545);
    border: 1px solid #3a3a5c; border-radius: 12px; padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {font-size: 1.3rem; color: #f0f0ff !important;}
[data-testid="stMetric"] [data-testid="stMetricLabel"] {color: #9090b0 !important;}

/* 展開區塊 */
div[data-testid="stExpander"] {
    background: rgba(26,26,46,0.6); border: 1px solid #3a3a5c; border-radius: 10px;
}
div[data-testid="stExpander"] summary {color: #d0d0e8 !important;}

/* 按鈕 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4a6cf7, #6366f1) !important;
    border: none !important; color: white !important; border-radius: 8px;
    box-shadow: 0 2px 10px rgba(99,102,241,0.3);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #5b7cf8, #7577f2) !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.5);
}
.stButton > button[kind="secondary"], .stButton > button:not([kind]) {
    background: rgba(40,40,70,0.8) !important; border: 1px solid #4a4a6c !important;
    color: #d0d0e8 !important; border-radius: 8px;
}

/* Tab */
.stTabs [data-baseweb="tab-list"] {background: transparent; border-bottom: 1px solid #3a3a5c;}
.stTabs [data-baseweb="tab"] {color: #9090b0 !important; background: transparent;}
.stTabs [aria-selected="true"] {color: #6ea8fe !important; border-bottom: 2px solid #6ea8fe;}

/* 表格 */
[data-testid="stDataFrame"] {border-radius: 8px; overflow: hidden;}

/* 輸入框 */
.stTextInput input, .stNumberInput input, .stSelectbox > div > div {
    background: rgba(30,30,55,0.8) !important; border: 1px solid #3a3a5c !important;
    color: #e0e0e8 !important; border-radius: 6px;
}

/* 面包屑 */
.breadcrumb {font-size: 0.85rem; color: #7070a0; margin-bottom: 0.5rem;}

/* 動畫 */
@keyframes fadeIn {from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)}}
.success-banner {
    background: linear-gradient(135deg, #1a3a2a, #1e4a32); border: 1px solid #28a745;
    border-radius: 10px; padding: 15px; margin: 10px 0; animation: fadeIn 0.5s; color: #a0e8b0;
}
.fail-banner {
    background: linear-gradient(135deg, #3a1a1a, #4a1e1e); border: 1px solid #dc3545;
    border-radius: 10px; padding: 15px; margin: 10px 0; animation: fadeIn 0.5s; color: #e8a0a0;
}

/* info/warning/error */
div[data-testid="stAlert"] {border-radius: 8px;}
"""
