# 限流保護：指數退避重試
from __future__ import annotations

import time
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """簡單的滑動窗口限流器。"""

    def __init__(self, max_calls: int = 10, period: float = 1.0) -> None:
        self._max_calls = max_calls
        self._period = period
        self._calls: list[float] = []

    def wait(self) -> None:
        now = time.monotonic()
        self._calls = [t for t in self._calls if now - t < self._period]
        if len(self._calls) >= self._max_calls:
            sleep_time = self._period - (now - self._calls[0])
            if sleep_time > 0:
                logger.debug("Rate limiter: sleeping %.2fs", sleep_time)
                time.sleep(sleep_time)
        self._calls.append(time.monotonic())
