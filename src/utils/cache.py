"""
StocksX 簡易記憶體快取
取代 functools.lru_cache，提供 TTL 支援。
"""

from __future__ import annotations

import functools
import hashlib
import time
from typing import Any, TypeVar
from collections.abc import Callable

F = TypeVar("F", bound=Callable[..., Any])

# 全域快取存儲
_cache: dict[str, tuple[float, Any]] = {}


def cached(ttl: float = 300, key_prefix: str = ""):
    """
    記憶體快取裝飾器，支援 TTL。

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

            # 檢查快取
            now = time.time()
            if cache_key in _cache:
                cached_time, cached_value = _cache[cache_key]
                if now - cached_time < ttl:
                    return cached_value

            # 執行並快取
            result = func(*args, **kwargs)
            _cache[cache_key] = (now, result)
            return result

        return wrapper

    return decorator


def cache_clear(prefix: str = "") -> int:
    """清除快取。指定 prefix 只清除該前綴的快取。"""
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
    valid = sum(1 for t, _ in _cache.values() if now - t < 300)
    return {
        "total_entries": len(_cache),
        "valid_entries": valid,
        "expired_entries": len(_cache) - valid,
    }
