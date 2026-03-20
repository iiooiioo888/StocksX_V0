"""
Market Data Provider — 統一數據抽象層

取代 CryptoDataFetcher + DataService + CryptoMarketDataService 三個重疊層。
通過 Protocol 定義介面，每個 Provider 專注一個數據源。

架構：
  MarketProvider (Protocol)
    ├── CCXTProvider      → 加密貨幣 (11 交易所)
    ├── YahooProvider     → 美股/台股/ETF/期貨
    ├── CoinGeckoProvider → 市值、情緒、Fear&Greed
    └── CompositeProvider → 自動路由到正確的 Provider
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


# ════════════════════════════════════════════════════════════
# 數據結構 (Immutable Value Objects)
# ════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class OHLCV:
    """K 線數據."""

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> OHLCV:
        return cls(
            timestamp=int(d["timestamp"]),
            open=float(d["open"]),
            high=float(d["high"]),
            low=float(d["low"]),
            close=float(d["close"]),
            volume=float(d.get("volume", 0)),
        )


@dataclass(frozen=True, slots=True)
class Ticker:
    """即時行情."""

    symbol: str
    price: float
    change_pct: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    volume_24h: float = 0.0
    timestamp: int = 0


@dataclass(frozen=True, slots=True)
class OrderBook:
    """訂單簿."""

    symbol: str
    bids: list[list[float]] = field(default_factory=list)
    asks: list[list[float]] = field(default_factory=list)
    timestamp: int = 0


# ════════════════════════════════════════════════════════════
# 快取介面
# ════════════════════════════════════════════════════════════


@runtime_checkable
class CacheBackend(Protocol):
    """快取後端介面，可替換為 Redis / 內存 / 磁碟."""

    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl: int = 60) -> None: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...


class DictCache:
    """內存快取（開發用，不跨進程）."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        if key in self._store:
            val, expires = self._store[key]
            if time.time() < expires:
                return val
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        self._store[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None


class RedisCache:
    """Redis 快取（生產用，跨進程共享）."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        try:
            import redis as redis_lib

            self._client = redis_lib.from_url(redis_url, decode_responses=True)
            self._available = True
        except Exception:
            self._client = None
            self._available = False

    def get(self, key: str) -> Any | None:
        if not self._available:
            return None
        try:
            val = self._client.get(key)  # type: ignore[union-attr]
            if val is not None:
                import json

                return json.loads(val)
        except Exception:
            pass
        return None

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        if not self._available:
            return
        try:
            import json

            self._client.setex(key, ttl, json.dumps(value))  # type: ignore[union-attr]
        except Exception:
            pass

    def delete(self, key: str) -> None:
        if not self._available:
            return
        try:
            self._client.delete(key)  # type: ignore[union-attr]
        except Exception:
            pass

    def exists(self, key: str) -> bool:
        if not self._available:
            return False
        try:
            return bool(self._client.exists(key))  # type: ignore[union-attr]
        except Exception:
            return False


def make_cache(redis_url: str | None = None) -> CacheBackend:
    """工廠函數：有 Redis 就用 Redis，否則用 Dict."""
    if redis_url:
        cache = RedisCache(redis_url)
        if cache._available:
            return cache
    return DictCache()


# ════════════════════════════════════════════════════════════
# Provider 介面
# ════════════════════════════════════════════════════════════


@runtime_checkable
class MarketProvider(Protocol):
    """市場數據提供者."""

    @property
    def name(self) -> str:
        """Provider 名稱."""
        ...

    def supports(self, symbol: str) -> bool:
        """是否支持此交易對."""
        ...

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int | None = None,
        limit: int = 500,
    ) -> list[OHLCV]:
        """取得 K 線數據."""
        ...

    def fetch_ticker(self, symbol: str) -> Ticker | None:
        """取得即時行情."""
        ...

    def fetch_orderbook(self, symbol: str, limit: int = 20) -> OrderBook | None:
        """取得訂單簿."""
        ...
