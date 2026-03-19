# 共用配置 — 策略標籤、顏色、市場分類（v5.1 統一化）
from __future__ import annotations

# Settings 統一由 src.core.config 提供，這裡做導出保持向後兼容

STRATEGY_LABELS = {
    "sma_cross": "雙均線交叉",
    "buy_and_hold": "買入持有",
    "rsi_signal": "RSI",
    "macd_cross": "MACD 交叉",
    "bollinger_signal": "布林帶",
    "ema_cross": "EMA 交叉",
    "donchian_channel": "唐奇安通道",
    "supertrend": "超級趨勢",
    "dual_thrust": "雙推力",
    "vwap_reversion": "VWAP 回歸",
    "ichimoku": "一目均衡表",
    "stochastic": "KD 隨機指標",
    "williams_r": "威廉指標",
    "adx_trend": "ADX 趨勢",
    "parabolic_sar": "拋物線 SAR",
}

STRATEGY_COLORS = {
    "sma_cross": "#636EFA",
    "buy_and_hold": "#00CC96",
    "rsi_signal": "#EF553B",
    "macd_cross": "#AB63FA",
    "bollinger_signal": "#FFA15A",
    "ema_cross": "#19D3F3",
    "donchian_channel": "#FF6692",
    "supertrend": "#B6E880",
    "dual_thrust": "#FF97FF",
    "vwap_reversion": "#FECB52",
    "ichimoku": "#17BECF",
    "stochastic": "#7F7F7F",
    "williams_r": "#E377C2",
    "adx_trend": "#8C564B",
    "parabolic_sar": "#2CA02C",
}

CRYPTO_CATEGORIES = {
    "🔥 主流永續": [
        "BTC/USDT:USDT",
        "ETH/USDT:USDT",
        "BNB/USDT:USDT",
        "SOL/USDT:USDT",
        "XRP/USDT:USDT",
        "DOGE/USDT:USDT",
        "ADA/USDT:USDT",
        "AVAX/USDT:USDT",
        "LINK/USDT:USDT",
        "DOT/USDT:USDT",
        "LTC/USDT:USDT",
    ],
    "💎 主流現貨": [
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT",
        "SOL/USDT",
        "XRP/USDT",
        "DOGE/USDT",
        "ADA/USDT",
        "AVAX/USDT",
        "LINK/USDT",
        "DOT/USDT",
        "LTC/USDT",
    ],
    "🌐 DeFi": ["UNI/USDT", "AAVE/USDT", "LINK/USDT", "ATOM/USDT", "INJ/USDT"],
    "🚀 Layer2 / 新幣": [
        "ARB/USDT",
        "OP/USDT",
        "SUI/USDT",
        "SEI/USDT",
        "TIA/USDT",
        "APT/USDT",
        "NEAR/USDT",
        "WLD/USDT",
        "JUP/USDT",
        "STRK/USDT",
    ],
    "🐸 Meme": ["DOGE/USDT", "SHIB/USDT", "PEPE/USDT", "BONK/USDT", "WIF/USDT", "FLOKI/USDT"],
}

EXCHANGE_OPTIONS = ["binance", "okx", "bybit", "gate", "bitget", "huobi", "kucoin", "mexc"]

TRADITIONAL_CATEGORIES = {
    "🇺🇸 美股": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "SPY", "QQQ"],
    "🇹🇼 台股": ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "0050.TW", "0056.TW"],
    "📈 ETF": ["SPY", "QQQ", "IWM", "EFA", "VWO", "TLT", "GLD", "SLV"],
}

# Settings 和 get_settings 已從 src.core.config 導入（見上方）


def format_price(price: float, decimals: int = 2) -> str:
    """格式化價格顯示"""
    if price >= 1000:
        return f"{price:,.{decimals}f}"
    elif price >= 1:
        return f"{price:.{decimals}f}"
    else:
        return f"{price:.{max(decimals, 4)}f}"


# ─── CSS ───

APP_CSS = """
<style>
/* ─── 全局 ─── */
.stApp { background: #0e1117; color: #e0e0e0; }
.stSidebar { background: #161b22; }
[data-testid="stMetricValue"] { color: #58a6ff; }
.stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: #fff; border: none; border-radius: 8px; padding: 0.5rem 1.2rem;
}
.stButton > button:hover { background: linear-gradient(135deg, #2ea043, #3fb950); }
.stSelectbox > div > div { background: #161b22; border-color: #30363d; }
.stTextInput > div > div > input { background: #161b22; border-color: #30363d; color: #e0e0e0; }
.stTabs [data-baseweb="tab"] { color: #8b949e; }
.stTabs [aria-selected="true"] { color: #58a6ff; border-bottom-color: #58a6ff; }
</style>
"""
