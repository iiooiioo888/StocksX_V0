# 傳統市場數據抓取器（yfinance + SQLite 快取）
from __future__ import annotations

import logging
from typing import Any

from src.data.sources.yfinance_source import YfinanceOhlcvSource
from src.data.storage.sqlite_storage import SQLiteMarketDataStorage

logger = logging.getLogger(__name__)

_TF_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000,
}

_DB_PATH = "cache/traditional_cache.sqlite"


class TraditionalDataFetcher:
    """傳統市場數據抓取器，接口與 CryptoDataFetcher 一致，含 SQLite 快取。"""

    def __init__(self, exchange_id: str = "yfinance") -> None:
        self._exchange_id = exchange_id
        self._source = YfinanceOhlcvSource()
        self._storage = SQLiteMarketDataStorage(_DB_PATH)

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
        fill_gaps: bool = True,
        exclude_outliers: bool = False,
    ) -> list[dict[str, Any]]:
        tf_ms = _TF_MS.get(timeframe, 86_400_000)
        aligned_since = since - (since % tf_ms)

        cached = self._storage.load_ohlcv("yfinance", symbol, timeframe, aligned_since, until)
        expected = max(1, (until - aligned_since) // tf_ms)

        if len(cached) < expected * 0.3:
            logger.info("Traditional cache miss, fetching: %s %s", symbol, timeframe)
            fresh = self._source.fetch_range(symbol, timeframe, since, until)
            if fresh:
                self._storage.save_ohlcv(fresh)
                cached = self._storage.load_ohlcv("yfinance", symbol, timeframe, aligned_since, until)

        return cached if cached else self._source.fetch_range(symbol, timeframe, since, until)
