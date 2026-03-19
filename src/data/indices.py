# 全球市場指數
# 整合多個指數數據源

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from datetime import datetime, timezone
from typing import Any

# ════════════════════════════════════════════════════════════
# 指數配置
# ════════════════════════════════════════════════════════════

GLOBAL_INDICES = {
    # 美股指數
    "US": {
        "^GSPC": {"name": "S&P 500", "region": "美國", "type": "股票"},
        "^DJI": {"name": "道瓊工業平均", "region": "美國", "type": "股票"},
        "^IXIC": {"name": "那斯達克綜合", "region": "美國", "type": "股票"},
        "^RUT": {"name": "羅素 2000", "region": "美國", "type": "股票"},
        "^VIX": {"name": "VIX 波動率指數", "region": "美國", "type": "波動率"},
    },
    # 歐洲指數
    "EU": {
        "^FTSE": {"name": "富時 100", "region": "英國", "type": "股票"},
        "^GDAXI": {"name": "DAX", "region": "德國", "type": "股票"},
        "^FCHI": {"name": "CAC 40", "region": "法國", "type": "股票"},
        "^STOXX50E": {"name": "歐洲斯托克 50", "region": "歐洲", "type": "股票"},
    },
    # 亞洲指數
    "ASIA": {
        "^N225": {"name": "日經 225", "region": "日本", "type": "股票"},
        "^HSI": {"name": "恆生指數", "region": "香港", "type": "股票"},
        "^SSEC": {"name": "上證綜合", "region": "中國", "type": "股票"},
        "^KS11": {"name": "韓國綜合", "region": "韓國", "type": "股票"},
        "^TWII": {"name": "台灣加權", "region": "台灣", "type": "股票"},
    },
    # 其他指數
    "OTHER": {
        "^AXJO": {"name": "澳股綜合", "region": "澳洲", "type": "股票"},
        "^BSESN": {"name": "印度 Sensex", "region": "印度", "type": "股票"},
        "^BVSP": {"name": "巴西 BOVESPA", "region": "巴西", "type": "股票"},
    },
}

# 商品指數
COMMODITY_INDICES = {
    "GC=F": {"name": "黃金", "category": "貴金屬", "unit": "USD/oz"},
    "SI=F": {"name": "白銀", "category": "貴金屬", "unit": "USD/oz"},
    "CL=F": {"name": "WTI 原油", "category": "能源", "unit": "USD/bbl"},
    "BZ=F": {"name": "Brent 原油", "category": "能源", "unit": "USD/bbl"},
    "NG=F": {"name": "天然氣", "category": "能源", "unit": "USD/MMBtu"},
    "HG=F": {"name": "銅", "category": "金屬", "unit": "USD/lb"},
    "ZC=F": {"name": "玉米", "category": "農產品", "unit": "USD/bu"},
    "ZW=F": {"name": "小麥", "category": "農產品", "unit": "USD/bu"},
    "ZS=F": {"name": "黃豆", "category": "農產品", "unit": "USD/bu"},
}

# 債券指數
BOND_INDICES = {
    "^TNX": {"name": "10 年期國債殖利率", "region": "美國", "unit": "%"},
    "^TYX": {"name": "30 年期國債殖利率", "region": "美國", "unit": "%"},
    "^FVX": {"name": "5 年期國債殖利率", "region": "美國", "unit": "%"},
    "^IRX": {"name": "3 個月國庫券", "region": "美國", "unit": "%"},
    "US10Y": {"name": "美國 10 年期公債", "region": "美國", "unit": "%"},
}

# 匯率指數
CURRENCY_INDICES = {
    "DX-Y.NYB": {"name": "美元指數", "base": "USD", "type": "指數"},
    "EURUSD=X": {"name": "歐元/美元", "base": "EUR", "quote": "USD", "type": "匯率"},
    "GBPUSD=X": {"name": "英鎊/美元", "base": "GBP", "quote": "USD", "type": "匯率"},
    "USDJPY=X": {"name": "美元/日圓", "base": "USD", "quote": "JPY", "type": "匯率"},
    "USDCNY=X": {"name": "美元/人民幣", "base": "USD", "quote": "CNY", "type": "匯率"},
    "USDTWD=X": {"name": "美元/台幣", "base": "USD", "quote": "TWD", "type": "匯率"},
    "BTCUSD=X": {"name": "比特幣/美元", "base": "BTC", "quote": "USD", "type": "加密"},
    "ETHUSD=X": {"name": "以太幣/美元", "base": "ETH", "quote": "USD", "type": "加密"},
}


# ════════════════════════════════════════════════════════════
# 指數數據獲取
# ════════════════════════════════════════════════════════════


