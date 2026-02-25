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


class CcxtOhlcvSource:
    """透過 CCXT 拉取 K 線。"""

    def __init__(self, exchange_id: str) -> None:
        cls = getattr(ccxt, exchange_id, None)
        if cls is None:
            raise ValueError(f"不支援的交易所: {exchange_id}")
        self._exchange: ccxt.Exchange = cls({"enableRateLimit": True})
        self._exchange_id = exchange_id

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
        cursor = since
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
        cls = getattr(ccxt, exchange_id, None)
        if cls is None:
            raise ValueError(f"不支援的交易所: {exchange_id}")
        self._exchange: ccxt.Exchange = cls({"enableRateLimit": True})
        self._exchange_id = exchange_id

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
