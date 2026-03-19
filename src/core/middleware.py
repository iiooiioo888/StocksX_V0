"""
中間件管道 — 橫切關注點處理

取代散落在各處的 try/except、日誌、限流邏輯。
每個中間件是一個 callable，串成管道執行。

用法：
    pipe = MiddlewarePipeline()
    pipe.use(RetryMiddleware(max_retries=3))
    pipe.use(LoggingMiddleware())
    pipe.use(RateLimitMiddleware(rps=10))
    result = pipe.execute(lambda: provider.fetch_ohlcv(...))
"""

from __future__ import annotations

import functools
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


class Middleware:
    """中間件基類。子類實現 before/after/error。"""

    def before(self, context: dict[str, Any]) -> None:
        """執行前 hook."""
        pass

    def after(self, context: dict[str, Any], result: Any) -> Any:
        """執行後 hook，可修改 result."""
        return result

    def error(self, context: dict[str, Any], exc: Exception) -> Any | None:
        """異常 hook，返回值替代異常，None 則繼續拋出."""
        return None


# ─── 常用中間件 ───


class LoggingMiddleware(Middleware):
    """自動日誌中間件."""

    def __init__(self, log_level: int = logging.DEBUG) -> None:
        self._level = log_level

    def before(self, context: dict[str, Any]) -> None:
        context["_start_time"] = time.monotonic()
        logger.log(self._level, "▶ %s args=%s", context.get("name", "?"), context.get("args", {}))

    def after(self, context: dict[str, Any], result: Any) -> Any:
        elapsed = time.monotonic() - context.get("_start_time", 0)
        logger.log(self._level, "✔ %s done in %.1fms", context.get("name", "?"), elapsed * 1000)
        return result

    def error(self, context: dict[str, Any], exc: Exception) -> Any | None:
        elapsed = time.monotonic() - context.get("_start_time", 0)
        logger.error("✘ %s failed in %.1fms: %s", context.get("name", "?"), elapsed * 1000, exc)
        return None


class RetryMiddleware(Middleware):
    """自動重試中間件."""

    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,),
    ) -> None:
        self._max_retries = max_retries
        self._delay = delay
        self._backoff = backoff
        self._exceptions = exceptions


class RateLimitMiddleware(Middleware):
    """簡單速率限制中間件."""

    def __init__(self, rps: float = 10.0) -> None:
        self._min_interval = 1.0 / rps if rps > 0 else 0
        self._last_call: float = 0

    def before(self, context: dict[str, Any]) -> None:
        if self._min_interval > 0:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()


class TimingMiddleware(Middleware):
    """耗時統計中間件."""

    def before(self, context: dict[str, Any]) -> None:
        context["_timing_start"] = time.monotonic()

    def after(self, context: dict[str, Any], result: Any) -> Any:
        elapsed = time.monotonic() - context.get("_timing_start", 0)
        context["elapsed_ms"] = round(elapsed * 1000, 1)
        return result


# ─── 管道 ───


class MiddlewarePipeline:
    """
    中間件管道：將多個 Middleware 串成鏈執行。

    執行順序：
      before → [mw1, mw2, mw3] → func() → [mw3, mw2, mw1] after
    """

    def __init__(self, name: str = "pipeline") -> None:
        self.name = name
        self._middlewares: list[Middleware] = []

    def use(self, mw: Middleware) -> MiddlewarePipeline:
        """添加中間件，支持鏈式調用."""
        self._middlewares.append(mw)
        return self

    def execute(self, func: Callable[[], T], **context_kwargs: Any) -> T:
        """執行管道."""
        ctx: dict[str, Any] = {"name": self.name, **context_kwargs}

        # before hooks（正序）
        for mw in self._middlewares:
            mw.before(ctx)

        try:
            result = func()
        except Exception as exc:
            # error hooks（正序，第一個返回非 None 就替代異常）
            for mw in self._middlewares:
                recovered = mw.error(ctx, exc)
                if recovered is not None:
                    result = recovered
                    break
            else:
                raise

        # after hooks（逆序）
        for mw in reversed(self._middlewares):
            result = mw.after(ctx, result)

        return result


# ─── 裝飾器語法 ───


def with_middleware(*middlewares: Middleware, name: str = "") -> Callable:
    """裝飾器：為函數自動添加中間件."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            pipe = MiddlewarePipeline(name=name or func.__name__)
            for mw in middlewares:
                pipe.use(mw)
            return pipe.execute(lambda: func(*args, **kwargs))

        return wrapper

    return decorator
