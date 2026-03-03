from __future__ import annotations

"""
統一外部 API 取值入口。

整合內容：
- 傳統市場 K 線：yfinance
- 加密貨幣 K 線：CCXT
- 預測市場：Polymarket Gamma API
- 宏觀經濟：FRED、TradingEconomics
- 股市數據：Alpha Vantage、Polygon.io、FMP
- 加密貨幣：CoinGecko、CoinMarketCap、Glassnode
- 券商交易：Alpaca
- 情緒數據：Fear & Greed Index、CBOE VIX

v2.0 更新：
- 加入 API 限流器（令牌桶演算法）
- 加入結構化日誌
- 加入請求計時與統計
"""

import time
from typing import Any, Dict, List, Optional

import requests

from src.config_secrets import (
    ALPHA_VANTAGE_API_KEY,
    FRED_API_KEY,
    POLYGON_API_KEY,
    COINGECKO_API_KEY,
    COINMARKETCAP_API_KEY,
    GLASSNODE_API_KEY,
    TRADING_ECONOMICS_API_KEY,
    FMP_API_KEY,
    ALPACA_API_KEY,
    ALPACA_API_SECRET,
    CBOE_API_KEY,
    require,
)
from .yfinance_source import YfinanceOhlcvSource
from .crypto_ccxt import CcxtOhlcvSource

# 引入限流器與日誌
try:
    from src.utils.rate_limiter import (
        RateLimiter,
        RateLimitExceeded,
        get_api_limiter,
        log_api_call,
    )
    from src.utils.logger import get_logger
    
    logger = get_logger('stocksx.api_hub')
    USE_RATE_LIMITER = True
except ImportError:
    USE_RATE_LIMITER = False
    logger = None


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

    # 限流檢查
    if USE_RATE_LIMITER:
        limiter, config = get_api_limiter("polymarket")
        try:
            allowed, wait_time = limiter.allow_request(
                key="polymarket",
                capacity=config["capacity"],
                refill_rate=config["refill_rate"],
                wait=False
            )
            if not allowed:
                log_api_call(
                    logger, "polymarket", "/markets",
                    params=params, status="rate_limited",
                    retry_after=wait_time
                )
                raise RateLimitExceeded(
                    f"Polymarket rate limit exceeded. Retry after {wait_time:.1f}s",
                    retry_after=wait_time
                )
        except Exception as e:
            if "rate limit" in str(e).lower():
                raise
            logger.warning(f"Rate limiter check failed: {e}")

    # 發送請求
    start_time = time.time()
    status = "success"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        markets: List[Dict[str, Any]] = []
        if isinstance(data, list):
            iterable = data
        else:
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

        response_time = (time.time() - start_time) * 1000
        log_api_call(
            logger, "polymarket", "/markets",
            params=params, response_time_ms=response_time,
            status=status, result_count=len(markets)
        )
        return markets

    except requests.exceptions.RequestException as e:
        status = "failed"
        response_time = (time.time() - start_time) * 1000
        log_api_call(
            logger, "polymarket", "/markets",
            params=params, response_time_ms=response_time,
            status=status, error=str(e)
        )
        raise


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

    # 限流檢查
    if USE_RATE_LIMITER:
        limiter, config = get_api_limiter("fred")
        allowed, wait_time = limiter.allow_request(
            key="fred",
            capacity=config["capacity"],
            refill_rate=config["refill_rate"],
            wait=False
        )
        if not allowed:
            log_api_call(
                logger, "fred", "/series/observations",
                params=params, status="rate_limited",
                retry_after=wait_time
            )
            raise RateLimitExceeded(
                f"FRED rate limit exceeded. Retry after {wait_time:.1f}s",
                retry_after=wait_time
            )

    # 發送請求
    start_time = time.time()
    status = "success"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        response_time = (time.time() - start_time) * 1000
        log_api_call(
            logger, "fred", "/series/observations",
            params=params, response_time_ms=response_time,
            status=status, series_id=series_id
        )
        return resp.json()

    except requests.exceptions.RequestException as e:
        status = "failed"
        response_time = (time.time() - start_time) * 1000
        log_api_call(
            logger, "fred", "/series/observations",
            params=params, response_time_ms=response_time,
            status=status, error=str(e)
        )
        raise


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

    # 限流檢查
    if USE_RATE_LIMITER:
        limiter, config = get_api_limiter("alpha_vantage")
        allowed, wait_time = limiter.allow_request(
            key="alpha_vantage",
            capacity=config["capacity"],
            refill_rate=config["refill_rate"],
            wait=False
        )
        if not allowed:
            log_api_call(
                logger, "alpha_vantage", function,
                params=params, status="rate_limited",
                retry_after=wait_time
            )
            raise RateLimitExceeded(
                f"Alpha Vantage rate limit exceeded. Retry after {wait_time:.1f}s",
                retry_after=wait_time
            )

    # 發送請求
    start_time = time.time()
    status = "success"
    try:
        resp = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        response_time = (time.time() - start_time) * 1000
        log_api_call(
            logger, "alpha_vantage", function,
            params=params, response_time_ms=response_time,
            status=status, symbol=symbol
        )
        return resp.json()

    except requests.exceptions.RequestException as e:
        status = "failed"
        response_time = (time.time() - start_time) * 1000
        log_api_call(
            logger, "alpha_vantage", function,
            params=params, response_time_ms=response_time,
            status=status, error=str(e)
        )
        raise


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


