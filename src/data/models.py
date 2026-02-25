# 領域模型：OhlcvBar, FundingRateRecord
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OhlcvBar:
    """一根 K 線。"""
    exchange: str
    symbol: str
    timeframe: str
    timestamp: int          # UTC 毫秒
    open: float
    high: float
    low: float
    close: float
    volume: float
    filled: int = 0         # 1 = FFill 補值
    is_outlier: int = 0     # 1 = 插針標記

    def to_dict(self) -> dict[str, Any]:
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "filled": self.filled,
            "is_outlier": self.is_outlier,
        }


@dataclass
class FundingRateRecord:
    """資金費率記錄。"""
    exchange: str
    symbol: str
    timestamp: int          # UTC 毫秒
    funding_rate: float
    open_interest: float | None = None
    mark_price: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "funding_rate": self.funding_rate,
            "open_interest": self.open_interest,
            "mark_price": self.mark_price,
        }
