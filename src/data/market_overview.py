# 市場總覽 — 資產類別 × 交易類型 矩陣
# 一級：資產 (Asset) | 二級：交易類型 (現貨/期貨/期權/指標) | 三級：板塊/市場
from __future__ import annotations

import logging
import warnings
from typing import Any

import streamlit as st

# 過濾 Yahoo Finance 警告
logging.getLogger("yfinance").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")
warnings.filterwarnings("ignore", message=".*possibly delisted.*")
warnings.filterwarnings("ignore", message=".*No data found.*")

# 矩陣結構：ASSET -> INSTRUMENT -> SECTOR -> [(name, symbol), ...]
# 期貨歸屬到對應資產下（股指期貨→傳統、商品期貨→大宗、外匯期貨→外匯），情緒獨立為儀表板
# 註：Yahoo Finance 不支援加密貨幣合約和期權，這些僅供參考
MARKET_HIERARCHY: dict[str, dict[str, dict[str, list[tuple[str, str]]]]] = {
    "🪙 加密資產": {
        "現貨": {
            "₿ 加密主流": [
                ("BTC", "BTC-USD"),
                ("ETH", "ETH-USD"),
                ("SOL", "SOL-USD"),
                ("BNB", "BNB-USD"),
                ("XRP", "XRP-USD"),
                ("ADA", "ADA-USD"),
            ],
            "🌐 DeFi/L2": [
                ("LINK", "LINK-USD"),
                ("AAVE", "AAVE-USD"),
                ("OP", "OP-USD"),
                ("SUI", "SUI20947-USD"),
            ],
            "🐶 Meme 老牌": [
                ("DOGE", "DOGE-USD"),
                ("SHIB", "SHIB-USD"),
            ],
            "🧪 Meme 新興": [
                ("WIF", "WIF-USD"),
                ("BONK", "BONK-USD"),
                ("FLOKI", "FLOKI-USD"),
            ],
        },
        "期貨/合約": {
            # Yahoo Finance 不支援加密合約，顯示提示
            "提示": [
                ("說明", "YAHOO_HINT"),
            ],
        },
        "期權": {
            # Yahoo Finance 不支援加密期權，顯示提示
            "提示": [
                ("說明", "YAHOO_HINT"),
            ],
        },
    },
    "📈 傳統股票/指數": {
        "現貨": {
            "美股": [
                ("AAPL", "AAPL"),
                ("MSFT", "MSFT"),
                ("NVDA", "NVDA"),
                ("TSLA", "TSLA"),
                ("META", "META"),
                ("GOOGL", "GOOGL"),
                ("AMD", "AMD"),
                ("AVGO", "AVGO"),
                ("JPM", "JPM"),
                ("AMZN", "AMZN"),
            ],
            "美股 · 科技/半導體": [
                ("ASML", "ASML"),
                ("TSM", "TSM"),
                ("INTC", "INTC"),
                ("CRM", "CRM"),
                ("ADBE", "ADBE"),
                ("NOW", "NOW"),
                ("SNOW", "SNOW"),
                ("PLTR", "PLTR"),
            ],
            "美股 · 金融/消費/能源": [
                ("BAC", "BAC"),
                ("WFC", "WFC"),
                ("GS", "GS"),
                ("V", "V"),
                ("MA", "MA"),
                ("WMT", "WMT"),
                ("COST", "COST"),
                ("XOM", "XOM"),
                ("CVX", "CVX"),
            ],
            "港股": [
                ("騰訊", "0700.HK"),
                ("阿里巴巴", "9988.HK"),
                ("港交所", "0388.HK"),
                ("美團", "3690.HK"),
                ("小米", "1810.HK"),
            ],
            "A 股": [
                ("貴州茅台", "600519.SS"),
                ("寧德時代", "300750.SZ"),
                ("比亞迪", "002594.SZ"),
            ],
            "台股": [
                ("台積電", "2330.TW"),
                ("鴻海", "2317.TW"),
                ("聯發科", "2454.TW"),
                ("元大 50", "0050.TW"),
                ("高股息", "00878.TW"),
            ],
            "ETF 大盤/科技": [
                ("S&P500", "SPY"),
                ("Nasdaq", "QQQ"),
                ("道瓊", "DIA"),
                ("全市場", "VTI"),
                ("半導體", "SOXX"),
                ("科技", "XLK"),
                ("創新", "ARKK"),
            ],
            "ETF 策略/區域": [
                ("紅利", "SCHD"),
                ("成長", "VUG"),
                ("價值", "VTV"),
                ("中國", "MCHI"),
                ("台灣", "EWT"),
                ("日本", "EWJ"),
                ("歐洲", "VGK"),
            ],
            "債券": [
                ("美長債", "TLT"),
                ("中期債", "IEF"),
                ("短期債", "SHY"),
                ("高收債", "HYG"),
                ("投資級", "LQD"),
                ("綜合", "BND"),
            ],
            "REITs": [
                ("Vanguard 房地產", "VNQ"),
                ("Realty Income", "O"),
                ("Prologis", "PLD"),
            ],
            "全球指數": [
                ("S&P500", "^GSPC"),
                ("Nasdaq", "^IXIC"),
                ("道瓊", "^DJI"),
                ("日經", "^N225"),
                ("恆生", "^HSI"),
                ("加權", "^TWII"),
                ("德國 DAX", "^GDAXI"),
                ("英國 FTSE", "^FTSE"),
            ],
        },
        "期貨": {
            "股指期貨": [
                ("標普 500", "ES=F"),
                ("納斯達克", "NQ=F"),
                ("道瓊", "YM=F"),
                ("恆生", "HSI=F"),
                ("台指", "TW=F"),
                ("日經", "NIY=F"),
            ],
            "債券期貨": [
                ("10 年期美債", "ZN=F"),
                ("30 年期美債", "ZB=F"),
                ("2 年期美債", "ZT=F"),
            ],
        },
    },
    "💱 外匯": {
        "現貨": {
            "G10 主流": [
                ("歐元/美元", "EURUSD=X"),
                ("英鎊/美元", "GBPUSD=X"),
                ("美元/日圓", "USDJPY=X"),
                ("澳元/美元", "AUDUSD=X"),
                ("美元/加元", "USDCAD=X"),
            ],
            "交叉/新興": [
                ("歐元/日圓", "EURJPY=X"),
                ("美元/離岸人民幣", "USDCNH=X"),
                ("美元/港幣", "USDHKD=X"),
                ("美元/台幣", "USDTWD=X"),
            ],
        },
        "期貨": {
            "外匯期貨": [
                ("歐元", "6E=F"),
                ("日圓", "6J=F"),
                ("英鎊", "6B=F"),
                ("澳元", "6A=F"),
            ],
        },
    },
    "🥇 大宗商品": {
        "現貨": {
            "貴金屬 ETF": [
                ("黃金", "GLD"),
                ("白銀", "SLV"),
                ("鉑金", "PPLT"),
                ("鈀金", "PALL"),
            ],
            "能源/原物料 ETF": [
                ("原油", "USO"),
                ("天然氣", "UNG"),
                ("布蘭特原油", "BNO"),
                ("銅", "CPER"),
                ("綜合商品", "DBC"),
                ("農產品", "DBA"),
            ],
        },
        "期貨": {
            "商品期貨": [
                ("黃金", "GC=F"),
                ("原油", "CL=F"),
                ("天然氣", "NG=F"),
                ("銅", "HG=F"),
                ("玉米", "ZC=F"),
                ("大豆", "ZS=F"),
            ],
        },
    },
    "📊 情緒儀表板": {
        "指標": {
            "🌡️ 加密情緒": [
                ("恐懼貪婪", "FG_INDEX"),
            ],
            "😨 股市情緒": [
                ("VIX", "VIX_INDEX"),
            ],
        },
        "預測市場": {
            "🔮 Polymarket": [
                ("BTC 100K", "POLY_BTC_100K"),
                ("美大選", "POLY_US_ELECTION"),
                ("聯儲決策", "POLY_FED_RATE"),
            ],
        },
    },
}


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_single(symbol: str) -> dict | None:
    """
    逐個拉取單一標的行情（優先使用 fast_info，失敗再回退到 history）
    自動過濾 Yahoo Finance 不支援的代碼
    """
    # 過濾 Yahoo Finance 不支援的代碼
    if symbol in ["YAHOO_HINT", "FG_INDEX", "VIX_INDEX", "POLY_BTC_100K", "POLY_US_ELECTION", "POLY_FED_RATE"]:
        return None

    # 過濾加密合約和期權代碼（Yahoo 不支援）
    if symbol.endswith(".P") or symbol.endswith("-OPTION"):
        return None

    try:
        import yfinance as yf

        t = yf.Ticker(symbol)

        last = None
        prev = None
        currency = None

        # 優先嘗試 fast_info（速度較快）
        try:
            finfo = getattr(t, "fast_info", None) or {}
            last = finfo.get("lastPrice")
            prev = finfo.get("previousClose")
            currency = finfo.get("currency")
        except Exception:
            pass

        # 如 fast_info 取不到價格，回退到 history
        if last is None or prev is None:
            h = t.history(period="5d", interval="1d")
            if h.empty or len(h) < 2:
                return None
            last = float(h["Close"].iloc[-1])
            prev = float(h["Close"].iloc[-2])

        change = ((last - prev) / prev * 100) if prev else 0

        data: dict[str, Any] = {
            "price": float(last),
            "change": round(change, 2),
        }
        if currency:
            data["currency"] = currency

        return data
    except Exception:
        return None


