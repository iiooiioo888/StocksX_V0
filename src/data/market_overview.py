# 市場總覽 — 各板塊即時漲跌
from __future__ import annotations

import streamlit as st
from typing import Any

# 更完整的市場層級：GROUP -> MARKET -> SECTOR -> [(name, symbol), ...]
MARKET_HIERARCHY: dict[str, dict[str, dict[str, list[tuple[str, str]]]]] = {
    "🪙 加密市場": {
        "現貨": {
            "₿ 加密主流": [
                ("BTC", "BTC-USD"), ("ETH", "ETH-USD"), ("SOL", "SOL-USD"),
                ("BNB", "BNB-USD"), ("XRP", "XRP-USD"), ("ADA", "ADA-USD"),
            ],
            "🌐 DeFi/L2": [
                ("UNI", "UNI-USD"), ("LINK", "LINK-USD"), ("AAVE", "AAVE-USD"),
                ("ARB", "ARB11841-USD"), ("OP", "OP-USD"), ("SUI", "SUI20947-USD"),
            ],
            "🐶 Meme 老牌": [
                ("DOGE", "DOGE-USD"), ("SHIB", "SHIB-USD"),
            ],
            "🧪 Meme 新興": [
                ("PEPE", "PEPE-USD"), ("WIF", "WIF-USD"),
                ("BONK", "BONK-USD"), ("FLOKI", "FLOKI-USD"),
            ],
        },
        "合約/衍生": {
            "Perpetual": [
                ("BTC 永續", "BTCUSDT.P"), ("ETH 永續", "ETHUSDT.P"), ("SOL 永續", "SOLUSDT.P"),
            ],
            "期權": [
                ("BTC 期權", "BTC-OPTION"), ("ETH 期權", "ETH-OPTION"),
            ],
        },
    },
    "📈 傳統市場": {
        "美股": {
            "📈 美股科技": [
                ("AAPL", "AAPL"), ("MSFT", "MSFT"), ("NVDA", "NVDA"),
                ("TSLA", "TSLA"), ("META", "META"), ("GOOGL", "GOOGL"),
            ],
            "🔌 半導體": [
                ("AMD", "AMD"), ("AVGO", "AVGO"), ("ASML", "ASML"),
                ("TSM", "TSM"), ("INTC", "INTC"),
            ],
            "🤖 AI / 雲端": [
                ("CRM", "CRM"), ("ADBE", "ADBE"), ("NOW", "NOW"),
                ("SNOW", "SNOW"), ("PLTR", "PLTR"),
            ],
            "💊 美股醫療": [
                ("UNH", "UNH"), ("JNJ", "JNJ"), ("LLY", "LLY"),
                ("PFE", "PFE"), ("ABBV", "ABBV"), ("MRK", "MRK"),
            ],
            "🏦 金融": [
                ("JPM", "JPM"), ("BAC", "BAC"), ("WFC", "WFC"),
                ("GS", "GS"), ("MS", "MS"), ("V", "V"), ("MA", "MA"),
            ],
            "🛒 消費": [
                ("AMZN", "AMZN"), ("WMT", "WMT"), ("COST", "COST"),
                ("HD", "HD"), ("NKE", "NKE"), ("MCD", "MCD"),
            ],
            "⚡ 能源": [
                ("XOM", "XOM"), ("CVX", "CVX"), ("COP", "COP"), ("SLB", "SLB"),
            ],
            "🏭 工業": [
                ("CAT", "CAT"), ("BA", "BA"), ("UPS", "UPS"), ("HON", "HON"),
            ],
        },
        "港股": {
            "🇭🇰 港股藍籌": [
                ("騰訊", "0700.HK"), ("阿里巴巴", "9988.HK"), ("港交所", "0388.HK"),
                ("中國建行", "0939.HK"), ("中國平安", "2318.HK"), ("友邦保險", "1299.HK"),
            ],
            "🏠 地產": [
                ("領展", "0823.HK"), ("新鴻基地產", "0016.HK"), ("長實集團", "1113.HK"),
            ],
            "🎮 科技/遊戲": [
                ("網易", "9999.HK"), ("快手", "1024.HK"), ("美團", "3690.HK"), ("小米", "1810.HK"),
            ],
        },
        "A 股": {
            "🇨🇳 滬深藍籌": [
                ("貴州茅台", "600519.SS"), ("招商銀行", "600036.SS"),
                ("中國平安", "601318.SS"), ("寧德時代", "300750.SZ"), ("格力電器", "000651.SZ"),
            ],
            "🔋 新能源": [
                ("比亞迪", "002594.SZ"), ("隆基綠能", "601012.SS"), ("陽光電源", "300274.SZ"),
            ],
        },
        "台股": {
            "🇹🇼 台灣": [
                ("台積電", "2330.TW"), ("鴻海", "2317.TW"), ("聯發科", "2454.TW"),
                ("元大 50", "0050.TW"), ("高股息", "00878.TW"),
            ],
            "📦 傳產/金融": [
                ("富邦金", "2881.TW"), ("國泰金", "2882.TW"),
                ("中信金", "2891.TW"), ("統一", "1216.TW"),
            ],
        },
        "ETF": {
            "🏦 美股 ETF 大盤": [
                ("S&P500", "SPY"), ("Nasdaq", "QQQ"), ("小型股", "IWM"),
                ("道瓊", "DIA"), ("全市場", "VTI"),
            ],
            "🤖 AI / 科技 ETF": [
                ("半導體", "SOXX"), ("半導體 (台股權重)", "SMH"),
                ("科技", "XLK"), ("創新", "ARKK"), ("次世代網路", "ARKW"),
            ],
            "💰 策略/因子": [
                ("紅利", "SCHD"), ("低波動", "USMV"),
                ("成長", "VUG"), ("價值", "VTV"), ("動量", "MTUM"),
            ],
            "🌏 國家/區域": [
                ("中國", "MCHI"), ("台灣", "EWT"), ("日本", "EWJ"),
                ("歐洲", "VGK"), ("新興市場", "VWO"),
            ],
        },
        "商品": {
            "🥇 貴金屬": [
                ("黃金", "GLD"), ("白銀", "SLV"), ("鉑金", "PPLT"), ("鈀金", "PALL"),
            ],
            "🛢️ 能源商品": [
                ("原油", "USO"), ("天然氣", "UNG"), ("布蘭特原油", "BNO"),
            ],
            "⚙️ 原物料 / 農產品": [
                ("銅", "CPER"), ("綜合商品", "DBC"), ("農產品", "DBA"),
                ("玉米", "CORN"), ("小麥", "WEAT"),
            ],
        },
        "債券": {
            "📜 債券": [
                ("美長債", "TLT"), ("中期債", "IEF"), ("短期債", "SHY"),
                ("高收債", "HYG"), ("投資級", "LQD"),
                ("美國債券綜合", "BND"), ("美國債券綜合 (AGG)", "AGG"),
                ("新興市場債", "EMB"),
            ],
        },
        "🏢 房地產 (REITs)": {
            "🇺🇸 美股 REITs": [
                ("Vanguard 房地產", "VNQ"), ("Realty Income", "O"),
                ("Prologis", "PLD"), ("American Tower", "AMT"),
            ],
            "🇭🇰 港股 REITs": [
                ("領展", "0823.HK"), ("置富", "0778.HK"), ("陽光", "0435.HK"),
            ],
        },
        "全球指數": {
            "🌍 全球指數": [
                ("S&P500", "^GSPC"), ("Nasdaq", "^IXIC"), ("道瓊", "^DJI"),
                ("日經", "^N225"), ("恆生", "^HSI"), ("加權", "^TWII"),
                ("歐洲 Stoxx50", "^STOXX50E"), ("德國 DAX", "^GDAXI"),
                ("英國 FTSE100", "^FTSE"), ("上證", "000001.SS"), ("深證", "399001.SZ"),
            ],
        },
    },
    "💱 外匯市場": {
        "主要貨幣": {
            "G10 主流": [
                ("歐元/美元", "EURUSD=X"), ("英鎊/美元", "GBPUSD=X"),
                ("美元/日圓", "USDJPY=X"), ("美元/瑞郎", "USDCHF=X"),
                ("澳元/美元", "AUDUSD=X"), ("美元/加元", "USDCAD=X"),
            ],
        },
        "交叉貨幣": {
            "主要交叉": [
                ("歐元/日圓", "EURJPY=X"), ("英鎊/日圓", "GBPJPY=X"),
                ("澳元/日圓", "AUDJPY=X"), ("歐元/英鎊", "EURGBP=X"),
                ("紐元/美元", "NZDUSD=X"),
            ],
        },
        "新興/離岸": {
            "新興貨幣": [
                ("美元/離岸人民幣", "USDCNH=X"), ("美元/在岸人民幣", "USDCNY=X"),
                ("美元/港幣", "USDHKD=X"), ("美元/台幣", "USDTWD=X"),
                ("美元/韓元", "USDKRW=X"), ("美元/新加坡幣", "USDSGD=X"),
            ],
        },
    },
    "📑 期貨市場": {
        "股指期貨": {
            "股指": [
                ("標普 500", "ES=F"), ("納斯達克", "NQ=F"), ("道瓊", "YM=F"),
                ("恆生", "HSI=F"), ("台指", "TW=F"), ("日經", "NIY=F"),
            ],
        },
        "商品期貨": {
            "商品": [
                ("黃金", "GC=F"), ("原油", "CL=F"), ("天然氣", "NG=F"),
                ("銅", "HG=F"), ("玉米", "ZC=F"), ("大豆", "ZS=F"),
            ],
        },
        "債券期貨": {
            "美債": [
                ("10 年期美債", "ZN=F"), ("30 年期美債", "ZB=F"), ("2 年期美債", "ZT=F"),
            ],
        },
        "外匯期貨": {
            "主要外匯期貨": [
                ("歐元", "6E=F"), ("日圓", "6J=F"), ("英鎊", "6B=F"), ("澳元", "6A=F"),
            ],
        },
    },
    "📊 經濟數據": {
        "美國": {
            "美國經濟": [
                ("非農就業", "NFP"), ("CPI 通脹", "CPI"), ("核心 PCE", "PCE"),
                ("聯儲利率", "FEDRATE"), ("GDP", "GDP"),
            ],
        },
        "中國": {
            "中國經濟": [
                ("PMI 製造業", "CN_PMI"), ("CPI", "CN_CPI"),
                ("PPI", "CN_PPI"), ("社會融資", "CN_TS"),
            ],
        },
    },
}


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_single(symbol: str) -> dict | None:
    """逐個拉取單一標的行情（優先使用 fast_info，失敗再回退到 history）"""
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


@st.cache_data(ttl=120, show_spinner=False)
def fetch_market_data() -> dict[str, dict[str, dict[str, list[dict[str, Any]]]]]:
    """
    拉取各板塊即時行情（2 分鐘快取），結構：
    {
      "🪙 加密市場": {
        "現貨": { "₿ 加密主流": [...], ... },
      },
      "📈 傳統市場": {
        "美股": { "📈 美股科技": [...], ... },
        "ETF": { ... },
        ...
      },
    }
    """
    result: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    for group_name, markets in MARKET_HIERARCHY.items():
        group_data: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for market_name, sectors in markets.items():
            market_data: dict[str, list[dict[str, Any]]] = {}
            for sector, tickers in sectors.items():
                sector_data: list[dict[str, Any]] = []
                for name, sym in tickers:
                    # 經濟數據等非交易型指標無法透過 yfinance 抓取，直接略過
                    if any(
                        x in sym
                        for x in ["NFP", "CPI", "PCE", "GDP", "PMI", "HALVING", "RATE"]
                    ):
                        continue

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
