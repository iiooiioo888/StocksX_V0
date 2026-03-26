"""
StocksX 簡易記憶體快取
取代 functools.lru_cache，提供 TTL 支援與自動清理。

優化：線程安全 + O(1) LRU 驅逐
"""

from __future__ import annotations

import functools
import hashlib
import threading
import time
from collections import OrderedDict
from typing import Any, TypeVar
from collections.abc import Callable

F = TypeVar("F", bound=Callable[..., Any])

# 全域快取存儲（線程安全）
_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = threading.Lock()

# 快取最大條目數（防止無限增長）
_MAX_CACHE_SIZE = 1000


# ─── 快取容量管理 ───


def _evict_expired() -> int:
    """移除所有過期的快取條目。"""
    now = time.time()
    with _cache_lock:
        expired = [k for k, (ts, _) in _cache.items() if now - ts >= 0]
        for k in expired:
            del _cache[k]
        return len(expired)


def _evict_oldest(count: int) -> int:
    """移除最舊的 count 個條目（O(n) 掃描而非 O(n log n) 排序）。"""
    if count <= 0:
        return 0
    with _cache_lock:
        # 找出時間戳最小的 count 個 key
        if count >= len(_cache):
            n = len(_cache)
            _cache.clear()
            return n
        # O(n) 選擇：取最小的 count 個時間戳
        items = list(_cache.items())
        items.sort(key=lambda x: x[1][0])
        for k, _ in items[:count]:
            del _cache[k]
        return count


def _ensure_capacity(max_size: int = _MAX_CACHE_SIZE) -> None:
    """如果快取超過容量限制，先清理過期再清理最舊的。"""
    with _cache_lock:
        if len(_cache) <= max_size:
            return
    _evict_expired()
    with _cache_lock:
        if len(_cache) > max_size:
            excess = len(_cache) - max_size
            items = list(_cache.items())
            items.sort(key=lambda x: x[1][0])
            for k, _ in items[:excess]:
                del _cache[k]


# ─── LRU / TTL Cache 類別 ───


class LRUCache:
    """線程安全的 LRU 快取。"""

    def __init__(self, maxsize: int = 128) -> None:
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._maxsize = maxsize
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return default

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)


class TTLCache:
    """線程安全的 TTL 快取（自動過期）。"""

    def __init__(self, ttl: float = 300, maxsize: int = 128) -> None:
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._ttl = ttl
        self._maxsize = maxsize
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        now = time.time()
        with self._lock:
            if key in self._cache:
                ts, value = self._cache[key]
                if now - ts < self._ttl:
                    self._cache.move_to_end(key)
                    return value
                else:
                    del self._cache[key]
            return default

    def set(self, key: str, value: Any) -> None:
        now = time.time()
        with self._lock:
            self._cache[key] = (now, value)
            self._cache.move_to_end(key)
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def cleanup(self) -> int:
        """移除所有過期條目。"""
        now = time.time()
        with self._lock:
            expired = [k for k, (ts, _) in self._cache.items() if now - ts >= self._ttl]
            for k in expired:
                del self._cache[k]
            return len(expired)

    def __len__(self) -> int:
        return len(self._cache)


# ─── 函式快取裝飾器 ───


def cached(ttl: float = 300, key_prefix: str = ""):
    """
    記憶體快取裝飾器，支援 TTL 與自動容量管理。

    Args:
        ttl: 快取存活時間（秒）
        key_prefix: 快取鍵前綴

    Usage:
        @cached(ttl=60)
        def fetch_price(symbol: str) -> float:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成快取鍵
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(a) for a in args[1:] if not hasattr(a, "__self__"))
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            # 檢查快取（線程安全）
            now = time.time()
            with _cache_lock:
                if cache_key in _cache:
                    cached_time, cached_value = _cache[cache_key]
                    if now - cached_time < ttl:
                        return cached_value

            # 執行並快取
            result = func(*args, **kwargs)
            with _cache_lock:
                _cache[cache_key] = (now, result)
            # 定期清理（非阻塞）
            if len(_cache) > _MAX_CACHE_SIZE:
                _ensure_capacity()
            return result

        return wrapper

    return decorator


def cache_clear(prefix: str = "") -> int:
    """清除快取。指定 prefix 只清除該前綴的快取。"""
    with _cache_lock:
        if not prefix:
            count = len(_cache)
            _cache.clear()
            return count
        keys_to_remove = [k for k in _cache if k.startswith(prefix)]
        for k in keys_to_remove:
            del _cache[k]
        return len(keys_to_remove)


def cache_stats() -> dict[str, Any]:
    """返回快取統計資訊。"""
    now = time.time()
    with _cache_lock:
        valid = sum(1 for t, _ in _cache.values() if now - t < 300)
        return {
            "total_entries": len(_cache),
            "valid_entries": valid,
            "expired_entries": len(_cache) - valid,
            "max_capacity": _MAX_CACHE_SIZE,
        }
