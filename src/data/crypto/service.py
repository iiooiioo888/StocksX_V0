# CryptoMarketDataService：緩存 + 缺口補齊 + 插針標記
from __future__ import annotations

import logging
import statistics
from typing import Any

from src.data.sources.crypto_ccxt import CcxtFundingSource, CcxtOhlcvSource
from src.data.storage.sqlite_storage import SQLiteMarketDataStorage

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

_OUTLIER_THRESHOLD = 0.05  # 偏離均價 5% 標記插針


class CryptoMarketDataService:
    """組合服務：緩存優先 + 自動補齊缺口 + 插針標記。"""

    def __init__(self, exchange_id: str, storage: SQLiteMarketDataStorage) -> None:
        self._storage = storage
        self._ohlcv_source = CcxtOhlcvSource(exchange_id)
        self._funding_source = CcxtFundingSource(exchange_id)
        self._exchange_id = self._ohlcv_source._exchange_id

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        rows = self._ohlcv_source.fetch(symbol, timeframe, since=since, limit=limit)
        self._mark_outliers(rows)
        self._storage.save_ohlcv(rows)
        return rows

    def fetch_funding_rate(
        self,
        symbol: str,
        since: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        rows = self._funding_source.fetch(symbol, since=since, limit=limit)
        self._storage.save_funding_rates(rows)
        return rows

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
        fill_gaps: bool = True,
        exclude_outliers: bool = False,
    ) -> list[dict[str, Any]]:
        tf_ms = _TIMEFRAME_MS.get(timeframe, 3_600_000)
        aligned_since = since - (since % tf_ms)
        cached = self._storage.load_ohlcv(self._exchange_id, symbol, timeframe, aligned_since, until)

        expected_bars = max(1, (until - aligned_since) // tf_ms)

        if len(cached) < expected_bars * 0.5:
            logger.info("Cache miss or insufficient, fetching from exchange: %s %s %s", symbol, timeframe, self._exchange_id)
            fresh = self._ohlcv_source.fetch_range(symbol, timeframe, since, until)
            self._mark_outliers(fresh)
            self._storage.save_ohlcv(fresh)
            cached = self._storage.load_ohlcv(self._exchange_id, symbol, timeframe, since, until)

        if exclude_outliers:
            cached = [r for r in cached if not r.get("is_outlier")]

        if fill_gaps:
            cached = self._fill_gaps(cached, symbol, timeframe, since, until, tf_ms)

        return cached

    def get_cached_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
        fill_gaps: bool = True,
    ) -> list[dict[str, Any]]:
        cached = self._storage.load_ohlcv(self._exchange_id, symbol, timeframe, since, until)
        if fill_gaps:
            tf_ms = _TIMEFRAME_MS.get(timeframe, 3_600_000)
            cached = self._fill_gaps(cached, symbol, timeframe, since, until, tf_ms)
        return cached

    def _fill_gaps(
        self,
        rows: list[dict[str, Any]],
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
        tf_ms: int,
    ) -> list[dict[str, Any]]:
        """前向填充 (FFill) 缺失 K 線。O(n) 實作，cursor 對齊時間格線。"""
        if not rows:
            return rows

        ts_map = {r["timestamp"]: r for r in rows}
        filled: list[dict[str, Any]] = []

        cursor = since - (since % tf_ms)
        last_close = rows[0]["close"]

        while cursor <= until:
            bar = ts_map.get(cursor)
            if bar is not None:
                last_close = bar["close"]
                filled.append(bar)
            else:
                filled.append({
                    "exchange": self._exchange_id,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": cursor,
                    "open": last_close,
                    "high": last_close,
                    "low": last_close,
                    "close": last_close,
                    "volume": 0.0,
                    "filled": 1,
                    "is_outlier": 0,
                })
            cursor += tf_ms

        return filled

    def _mark_outliers(self, rows: list[dict[str, Any]]) -> None:
        """插針標記：偏離均價超過 5% 的 K 線。"""
        if len(rows) < 5:
            return
        closes = [r["close"] for r in rows if r["close"]]
        if not closes:
            return
        try:
            mean_price = statistics.mean(closes)
        except statistics.StatisticsError:
            return
        for r in rows:
            if r["close"] and mean_price > 0:
                deviation = abs(r["close"] - mean_price) / mean_price
                if deviation > _OUTLIER_THRESHOLD:
                    r["is_outlier"] = 1
