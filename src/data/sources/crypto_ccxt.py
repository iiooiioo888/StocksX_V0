# CCXT 資料來源：K 線 (OHLCV) 與資金費率
from __future__ import annotations

import logging
import time
from typing import Any

import ccxt

logger = logging.getLogger(__name__)

_TIMEFRAME_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}


_FALLBACK_ORDER = ["okx", "gate", "kucoin", "mexc"]

_exchange_cache: dict[str, tuple[ccxt.Exchange, str]] = {}


def _create_exchange(exchange_id: str) -> tuple[ccxt.Exchange, str]:
    """建立交易所實例，快取探測結果避免重複嘗試。"""
    if exchange_id in _exchange_cache:
        cached_ex, cached_id = _exchange_cache[exchange_id]
        return type(cached_ex)({"enableRateLimit": True}), cached_id

    cls = getattr(ccxt, exchange_id, None)
    if cls is None:
        raise ValueError(f"不支援的交易所: {exchange_id}")
    exchange = cls({"enableRateLimit": True})
    try:
        exchange.fetch_ohlcv("BTC/USDT:USDT", "1h", limit=1)
        _exchange_cache[exchange_id] = (exchange, exchange_id)
        return exchange, exchange_id
    except (ccxt.ExchangeNotAvailable, ccxt.RateLimitExceeded, ccxt.NetworkError) as e:
        logger.warning("交易所 %s 不可用 (%s)，嘗試回退...", exchange_id, e)
    except Exception as e:
        if "451" in str(e) or "403" in str(e) or "restricted" in str(e).lower():
            logger.warning("交易所 %s 地區受限 (%s)，嘗試回退...", exchange_id, e)
        else:
            raise

    for fb_id in _FALLBACK_ORDER:
        if fb_id == exchange_id:
            continue
        try:
            fb_cls = getattr(ccxt, fb_id, None)
            if fb_cls is None:
                continue
            fb_exchange = fb_cls({"enableRateLimit": True})
            fb_exchange.fetch_ohlcv("BTC/USDT:USDT", "1h", limit=1)
            logger.info("回退到交易所: %s", fb_id)
            _exchange_cache[exchange_id] = (fb_exchange, fb_id)
            return fb_exchange, fb_id
        except Exception:
            continue

    raise RuntimeError(f"所有交易所均不可用（主: {exchange_id}，回退: {_FALLBACK_ORDER}）")


class CcxtOhlcvSource:
    """透過 CCXT 拉取 K 線。"""

    def __init__(self, exchange_id: str) -> None:
        self._exchange, self._exchange_id = _create_exchange(exchange_id)

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        since: int | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        retries = 0
        while True:
            try:
                candles = self._exchange.fetch_ohlcv(
                    symbol, timeframe, since=since, limit=limit
                )
                break
            except (ccxt.RateLimitExceeded, ccxt.NetworkError) as e:
                retries += 1
                if retries > 5:
                    raise
                wait = 2 ** retries
                logger.warning("CCXT rate limit/network error, retry in %ds: %s", wait, e)
                time.sleep(wait)

        for c in candles:
            rows.append({
                "exchange": self._exchange_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": c[0],
                "open": c[1],
                "high": c[2],
                "low": c[3],
                "close": c[4],
                "volume": c[5],
                "filled": 0,
                "is_outlier": 0,
            })
        return rows

    def fetch_range(
        self,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
        batch_limit: int = 500,
    ) -> list[dict[str, Any]]:
        """批次拉取 [since, until] 區間的全部 K 線。"""
        tf_ms = _TIMEFRAME_MS.get(timeframe, 3_600_000)
        all_rows: list[dict[str, Any]] = []
        cursor = since - (since % tf_ms)
        while cursor < until:
            batch = self.fetch(symbol, timeframe, since=cursor, limit=batch_limit)
            if not batch:
                break
            all_rows.extend(batch)
            last_ts = batch[-1]["timestamp"]
            if last_ts <= cursor:
                break
            cursor = last_ts + tf_ms
            time.sleep(self._exchange.rateLimit / 1000 if self._exchange.rateLimit else 0.1)
        return [r for r in all_rows if r["timestamp"] <= until]


class CcxtFundingSource:
    """透過 CCXT 拉取資金費率。"""

    def __init__(self, exchange_id: str) -> None:
        self._exchange, self._exchange_id = _create_exchange(exchange_id)

    def fetch(
        self,
        symbol: str,
        since: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        retries = 0
        while True:
            try:
                rates = self._exchange.fetch_funding_rate_history(
                    symbol, since=since, limit=limit
                )
                break
            except (ccxt.RateLimitExceeded, ccxt.NetworkError) as e:
                retries += 1
                if retries > 5:
                    raise
                wait = 2 ** retries
                logger.warning("CCXT rate limit/network error, retry in %ds: %s", wait, e)
                time.sleep(wait)
            except Exception:
                return []

        rows: list[dict[str, Any]] = []
        for r in rates:
            rows.append({
                "exchange": self._exchange_id,
                "symbol": symbol,
                "timestamp": r.get("timestamp", 0),
                "funding_rate": r.get("fundingRate", 0.0),
                "open_interest": r.get("openInterest"),
                "mark_price": r.get("markPrice"),
            })
        return rows
