"""
常用裝飾器 — 重試、計時、快取、限流

用法：
    from src.utils.decorators import retry, timed, cached

    @retry(max_retries=3, delay=1.0)
    def fetch_data(symbol): ...

    @timed
    def heavy_computation(): ...

    @cached(ttl=300)
    def expensive_query(key): ...
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable[[F], F]:
    """
    重試裝飾器 — 指數退避.

    Args:
        max_retries: 最大重試次數
        delay: 初始延遲（秒）
        backoff: 退避係數
        on_retry: 重試時的回調
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            current_delay = delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_retries:
                        logger.warning(
                            "retry_attempt",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "error": str(e),
                                "next_delay": current_delay,
                            },
                        )
                        if on_retry:
                            on_retry(attempt + 1, e)
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise last_exc  # type: ignore[misc]
        return functools.update_wrapper(wrapper, func)  # type: ignore[return-value]
    return decorator


def timed(func: F) -> F:
    """計時裝飾器 — 記錄函數執行時間."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.info(
                "function_timing",
                extra={"function": func.__name__, "elapsed_ms": round(elapsed * 1000, 2), "status": "success"},
            )
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.warning(
                "function_timing",
                extra={"function": func.__name__, "elapsed_ms": round(elapsed * 1000, 2), "status": "error", "error": str(e)},
            )
            raise
    return functools.update_wrapper(wrapper, func)  # type: ignore[return-value]


def cached(ttl: float = 300, maxsize: int = 128) -> Callable[[F], F]:
    """
    簡易快取裝飾器 — TTL + LRU.

    Args:
        ttl: 過期時間（秒）
        maxsize: 最大快取項目數
    """
    cache: dict[str, tuple[float, Any]] = {}

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = str(args) + str(sorted(kwargs.items()))
            now = time.time()

            if key in cache:
                ts, value = cache[key]
                if now - ts < ttl:
                    return value

            result = func(*args, **kwargs)

            # 簡易 LRU：超過 maxsize 時清理最舊的
            if len(cache) >= maxsize:
                oldest_key = min(cache, key=lambda k: cache[k][0])
                del cache[oldest_key]

            cache[key] = (now, result)
            return result

        def cache_clear() -> None:
            cache.clear()

        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        return functools.update_wrapper(wrapper, func)  # type: ignore[return-value]
    return decorator


def rate_limit(max_calls: int = 10, period: float = 60.0) -> Callable[[F], F]:
    """
    簡易限流裝飾器 — 滑動窗口.

    Args:
        max_calls: 時間窗口內最大調用次數
        period: 時間窗口（秒）
    """
    calls: list[float] = []

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.time()
            # 清理過期記錄
            nonlocal calls
            calls[:] = [t for t in calls if now - t < period]

            if len(calls) >= max_calls:
                wait_time = period - (now - calls[0])
                logger.warning(
                    "rate_limited",
                    extra={"function": func.__name__, "wait_seconds": round(wait_time, 2)},
                )
                time.sleep(wait_time)
                now = time.time()
                calls[:] = [t for t in calls if now - t < period]

            calls.append(now)
            return func(*args, **kwargs)
        return functools.update_wrapper(wrapper, func)  # type: ignore[return-value]
    return decorator


def suppress_errors(default: Any = None, log: bool = True) -> Callable[[F], F]:
    """
    異常抑制裝飾器 — 發生異常時返回預設值.

    Args:
        default: 異常時返回的預設值
        log: 是否記錄異常
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log:
                    logger.warning(
                        "suppressed_error",
                        extra={"function": func.__name__, "error": str(e)},
                    )
                return default
        return functools.update_wrapper(wrapper, func)  # type: ignore[return-value]
    return decorator
