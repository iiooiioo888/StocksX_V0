# 市場總覽 — 各板塊即時漲跌
from __future__ import annotations

import streamlit as st
from typing import Any


MARKET_TICKERS = {
    "₿ 加密主流": [
        ("BTC", "BTC-USD"), ("ETH", "ETH-USD"), ("SOL", "SOL-USD"),
        ("BNB", "BNB-USD"), ("XRP", "XRP-USD"), ("DOGE", "DOGE-USD"),
    ],
    "📈 美股科技": [
        ("AAPL", "AAPL"), ("MSFT", "MSFT"), ("NVDA", "NVDA"),
        ("TSLA", "TSLA"), ("META", "META"), ("GOOGL", "GOOGL"),
    ],
    "🏦 ETF": [
        ("S&P500", "SPY"), ("Nasdaq", "QQQ"), ("黃金", "GLD"),
        ("原油", "USO"), ("美債", "TLT"), ("台灣50", "0050.TW"),
    ],
    "🐸 Meme": [
        ("DOGE", "DOGE-USD"), ("SHIB", "SHIB-USD"), ("PEPE", "PEPE-USD"),
        ("WIF", "WIF-USD"), ("BONK", "BONK-USD"), ("FLOKI", "FLOKI-USD"),
    ],
}


@st.cache_data(ttl=120, show_spinner=False)
def fetch_market_data() -> dict[str, list[dict[str, Any]]]:
    """拉取各板塊即時行情（2 分鐘快取）"""
    try:
        import yfinance as yf
    except ImportError:
        return {}

    result = {}
    for sector, tickers in MARKET_TICKERS.items():
        sector_data = []
        symbols = [t[1] for t in tickers]
        names = [t[0] for t in tickers]
        try:
            data = yf.download(symbols, period="2d", interval="1d", progress=False, threads=True)
            if data.empty:
                continue
            close = data.get("Close")
            if close is None:
                continue
            for i, sym in enumerate(symbols):
                try:
                    if isinstance(close, type(data)):
                        col = close[sym] if sym in close.columns else None
                    else:
                        col = close
                    if col is None or len(col.dropna()) < 2:
                        continue
                    vals = col.dropna()
                    last = float(vals.iloc[-1])
                    prev = float(vals.iloc[-2]) if len(vals) > 1 else last
                    change = ((last - prev) / prev * 100) if prev else 0
                    sector_data.append({
                        "name": names[i], "symbol": sym,
                        "price": last, "change": round(change, 2),
                    })
                except Exception:
                    continue
        except Exception:
            continue
        if sector_data:
            result[sector] = sector_data
    return result
