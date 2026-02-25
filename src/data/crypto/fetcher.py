# 對外兼容層（舊 API），內部呼叫 CryptoMarketDataService
from __future__ import annotations

from typing import Any

from .db import get_storage
from .service import CryptoMarketDataService


class CryptoDataFetcher:
    """
    加密貨幣數據抓取器：對外統一 API。
    內部使用 CryptoMarketDataService 管理緩存與數據拉取。
    """

    def __init__(self, exchange_id: str, db_path: str | None = None) -> None:
        self._exchange_id = exchange_id
        storage = get_storage(db_path)
        self._service = CryptoMarketDataService(exchange_id, storage)

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        return self._service.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)

    def fetch_funding_rate(
        self,
        symbol: str,
        since: int | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        return self._service.fetch_funding_rate(symbol, since=since, limit=limit)

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
        fill_gaps: bool = True,
        exclude_outliers: bool = False,
    ) -> list[dict[str, Any]]:
        return self._service.get_ohlcv(
            symbol, timeframe, since, until,
            fill_gaps=fill_gaps,
            exclude_outliers=exclude_outliers,
        )

    def get_cached_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
        fill_gaps: bool = True,
    ) -> list[dict[str, Any]]:
        return self._service.get_cached_ohlcv(
            symbol, timeframe, since, until, fill_gaps=fill_gaps,
        )
