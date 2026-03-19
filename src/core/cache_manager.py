"""
CacheManager — 統一快取管理

取代散落在 DataService.price_cache / kline_cache / depth_cache 的碎片化快取。
支持多層快取（內存 → Redis）、命名空間隔離、統計監控。

架構：
  CacheManager
    ├── namespace("price")     → L1 DictCache, TTL=1s
    ├── namespace("kline")     → L1 DictCache + L2 RedisCache, TTL=300s
    └── namespace("orderbook") → L1 DictCache, TTL=1s
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .provider import CacheBackend, DictCache, RedisCache

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """快取統計."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "evictions": self.evictions,
            "hit_rate": round(self.hit_rate, 4),
        }


class CacheNamespace:
    """
    命名空間快取：帶前綴、TTL、統計。
    內部委託給 CacheBackend。
    """

    def __init__(
        self,
        name: str,
        backend: CacheBackend,
        default_ttl: int = 60,
    ) -> None:
        self.name = name
        self._backend = backend
        self._default_ttl = default_ttl
        self.stats = CacheStats()

    def _key(self, key: str) -> str:
        return f"{self.name}:{key}"

    def get(self, key: str) -> Any | None:
        val = self._backend.get(self._key(key))
        if val is not None:
            self.stats.hits += 1
        else:
            self.stats.misses += 1
        return val

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._backend.set(self._key(key), value, ttl=ttl or self._default_ttl)
        self.stats.sets += 1

    def delete(self, key: str) -> None:
        self._backend.delete(self._key(key))
        self.stats.evictions += 1

    def get_or_set(self, key: str, factory: Any, ttl: int | None = None) -> Any:
        """Cache-aside 模式：有就返回，沒有就計算後存入."""
        val = self.get(key)
        if val is not None:
            return val
        val = factory() if callable(factory) else factory
        self.set(key, val, ttl=ttl)
        return val

    def invalidate(self) -> None:
        """清空此命名空間（僅 DictCache 支持精確清空）."""
        if isinstance(self._backend, DictCache):
            prefix = f"{self.name}:"
            keys_to_delete = [k for k in list(self._backend._store.keys()) if k.startswith(prefix)]
            for k in keys_to_delete:
                self._backend._store.pop(k, None)
                self.stats.evictions += 1


class CacheManager:
    """
    統一快取管理器。

    用法：
        cm = CacheManager(redis_url="redis://...")
        prices = cm.price.get("BTC/USDT")
        klines = cm.kline.get_or_set("BTC/USDT:1h", lambda: fetch_klines(...))
    """

    def __init__(self, redis_url: str | None = None) -> None:
        # L1: 內存快取（總是可用）
        self._l1 = DictCache()
        # L2: Redis（可選）
        self._l2: CacheBackend | None = None
        if redis_url:
            self._l2 = RedisCache(redis_url)

        # 預設命名空間
        self.price = CacheNamespace("price", self._l1, default_ttl=1)
        self.kline = CacheNamespace("kline", self._l1, default_ttl=300)
        self.orderbook = CacheNamespace("orderbook", self._l1, default_ttl=1)
        self.user = CacheNamespace("user", self._l1, default_ttl=30)
        self.api = CacheNamespace("api", self._l1, default_ttl=300)

        self._namespaces: dict[str, CacheNamespace] = {
            "price": self.price,
            "kline": self.kline,
            "orderbook": self.orderbook,
            "user": self.user,
            "api": self.api,
        }

    def namespace(self, name: str, default_ttl: int = 60) -> CacheNamespace:
        """取得或建立命名空間."""
        if name not in self._namespaces:
            ns = CacheNamespace(name, self._l1, default_ttl=default_ttl)
            self._namespaces[name] = ns
        return self._namespaces[name]

    def all_stats(self) -> dict[str, dict[str, Any]]:
        """所有命名空間的統計."""
        return {name: ns.stats.to_dict() for name, ns in self._namespaces.items()}

    def clear_all(self) -> None:
        """清空所有快取."""
        for ns in self._namespaces.values():
            ns.invalidate()
        logger.info("All caches cleared")


# ─── 全域實例 ───

_cache_manager: CacheManager | None = None


def get_cache_manager(redis_url: str | None = None) -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(redis_url=redis_url)
    return _cache_manager
