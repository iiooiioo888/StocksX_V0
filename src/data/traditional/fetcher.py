# 傳統市場數據抓取器（yfinance）
from __future__ import annotations

import logging
from typing import Any

from src.data.sources.yfinance_source import YfinanceOhlcvSource

logger = logging.getLogger(__name__)

_TF_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000,
}


class TraditionalDataFetcher:
    """傳統市場數據抓取器，接口與 CryptoDataFetcher 一致。"""

    def __init__(self, exchange_id: str = "yfinance") -> None:
        self._exchange_id = exchange_id
        self._source = YfinanceOhlcvSource()

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
        fill_gaps: bool = True,
        exclude_outliers: bool = False,
    ) -> list[dict[str, Any]]:
        rows = self._source.fetch_range(symbol, timeframe, since, until)

        if fill_gaps and rows:
            rows = self._fill_gaps(rows, symbol, timeframe, since, until)

        return rows

    def _fill_gaps(
        self,
        rows: list[dict[str, Any]],
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
    ) -> list[dict[str, Any]]:
        if not rows:
            return rows

        tf_ms = _TF_MS.get(timeframe, 3_600_000)
        ts_map = {r["timestamp"]: r for r in rows}
        filled: list[dict[str, Any]] = []

        cursor = since - (since % tf_ms)
        last_close = rows[0]["close"]

        while cursor <= until:
            bar = ts_map.get(cursor)
            if bar is not None:
                last_close = bar["close"]
                filled.append(bar)
            cursor += tf_ms

        return filled if filled else rows
