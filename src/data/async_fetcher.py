"""
異步數據抓取器 — 並發拉取多個交易對的 K 線

優勢：
- 並發請求多個 symbol，大幅減少等待時間
- 自動重試 & 錯誤隔離
- 結構化日誌

用法：
    from src.data.async_fetcher import AsyncOHLCVFetcher

    async with AsyncOHLCVFetcher() as fetcher:
        results = await fetcher.fetch_multiple(
            symbols=["BTC/USDT", "ETH/USDT", "SOL/USDT"],
            timeframe="1h",
            limit=500,
        )
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AsyncOHLCVFetcher:
    """
    異步 OHLCV 數據抓取器.

    使用 asyncio + ccxt async 介面（如果可用），
    或在同步模式下用線程池並發執行.
    """

    def __init__(
        self,
        exchange_id: str = "binance",
        max_concurrent: int = 5,
        timeout: float = 15.0,
        max_retries: int = 2,
    ) -> None:
        self._exchange_id = exchange_id
        self._max_concurrent = max_concurrent
        self._timeout = timeout
        self._max_retries = max_retries
        self._exchange: Any = None
        self._semaphore: asyncio.Semaphore | None = None

    async def __aenter__(self) -> AsyncOHLCVFetcher:
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        try:
            import ccxt.async_support as ccxt_async

            exchange_class = getattr(ccxt_async, self._exchange_id)
            self._exchange = exchange_class({"timeout": int(self._timeout * 1000)})
        except (ImportError, AttributeError):
            # Fallback: use sync ccxt in thread pool
            import ccxt

            exchange_class = getattr(ccxt, self._exchange_id)
            self._exchange = exchange_class({"timeout": int(self._timeout * 1000)})
            self._sync_mode = True
        else:
            self._sync_mode = False
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._exchange:
            if hasattr(self._exchange, "close"):
                try:
                    await self._exchange.close()
                except Exception:
                    pass

    async def _fetch_one(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 500,
        since: int | None = None,
    ) -> list[dict[str, Any]]:
        """抓取單個 symbol 的 OHLCV."""
        assert self._semaphore is not None

        async with self._semaphore:
            for attempt in range(self._max_retries + 1):
                try:
                    if self._sync_mode:
                        # 同步模式：在線程池中執行
                        loop = asyncio.get_event_loop()
                        raw = await loop.run_in_executor(
                            None,
                            lambda: self._exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit),
                        )
                    else:
                        raw = await asyncio.wait_for(
                            self._exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit),
                            timeout=self._timeout,
                        )

                    rows = []
                    for candle in raw:
                        if len(candle) >= 6:
                            rows.append(
                                {
                                    "timestamp": candle[0],
                                    "open": candle[1],
                                    "high": candle[2],
                                    "low": candle[3],
                                    "close": candle[4],
                                    "volume": candle[5],
                                }
                            )

                    logger.info(
                        "async_fetch_ok",
                        extra={"symbol": symbol, "timeframe": timeframe, "bars": len(rows)},
                    )
                    return rows

                except Exception as e:
                    if attempt < self._max_retries:
                        wait = 1.0 * (2**attempt)
                        logger.warning(
                            "async_fetch_retry",
                            extra={"symbol": symbol, "attempt": attempt + 1, "error": str(e), "wait": wait},
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.error(
                            "async_fetch_failed",
                            extra={"symbol": symbol, "error": str(e)},
                        )
                        return []

            return []

    async def fetch_multiple(
        self,
        symbols: list[str],
        timeframe: str = "1h",
        limit: int = 500,
        since: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        並發抓取多個 symbol 的 OHLCV.

        Args:
            symbols: 交易對列表
            timeframe: K 線週期
            limit: 每個 symbol 最大 K 線數
            since: 起始時間戳

        Returns:
            {symbol: [ohlcv_rows]}
        """
        tasks = {symbol: asyncio.create_task(self._fetch_one(symbol, timeframe, limit, since)) for symbol in symbols}

        results: dict[str, list[dict[str, Any]]] = {}
        for symbol, task in tasks.items():
            try:
                rows = await task
                results[symbol] = rows
            except Exception as e:
                logger.error("async_fetch_task_error", extra={"symbol": symbol, "error": str(e)})
                results[symbol] = []

        return results


async def fetch_ohlcv_batch(
    symbols: list[str],
    exchange_id: str = "binance",
    timeframe: str = "1h",
    limit: int = 500,
    max_concurrent: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    """
    便捷函數 — 並發抓取多個 symbol.

    Usage:
        results = await fetch_ohlcv_batch(["BTC/USDT", "ETH/USDT"])
    """
    async with AsyncOHLCVFetcher(exchange_id, max_concurrent) as fetcher:
        return await fetcher.fetch_multiple(symbols, timeframe, limit)
