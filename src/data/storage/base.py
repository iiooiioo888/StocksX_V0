# MarketDataStorage 介面（Protocol）
from __future__ import annotations

from typing import Any, Protocol


class MarketDataStorage(Protocol):
    """市場數據存儲介面。"""

    def save_ohlcv(self, rows: list[dict[str, Any]]) -> None: ...

    def load_ohlcv(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        since: int,
        until: int,
    ) -> list[dict[str, Any]]: ...

    def save_funding_rates(self, rows: list[dict[str, Any]]) -> None: ...

    def load_funding_rates(
        self,
        exchange: str,
        symbol: str,
        since: int,
        until: int,
    ) -> list[dict[str, Any]]: ...