# ────────────────────────────── 股市：FMP (Financial Modeling Prep) ──────────────────────────────

FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"


def fetch_fmp(
    path: str,
    *,
    params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    FMP 通用 GET 封裝。
    path 例如：/profile/AAPL, /quote/AAPL, /financial-statements/income-statement/AAPL
    官方文件：https://financialmodelingprep.com/developer/docs/
    """
    api_key = require(FMP_API_KEY, "FMP_API_KEY")
    if params is None:
        params = {}
    params.setdefault("apikey", api_key)

    url = f"{FMP_BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_fmp_profile(symbol: str) -> Dict[str, Any]:
    """取得公司股票概況（公司名稱、產業、描述等）。"""
    return fetch_fmp(f"/profile/{symbol}")


def fetch_fmp_quote(symbol: str) -> Dict[str, Any]:
    """取得即時股價報價。"""
    data = fetch_fmp(f"/quote/{symbol}")
    return data[0] if isinstance(data, list) and data else data


def fetch_fmp_financials(symbol: str, statement: str = "income-statement") -> Dict[str, Any]:
    """
    取得財報數據。
    statement: "income-statement", "balance-sheet", "cash-flow-statement"
    """
    return fetch_fmp(f"/financial-statements/{statement}/{symbol}")


# ────────────────────────────── 券商：Alpaca ──────────────────────────────

ALPACA_BASE_URL = "https://api.alpaca.markets"
ALPACA_DATA_URL = "https://data.alpaca.markets"


def fetch_alpaca(
    path: str,
    *,
    params: Dict[str, Any] | None = None,
    use_data_url: bool = False,
) -> Dict[str, Any]:
    """
    Alpaca 通用 GET 封裝（需 API Key）。
    path 例如：/v2/stocks/AAPL/bars, /v2/orders
    """
    api_key = require(ALPACA_API_KEY, "ALPACA_API_KEY")
    api_secret = require(ALPACA_API_SECRET, "ALPACA_API_SECRET")
    if params is None:
        params = {}

    base_url = ALPACA_DATA_URL if use_data_url else ALPACA_BASE_URL
    url = f"{base_url}{path}"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
    }
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_alpaca_bars(
    symbol: str,
    timeframe: str = "1Day",
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
) -> Dict[str, Any]:
    """
    取得美股 K 線數據（透過 Alpaca）。
    timeframe: "1Min", "5Min", "15Min", "1Hour", "1Day"
    """
    params: Dict[str, Any] = {"timeframe": timeframe}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if limit:
        params["limit"] = limit
    return fetch_alpaca(f"/v2/stocks/{symbol}/bars", params=params, use_data_url=True)


def fetch_alpaca_account() -> Dict[str, Any]:
    """取得 Alpaca 帳戶資訊。"""
    return fetch_alpaca("/v2/account")


def fetch_alpaca_positions() -> Dict[str, Any]:
    """取得當前持倉。"""
    return fetch_alpaca("/v2/positions")


def fetch_alpaca_orders(status: str = "open") -> Dict[str, Any]:
    """取得訂單列表。"""
    return fetch_alpaca("/v2/orders", params={"status": status})


# ────────────────────────────── 情緒數據：Fear & Greed Index ──────────────────────────────

ALTERNATIVE_ME_BASE_URL = "https://api.alternative.me/fng"


def fetch_fear_greed_index(
    limit: int = 30,
) -> Dict[str, Any]:
    """
    從 Alternative.me 取得加密貨幣恐懼與貪婪指數。
    無需 API Key，直接存取公開 URL。
    官方文件：https://alternative.me/crypto/fear-and-greed-index/

    回傳範例：
    {
        "metadata": {"error": null},
        "data": [
            {"value": "50", "value_classification": "Neutral", "timestamp": "1709020800", ...},
            ...
        ]
    }
    """
    url = f"{ALTERNATIVE_ME_BASE_URL}/"
    params = {"limit": limit, "format": "json"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_current_fear_greed() -> Optional[Dict[str, Any]]:
    """取得當前恐懼與貪婪指數（單一最新值）。"""
    data = fetch_fear_greed_index(limit=1)
    if data.get("data"):
        entry = data["data"][0]
        return {
            "value": int(entry.get("value", 0)),
            "classification": entry.get("value_classification", "Unknown"),
            "timestamp": entry.get("timestamp"),
        }
    return None


# ────────────────────────────── 情緒數據：CBOE VIX ──────────────────────────────

CBOE_BASE_URL = "https://markets.cboe.com/us/options/market_statistics"


def fetch_cboe_vix() -> Optional[Dict[str, Any]]:
    """
    從 CBOE 取得 VIX 波動率指數。
    注意：CBOE API 無正式公開文件，此處使用公開網頁數據或 Alpha Vantage 替代方案。
    """
    # 方案 1：嘗試直接從 CBOE 網頁抓取（可能需要解析 HTML）
    # 方案 2：使用 Alpha Vantage 的 VIX 數據（更穩定）
    if ALPHA_VANTAGE_API_KEY:
        try:
            data = fetch_alpha_vantage(function="VIX", datatype="json")
            if "Meta Data" in data and "Time Series (VIX)" in data:
                ts = data["Time Series (VIX)"]
                latest_date = list(ts.keys())[0]
                vix_data = ts[latest_date]
                return {
                    "date": latest_date,
                    "open": float(vix_data.get("1. open", 0)),
                    "high": float(vix_data.get("2. high", 0)),
                    "low": float(vix_data.get("3. low", 0)),
                    "close": float(vix_data.get("4. close", 0)),
                }
        except Exception:
            pass
    return None


def fetch_vix_history(days: int = 30) -> List[Dict[str, Any]]:
    """
    取得 VIX 歷史數據（透過 Alpha Vantage）。
    """
    if not ALPHA_VANTAGE_API_KEY:
        return []
    try:
        data = fetch_alpha_vantage(function="VIX", datatype="json")
        if "Time Series (VIX)" not in data:
            return []
        ts = data["Time Series (VIX)"]
        result = []
        for i, (date, v) in enumerate(ts.items()):
            if i >= days:
                break
            result.append({
                "date": date,
                "open": float(v.get("1. open", 0)),
                "high": float(v.get("2. high", 0)),
                "low": float(v.get("3. low", 0)),
                "close": float(v.get("4. close", 0)),
            })
        return result
    except Exception:
        return []


# ────────────────────────────── 便捷整合函式 ──────────────────────────────

def fetch_market_sentiment() -> Dict[str, Any]:
    """
    取得綜合市場情緒指標（Fear & Greed + VIX）。
    """
    result: Dict[str, Any] = {}

    # 加密貨幣情緒
    fg = get_current_fear_greed()
    if fg:
        result["crypto_fear_greed"] = fg

    # 股市情緒（VIX）
    vix = fetch_cboe_vix()
    if vix:
        result["vix"] = vix

    return result