def _collect_all_symbols() -> list[str]:
    """收集所有需要拉取的 Yahoo Finance 代碼。"""
    symbols = []
    skip = {"YAHOO_HINT", "FG_INDEX", "VIX_INDEX", "POLY_BTC_100K", "POLY_US_ELECTION", "POLY_FED_RATE"}
    skip_suffixes = {".P", "-OPTION"}
    skip_patterns = {"NFP", "CPI", "PCE", "GDP", "PMI", "HALVING", "RATE"}

    for markets in MARKET_HIERARCHY.values():
        for sectors in markets.values():
            for tickers in sectors.values():
                for _, sym in tickers:
                    if sym in skip:
                        continue
                    if any(sym.endswith(s) for s in skip_suffixes):
                        continue
                    if any(p in sym for p in skip_patterns):
                        continue
                    symbols.append(sym)

    # 加上 futures 和 trending
    for _, sym in YAHOO_REFERENCE_FUTURES:
        if sym not in symbols:
            symbols.append(sym)
    for _, sym in YAHOO_REFERENCE_TRENDING:
        if sym not in symbols:
            symbols.append(sym)

    return symbols


@st.cache_data(ttl=120, show_spinner=False)
def _batch_fetch_prices(symbols: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    """
    批量下載 Yahoo Finance 數據（一次請求多個 ticker），比逐個快 5-10x。
    """
    import yfinance as yf

    result: dict[str, dict[str, Any]] = {}
    try:
        # 批量下載 5 天數據（用於計算 change）
        data = yf.download(list(symbols), period="5d", interval="1d", progress=False, threads=True)
        if data.empty:
            return result

        close = data.get("Close")
        if close is None:
            return result

        for sym in symbols:
            try:
                if sym in close.columns:
                    col = close[sym].dropna()
                    if len(col) >= 2:
                        last = float(col.iloc[-1])
                        prev = float(col.iloc[-2])
                        change = ((last - prev) / prev * 100) if prev else 0
                        result[sym] = {"price": last, "change": round(change, 2)}
            except Exception:
                continue
    except Exception:
        pass
    return result


@st.cache_data(ttl=120, show_spinner=False)
def fetch_market_data() -> dict[str, dict[str, dict[str, list[dict[str, Any]]]]]:
    """
    拉取各板塊即時行情（2 分鐘快取）。批量下載優化。
    """
    # 先批量下載所有 Yahoo Finance 數據
    all_symbols = _collect_all_symbols()
    batch_data = _batch_fetch_prices(tuple(all_symbols))

    result: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    for group_name, markets in MARKET_HIERARCHY.items():
        group_data: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for market_name, sectors in markets.items():
            market_data: dict[str, list[dict[str, Any]]] = {}
            for sector, tickers in sectors.items():
                sector_data: list[dict[str, Any]] = []
                for name, sym in tickers:
                    # 跳過提示類代碼
                    if sym == "YAHOO_HINT":
                        sector_data.append(
                            {
                                "name": "💡 Yahoo Finance 不支援此類數據",
                                "symbol": sym,
                                "price": 0,
                                "change": 0,
                                "note": "加密合約/期權請使用交易所 API",
                            }
                        )
                        continue

                    # 經濟數據等非交易型指標無法透過 yfinance 抓取
                    if any(x in sym for x in ["NFP", "CPI", "PCE", "GDP", "PMI", "HALVING", "RATE"]):
                        continue

                    # 處理恐懼貪婪指數
                    if sym == "FG_INDEX":
                        try:
                            from src.data.sources.api_hub import get_current_fear_greed

                            fg = get_current_fear_greed()
                            if fg:
                                sector_data.append(
                                    {
                                        "name": name,
                                        "symbol": sym,
                                        "price": fg["value"],
                                        "change": 0,
                                        "classification": fg["classification"],
                                    }
                                )
                        except Exception:
                            pass
                        continue

                    # 處理 VIX 指數
                    if sym == "VIX_INDEX":
                        try:
                            from src.data.sources.api_hub import fetch_cboe_vix

                            vix = fetch_cboe_vix()
                            if vix:
                                sector_data.append(
                                    {
                                        "name": name,
                                        "symbol": sym,
                                        "price": float(vix.get("close", 0)),
                                        "change": 0,
                                        "open": float(vix.get("open", 0)),
                                        "high": float(vix.get("high", 0)),
                                        "low": float(vix.get("low", 0)),
                                    }
                                )
                        except Exception:
                            pass
                        continue

                    # 優先從批量數據取，失敗才回退到逐個請求
                    data = batch_data.get(sym)
                    if not data:
                        data = _fetch_single(sym)
                    if data:
                        sector_data.append({"name": name, "symbol": sym, **data})
                if sector_data:
                    market_data[sector] = sector_data
            if market_data:
                group_data[market_name] = market_data
        if group_data:
            result[group_name] = group_data
    return result


# ─── 參考 Yahoo Finance 首頁：期貨報價與熱門標的 ───
YAHOO_REFERENCE_FUTURES: list[tuple[str, str]] = [
    ("標普500期貨", "ES=F"),
    ("納斯達克期貨", "NQ=F"),
    ("道瓊期貨", "YM=F"),
    ("原油", "CL=F"),
    ("黃金", "GC=F"),
    ("白銀", "SI=F"),
    ("VIX", "^VIX"),
]
YAHOO_REFERENCE_TRENDING: list[tuple[str, str]] = [
    ("NVIDIA", "NVDA"),
    ("蘋果", "AAPL"),
    ("微軟", "MSFT"),
    ("Google", "GOOGL"),
    ("亞馬遜", "AMZN"),
    ("Meta", "META"),
    ("特斯拉", "TSLA"),
    ("Netflix", "NFLX"),
    ("Palantir", "PLTR"),
    ("比特幣", "BTC-USD"),
    ("以太坊", "ETH-USD"),
]


@st.cache_data(ttl=120, show_spinner=False)
def fetch_yahoo_reference_futures() -> list[dict[str, Any]]:
    """Yahoo Finance 參考：期貨報價（批量優化）。"""
    syms = [s for _, s in YAHOO_REFERENCE_FUTURES]
    batch_data = _batch_fetch_prices(tuple(syms))
    out: list[dict[str, Any]] = []
    for name, sym in YAHOO_REFERENCE_FUTURES:
        data = batch_data.get(sym) or _fetch_single(sym)
        if data:
            out.append({"name": name, "symbol": sym, **data})
    return out


@st.cache_data(ttl=120, show_spinner=False)
def fetch_yahoo_reference_trending() -> list[dict[str, Any]]:
    """Yahoo Finance 參考：熱門標的（批量優化）。"""
    syms = [s for _, s in YAHOO_REFERENCE_TRENDING]
    batch_data = _batch_fetch_prices(tuple(syms))
    out: list[dict[str, Any]] = []
    for name, sym in YAHOO_REFERENCE_TRENDING:
        data = batch_data.get(sym) or _fetch_single(sym)
        if data:
            out.append({"name": name, "symbol": sym, **data})
    return out