def get_index_quote(symbol: str) -> dict[str, Any] | None:
    """
    取得指數報價（使用 Yahoo Finance）

    Args:
        symbol: 指數代碼

    Returns:
        {
            "symbol": str,
            "name": str,
            "price": float,
            "change": float,
            "change_pct": float,
            "open": float,
            "high": float,
            "low": float,
            "prev_close": float,
            "volume": int,
            "timestamp": int
        }
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.fast_info

        # 取得即時數據
        data = {
            "symbol": symbol,
            "name": GLOBAL_INDICES.get("US", {}).get(symbol, {}).get("name", symbol),
            "price": info.get("last_price", 0),
            "change": info.get("regular_market_change", 0),
            "change_pct": info.get("regular_market_change_percent", 0),
            "open": info.get("open", 0),
            "high": info.get("day_high", 0),
            "low": info.get("day_low", 0),
            "prev_close": info.get("previous_close", 0),
            "volume": info.get("volume", 0),
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        }

        return data
    except Exception as e:
        logger.error(f"取得指數報價失敗 {symbol}: {e}")
        return None


def get_indices_batch(symbols: list[str]) -> dict[str, dict]:
    """
    批量取得指數報價

    Args:
        symbols: 指數代碼列表

    Returns:
        {symbol: data}
    """
    result = {}
    for symbol in symbols:
        data = get_index_quote(symbol)
        if data:
            result[symbol] = data
    return result


def get_market_status() -> dict[str, bool]:
    """
    取得全球市場開收盤狀態

    Returns:
        {
            "US": bool,  # 美國市場
            "EU": bool,  # 歐洲市場
            "ASIA": bool,  # 亞洲市場
        }
    """
    from datetime import datetime

    now_utc = datetime.now(timezone.utc)

    # 簡化判斷（實際應考慮假日）
    market_hours = {
        "ASIA": (0, 9),  # UTC 0:00-9:00
        "EU": (7, 16),  # UTC 7:00-16:00
        "US": (13, 22),  # UTC 13:00-22:00
    }

    status = {}
    for region, (open_hour, close_hour) in market_hours.items():
        status[region] = open_hour <= now_utc.hour < close_hour

    return status


def get_global_market_overview() -> dict[str, Any]:
    """
    取得全球市場概覽

    Returns:
        {
            "market_status": Dict,
            "major_indices": Dict,
            "commodities": Dict,
            "currencies": Dict,
            "bonds": Dict
        }
    """
    # 市場狀態
    market_status = get_market_status()

    # 主要指數
    major_indices_symbols = ["^GSPC", "^DJI", "^IXIC", "^VIX", "^N225", "^HSI", "^TWII"]
    major_indices = get_indices_batch(major_indices_symbols)

    # 商品
    commodity_symbols = ["GC=F", "CL=F", "NG=F"]
    commodities = get_indices_batch(commodity_symbols)

    # 匯率
    currency_symbols = ["DX-Y.NYB", "EURUSD=X", "USDJPY=X"]
    currencies = get_indices_batch(currency_symbols)

    # 債券
    bond_symbols = ["^TNX", "^TYX"]
    bonds = get_indices_batch(bond_symbols)

    return {
        "market_status": market_status,
        "major_indices": major_indices,
        "commodities": commodities,
        "currencies": currencies,
        "bonds": bonds,
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
    }


# ════════════════════════════════════════════════════════════
# 經濟日曆
# ════════════════════════════════════════════════════════════


def get_economic_calendar(start_date: str = None, end_date: str = None, country: str = "US") -> list[dict[str, Any]]:
    """
    取得經濟日曆（使用 TradingEconomics 或其他 API）

    Args:
        start_date: 開始日期 YYYY-MM-DD
        end_date: 結束日期 YYYY-MM-DD
        country: 國家代碼（US, EU, JP, CN, TW 等）

    Returns:
        [
            {
                "date": str,
                "time": str,
                "country": str,
                "event": str,
                "importance": str,  # High, Medium, Low
                "actual": str,
                "forecast": str,
                "previous": str
            }
        ]
    """
    # 模擬數據（實際應連接 API）
    from datetime import datetime

    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")

    events = [
        {
            "date": start_date,
            "time": "08:30",
            "country": "US",
            "event": "非農就業人口",
            "importance": "High",
            "actual": "+250K",
            "forecast": "+200K",
            "previous": "+180K",
        },
        {
            "date": start_date,
            "time": "08:30",
            "country": "US",
            "event": "失業率",
            "importance": "High",
            "actual": "3.7%",
            "forecast": "3.8%",
            "previous": "3.8%",
        },
        {
            "date": start_date,
            "time": "14:00",
            "country": "US",
            "event": "FOMC 利率決策",
            "importance": "High",
            "actual": "5.50%",
            "forecast": "5.50%",
            "previous": "5.50%",
        },
        {
            "date": start_date,
            "time": "09:45",
            "country": "US",
            "event": "Markit 製造業 PMI",
            "importance": "Medium",
            "actual": "50.5",
            "forecast": "50.0",
            "previous": "49.8",
        },
        {
            "date": start_date,
            "time": "10:00",
            "country": "US",
            "event": "ISM 製造業 PMI",
            "importance": "High",
            "actual": "49.5",
            "forecast": "49.0",
            "previous": "48.8",
        },
    ]

    return events


# ════════════════════════════════════════════════════════════
# 市場情緒指標
# ════════════════════════════════════════════════════════════


def get_market_sentiment() -> dict[str, Any]:
    """
    取得市場情緒指標

    Returns:
        {
            "fear_greed": Dict,  # 恐懼貪婪指數
            "vix": Dict,  # VIX 波動率
            "put_call_ratio": Dict,  # Put/Call 比率
            "advance_decline": Dict,  # 漲跌家數
            "new_highs_lows": Dict  # 新高/新低
        }
    """
    from src.data.sources.api_hub import fetch_cboe_vix, get_current_fear_greed

    # 恐懼貪婪指數
    fg = get_current_fear_greed()

    # VIX
    vix = fetch_cboe_vix()

    # 模擬其他指標
    sentiment = {
        "fear_greed": fg,
        "vix": vix,
        "put_call_ratio": {
            "value": 0.65,
            "interpretation": "Neutral",  # >1 Bearish, <0.7 Bullish
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        },
        "advance_decline": {
            "advancing": 1850,
            "declining": 1200,
            "unchanged": 150,
            "ratio": 1.54,
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        },
        "new_highs_lows": {
            "new_highs": 125,
            "new_lows": 45,
            "ratio": 2.78,
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        },
    }

    return sentiment
