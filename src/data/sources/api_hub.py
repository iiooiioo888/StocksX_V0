from __future__ import annotations

"""
統一外部 API 取值入口。

目前整合：
- 傳統市場 K 線：yfinance
- 加密貨幣 K 線：CCXT
- 預測市場：Polymarket Gamma API
"""

from typing import Any, Dict, List

import requests

from src.config_secrets import (
    ALPHA_VANTAGE_API_KEY,
    FRED_API_KEY,
    POLYGON_API_KEY,
    COINGECKO_API_KEY,
    COINMARKETCAP_API_KEY,
    GLASSNODE_API_KEY,
    TRADING_ECONOMICS_API_KEY,
    require,
)
from .yfinance_source import YfinanceOhlcvSource
from .crypto_ccxt import CcxtOhlcvSource


def fetch_traditional_ohlcv(
    symbol: str,
    timeframe: str,
    since: int,
    until: int,
) -> List[Dict[str, Any]]:
    """
    透過 yfinance 取得傳統市場 K 線。

    回傳結構與內部統一格式一致：
    [{exchange, symbol, timeframe, timestamp, open, high, low, close, volume, ...}, ...]
    """
    source = YfinanceOhlcvSource()
    return source.fetch_range(symbol, timeframe, since, until)


def fetch_crypto_ohlcv(
    exchange_id: str,
    symbol: str,
    timeframe: str,
    since: int,
    until: int,
    batch_limit: int = 500,
) -> List[Dict[str, Any]]:
    """
    透過 CCXT 取得加密貨幣 K 線，內建地區限制/頻率限制回退機制。

    回傳結構與內部統一格式一致：
    [{exchange, symbol, timeframe, timestamp, open, high, low, close, volume, ...}, ...]
    """
    source = CcxtOhlcvSource(exchange_id)
    return source.fetch_range(symbol, timeframe, since, until, batch_limit=batch_limit)


POLY_BASE_URL = "https://gamma-api.polymarket.com"


def fetch_polymarket_markets(
    query: str = "",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    從 Polymarket Gamma API 抓取市場列表。

    注意：Gamma API 無正式文件，結構可能變動，本函式僅作為示意與輕量封裝。
    """
    url = f"{POLY_BASE_URL}/markets"
    params: Dict[str, Any] = {"limit": limit}
    if query:
        params["search"] = query

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    markets: List[Dict[str, Any]] = []
    if isinstance(data, list):
        iterable = data
    else:
        # 部分社群範例會回傳 {"markets": [...]}，做個保守處理
        iterable = data.get("markets", []) if isinstance(data, dict) else []

    for m in iterable:
        if not isinstance(m, dict):
            continue
        markets.append(
            {
                "id": m.get("id"),
                "title": m.get("title"),
                "yes_bid": m.get("yesBid"),
                "no_bid": m.get("noBid"),
                "volume": m.get("volume"),
                "status": m.get("status"),
            }
        )

    return markets


# ───────────────────────────────── 宏觀經濟數據：FRED ─────────────────────────────────

FRED_BASE_URL = "https://api.stlouisfed.org/fred"


def fetch_fred_series(
    series_id: str,
    *,
    observation_start: str | None = None,
    observation_end: str | None = None,
    units: str | None = None,
) -> Dict[str, Any]:
    """
    從 FRED 取得單一時間序列資料（僅示意常用參數）。

    官方文件：https://fred.stlouisfed.org/docs/api/fred/
    """
    api_key = require(FRED_API_KEY, "FRED_API_KEY")
    url = f"{FRED_BASE_URL}/series/observations"
    params: Dict[str, Any] = {
        "api_key": api_key,
        "series_id": series_id,
        "file_type": "json",
    }
    if observation_start:
        params["observation_start"] = observation_start
    if observation_end:
        params["observation_end"] = observation_end
    if units:
        params["units"] = units

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ───────────────────────────── 股市 / 外匯：Alpha Vantage ─────────────────────────────

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


def fetch_alpha_vantage(
    function: str,
    *,
    symbol: str | None = None,
    **extra: Any,
) -> Dict[str, Any]:
    """
    Alpha Vantage 通用呼叫封裝。

    常見 function 如：TIME_SERIES_DAILY, FX_DAILY, DIGITAL_CURRENCY_DAILY 等。
    官方文件：https://www.alphavantage.co/documentation/
    """
    api_key = require(ALPHA_VANTAGE_API_KEY, "ALPHA_VANTAGE_API_KEY")
    params: Dict[str, Any] = {"function": function, "apikey": api_key}
    if symbol:
        params["symbol"] = symbol
    params.update(extra)

    resp = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ─────────────────────────────── 股市：Polygon.io ───────────────────────────────

POLYGON_BASE_URL = "https://api.polygon.io"


def fetch_polygon(
    path: str,
    *,
    params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Polygon.io 通用 GET 封裝。
    path 例如：/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-31
    """
    api_key = require(POLYGON_API_KEY, "POLYGON_API_KEY")
    if params is None:
        params = {}
    params.setdefault("apiKey", api_key)

    url = f"{POLYGON_BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ────────────────────────────── 加密貨幣：CoinGecko ──────────────────────────────

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"


def fetch_coingecko(
    path: str,
    *,
    params: Dict[str, Any] | None = None,
) -> Any:
    """
    CoinGecko 通用 GET 封裝。
    path 例如：/simple/price?ids=bitcoin&vs_currencies=usd
    """
    if params is None:
        params = {}

    # 如果你有 Pro API Key，可改成放在 header 或 query
    if COINGECKO_API_KEY:
        params.setdefault("x_cg_pro_api_key", COINGECKO_API_KEY)

    url = f"{COINGECKO_BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ───────────────────────────── 加密貨幣：CoinMarketCap ─────────────────────────────

COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


def fetch_coinmarketcap(
    path: str,
    *,
    params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    CoinMarketCap 通用 GET 封裝。
    path 例如：/cryptocurrency/listings/latest
    """
    api_key = require(COINMARKETCAP_API_KEY, "COINMARKETCAP_API_KEY")
    if params is None:
        params = {}

    url = f"{COINMARKETCAP_BASE_URL}{path}"
    headers = {"X-CMC_PRO_API_KEY": api_key}
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ────────────────────────────── 鏈上數據：Glassnode ──────────────────────────────

GLASSNODE_BASE_URL = "https://api.glassnode.com/v1"


def fetch_glassnode(
    path: str,
    *,
    params: Dict[str, Any] | None = None,
) -> Any:
    """
    Glassnode 通用 GET 封裝。
    path 例如：/metrics/indicators/mvrv_z_score
    """
    api_key = require(GLASSNODE_API_KEY, "GLASSNODE_API_KEY")
    if params is None:
        params = {}
    params.setdefault("api_key", api_key)

    url = f"{GLASSNODE_BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ───────────────────────────── 宏觀：TradingEconomics ─────────────────────────────

TRADING_ECONOMICS_BASE_URL = "https://api.tradingeconomics.com"


def fetch_trading_economics(
    path: str,
    *,
    params: Dict[str, Any] | None = None,
) -> Any:
    """
    TradingEconomics 通用 GET 封裝。
    path 例如：/historical/country/united%20states/indicator/inflation%20rate
    """
    api_key = require(TRADING_ECONOMICS_API_KEY, "TRADING_ECONOMICS_API_KEY")
    if params is None:
        params = {}
    params.setdefault("client", api_key)

    url = f"{TRADING_ECONOMICS_BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

