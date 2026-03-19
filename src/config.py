# 共用配置 — 策略標籤、顏色、市場分類
from __future__ import annotations

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

TRADITIONAL_CATEGORIES = {
    "📈 美股": [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "NVDA",
        "META",
        "TSLA",
        "AMD",
        "INTC",
        "NFLX",
        "CRM",
        "ORCL",
        "ADBE",
        "PYPL",
        "COIN",
        "MSTR",
        "PLTR",
        "UBER",
    ],
    "🇹🇼 台股": [
        "2330.TW",
        "2317.TW",
        "2454.TW",
        "2308.TW",
        "2881.TW",
        "2882.TW",
        "2303.TW",
        "3711.TW",
        "2412.TW",
        "1301.TW",
    ],
    "🏦 ETF": [
        "SPY",
        "QQQ",
        "IWM",
        "DIA",
        "VTI",
        "GLD",
        "SLV",
        "USO",
        "TLT",
        "HYG",
        "ARKK",
        "SOXX",
        "XLF",
        "XLE",
        "XLK",
        "0050.TW",
        "00878.TW",
        "00919.TW",
    ],
    "🛢️ 期貨 / 商品": ["GC=F", "SI=F", "CL=F", "NG=F", "ES=F", "NQ=F", "YM=F", "RTY=F"],
    "🌍 指數": ["^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^GDAXI", "^N225", "^HSI", "^TWII"],
}

EXCHANGE_OPTIONS = {
    "okx": "OKX",
    "bitget": "Bitget",
    "gate": "Gate.io",
    "kucoin": "KuCoin（僅現貨）",
    "mexc": "MEXC",
    "htx": "HTX (火幣)",
    "bingx": "BingX",
    "woo": "WOO X",
    "binance": "Binance（受地區限制）",
    "bybit": "Bybit（受地區限制）",
    "cryptocom": "Crypto.com（僅現貨）",
}


def format_price(price: float, symbol: str = "") -> str:
    """智能價格格式化"""
    if price >= 10000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    else:
        return f"${price:.8f}"


from src.static.css import APP_CSS
