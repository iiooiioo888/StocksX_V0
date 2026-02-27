# 市場總覽 — 各板塊即時漲跌
from __future__ import annotations

import streamlit as st
from typing import Any

MARKET_TICKERS = {
    "₿ 加密主流": [
        ("BTC", "BTC-USD"), ("ETH", "ETH-USD"), ("SOL", "SOL-USD"),
        ("BNB", "BNB-USD"), ("XRP", "XRP-USD"), ("ADA", "ADA-USD"),
    ],
    "🌐 DeFi/L2": [
        ("UNI", "UNI-USD"), ("LINK", "LINK-USD"), ("AAVE", "AAVE-USD"),
        ("ARB", "ARB11841-USD"), ("OP", "OP-USD"), ("SUI", "SUI20947-USD"),
    ],
    "🐸 Meme": [
        ("DOGE", "DOGE-USD"), ("SHIB", "SHIB-USD"),
        ("BONK", "BONK-USD"), ("FLOKI", "FLOKI-USD"),
    ],
    "📈 美股科技": [
        ("AAPL", "AAPL"), ("MSFT", "MSFT"), ("NVDA", "NVDA"),
        ("TSLA", "TSLA"), ("META", "META"), ("GOOGL", "GOOGL"),
    ],
    "💊 美股醫療": [
        ("UNH", "UNH"), ("JNJ", "JNJ"), ("LLY", "LLY"),
        ("PFE", "PFE"), ("ABBV", "ABBV"), ("MRK", "MRK"),
    ],
    "🏦 美股 ETF": [
        ("S&P500", "SPY"), ("Nasdaq", "QQQ"), ("小型股", "IWM"),
        ("道瓊", "DIA"), ("全市場", "VTI"), ("半導體", "SOXX"),
    ],
    "🥇 商品": [
        ("黃金", "GLD"), ("白銀", "SLV"), ("原油", "USO"),
        ("天然氣", "UNG"), ("銅", "CPER"),
    ],
    "📜 債券": [
        ("美長債", "TLT"), ("中期債", "IEF"), ("短期債", "SHY"),
        ("高收債", "HYG"), ("投資級", "LQD"),
    ],
    "🇹🇼 台灣": [
        ("台積電", "2330.TW"), ("鴻海", "2317.TW"), ("聯發科", "2454.TW"),
        ("元大50", "0050.TW"), ("高股息", "00878.TW"),
    ],
    "🌍 全球指數": [
        ("S&P500", "^GSPC"), ("Nasdaq", "^IXIC"), ("道瓊", "^DJI"),
        ("日經", "^N225"), ("恆生", "^HSI"), ("加權", "^TWII"),
    ],
}


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_single(symbol: str) -> dict | None:
    """逐個拉取單一標的行情"""
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        h = t.history(period="5d", interval="1d")
        if h.empty or len(h) < 2:
            return None
        last = float(h["Close"].iloc[-1])
        prev = float(h["Close"].iloc[-2])
        change = ((last - prev) / prev * 100) if prev else 0
        return {"price": last, "change": round(change, 2)}
    except Exception:
        return None


@st.cache_data(ttl=120, show_spinner=False)
def fetch_market_data() -> dict[str, list[dict[str, Any]]]:
    """拉取各板塊即時行情（2 分鐘快取）"""
    result = {}
    for sector, tickers in MARKET_TICKERS.items():
        sector_data = []
        for name, sym in tickers:
            data = _fetch_single(sym)
            if data:
                sector_data.append({"name": name, "symbol": sym, **data})
        if sector_data:
            result[sector] = sector_data
    return result
