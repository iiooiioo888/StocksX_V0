"""
Provider Adapters — 具體 MarketProvider 實現

CCXTProvider  → 加密貨幣 (11 交易所)
YahooProvider → 美股/台股/ETF/期貨

通過 Protocol 實現，可獨立測試、替換。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from .provider import CacheBackend, DictCache, MarketProvider, OHLCV, OrderBook, Ticker

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# CCXT Provider
# ════════════════════════════════════════════════════════════


class CCXTProvider:
    """加密貨幣 Provider（CCXT）."""

    def __init__(
        self,
        exchange_id: str = "binance",
        cache: CacheBackend | None = None,
    ) -> None:
        self._exchange_id = exchange_id
        self._exchange = None
        self._cache = cache or DictCache()
        self._init_exchange()

    def _init_exchange(self) -> None:
        try:
            import ccxt

            exchange_class = getattr(ccxt, self._exchange_id, None)
            if exchange_class:
                self._exchange = exchange_class(
                    {
                        "options": {"defaultType": "spot"},
                        "timeout": 10000,
                    }
                )
            else:
                logger.warning("Unknown exchange: %s", self._exchange_id)
        except ImportError:
            logger.warning("ccxt not installed, CCXTProvider disabled")

    @property
    def name(self) -> str:
        return f"ccxt:{self._exchange_id}"

    def supports(self, symbol: str) -> bool:
        """加密貨幣格式: BTC/USDT 或 BTC/USDT:USDT."""
        return "/" in symbol

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int | None = None,
        limit: int = 500,
    ) -> list[OHLCV]:
        if not self._exchange:
            return []

        cache_key = f"ohlcv:{self._exchange_id}:{symbol}:{timeframe}:{since}:{limit}"
        cached = self._cache.get(cache_key)
        if cached:
            return [OHLCV.from_dict(r) for r in cached]

        try:
            raw_symbol = symbol.replace(":USDT", "")
            ohlcv = self._exchange.fetch_ohlcv(raw_symbol, timeframe, since=since, limit=limit)
            rows = [
                {
                    "timestamp": c[0],
                    "open": c[1],
                    "high": c[2],
                    "low": c[3],
                    "close": c[4],
                    "volume": c[5],
                }
                for c in ohlcv
            ]
            self._cache.set(cache_key, rows, ttl=300)
            return [OHLCV.from_dict(r) for r in rows]
        except Exception as e:
            logger.warning("fetch_ohlcv failed %s: %s", symbol, e)
            return []

    def fetch_ticker(self, symbol: str) -> Ticker | None:
        if not self._exchange:
            return None

        cache_key = f"ticker:{self._exchange_id}:{symbol}"
        cached = self._cache.get(cache_key)
        if cached:
            return Ticker(**cached)

        try:
            raw_symbol = symbol.replace(":USDT", "")
            t = self._exchange.fetch_ticker(raw_symbol)
            data = Ticker(
                symbol=symbol,
                price=float(t.get("last", 0)),
                change_pct=float(t.get("percentage", 0)),
                high_24h=float(t.get("high", 0)),
                low_24h=float(t.get("low", 0)),
                volume_24h=float(t.get("baseVolume", 0)),
                timestamp=int(time.time() * 1000),
            )
            self._cache.set(cache_key, {
                "symbol": data.symbol,
                "price": data.price,
                "change_pct": data.change_pct,
                "high_24h": data.high_24h,
                "low_24h": data.low_24h,
                "volume_24h": data.volume_24h,
                "timestamp": data.timestamp,
            }, ttl=5)
            return data
        except Exception as e:
            logger.warning("fetch_ticker failed %s: %s", symbol, e)
            return None

    def fetch_orderbook(self, symbol: str, limit: int = 20) -> OrderBook | None:
        if not self._exchange:
            return None

        try:
            raw_symbol = symbol.replace(":USDT", "")
            ob = self._exchange.fetch_order_book(raw_symbol, limit=limit)
            return OrderBook(
                symbol=symbol,
                bids=ob.get("bids", []),
                asks=ob.get("asks", []),
                timestamp=int(time.time() * 1000),
            )
        except Exception as e:
            logger.warning("fetch_orderbook failed %s: %s", symbol, e)
            return None


# ════════════════════════════════════════════════════════════
# Yahoo Finance Provider
# ════════════════════════════════════════════════════════════


# Yahoo 時間框架對應
_YF_INTERVALS = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "1h",  # yfinance 無 4h，用 1h 代替
    "1d": "1d", "1w": "1wk", "1M": "1mo",
}

_YF_PERIODS = {
    "1m": "7d", "5m": "60d", "15m": "60d", "30m": "60d",
    "1h": "730d", "4h": "730d",
    "1d": "max", "1w": "max", "1M": "max",
}


class YahooProvider:
    """Yahoo Finance Provider（美股/台股/ETF/期貨）."""

    def __init__(self, cache: CacheBackend | None = None) -> None:
        self._cache = cache or DictCache()

    @property
    def name(self) -> str:
        return "yahoo"

    def supports(self, symbol: str) -> bool:
        """Yahoo 格式: AAPL, 2330.TW, ^GSPC, GC=F."""
        return "/" not in symbol

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int | None = None,
        limit: int = 500,
    ) -> list[OHLCV]:
        cache_key = f"yahoo_ohlcv:{symbol}:{timeframe}:{since}:{limit}"
        cached = self._cache.get(cache_key)
        if cached:
            return [OHLCV.from_dict(r) for r in cached]

        try:
            import yfinance as yf

            interval = _YF_INTERVALS.get(timeframe, "1d")
            period = _YF_PERIODS.get(timeframe, "1y")

            ticker = yf.Ticker(symbol)
            if since:
                from datetime import datetime

                start = datetime.fromtimestamp(since / 1000)
                df = ticker.history(start=start, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)

            if df.empty:
                return []

            rows = []
            for ts, row in df.iterrows():
                rows.append(OHLCV(
                    timestamp=int(ts.timestamp() * 1000),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0)),
                ))

            self._cache.set(cache_key, [r.to_dict() for r in rows], ttl=300)
            return rows
        except Exception as e:
            logger.warning("Yahoo fetch_ohlcv failed %s: %s", symbol, e)
            return []

    def fetch_ticker(self, symbol: str) -> Ticker | None:
        try:
            import yfinance as yf

            t = yf.Ticker(symbol)
            info = t.fast_info
            price = float(info.get("lastPrice", 0) or 0)
            prev = float(info.get("previousClose", 0) or 0)
            change_pct = ((price - prev) / prev * 100) if prev else 0

            return Ticker(
                symbol=symbol,
                price=price,
                change_pct=round(change_pct, 2),
                high_24h=float(info.get("dayHigh", 0) or 0),
                low_24h=float(info.get("dayLow", 0) or 0),
                volume_24h=float(info.get("volume", 0) or 0),
                timestamp=int(time.time() * 1000),
            )
        except Exception as e:
            logger.warning("Yahoo fetch_ticker failed %s: %s", symbol, e)
            return None

    def fetch_orderbook(self, symbol: str, limit: int = 20) -> OrderBook | None:
        # Yahoo Finance 不提供訂單簿
        return None


# ════════════════════════════════════════════════════════════
# Composite Provider（自動路由）
# ════════════════════════════════════════════════════════════


class CompositeProvider:
    """
    組合 Provider：自動將 symbol 路由到正確的底層 Provider。

    用法：
        provider = CompositeProvider()
        provider.add(CCXTProvider("binance"))
        provider.add(YahooProvider())
        rows = provider.fetch_ohlcv("BTC/USDT", "1h")  # → CCXT
        rows = provider.fetch_ohlcv("AAPL", "1d")      # → Yahoo
    """

    def __init__(self) -> None:
        self._providers: list[MarketProvider] = []

    def add(self, provider: MarketProvider) -> CompositeProvider:
        self._providers.append(provider)
        return self

    @property
    def name(self) -> str:
        return "composite"

    def supports(self, symbol: str) -> bool:
        return any(p.supports(symbol) for p in self._providers)

    def _get_provider(self, symbol: str) -> MarketProvider | None:
        for p in self._providers:
            if p.supports(symbol):
                return p
        return None

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: int | None = None,
        limit: int = 500,
    ) -> list[OHLCV]:
        p = self._get_provider(symbol)
        if p:
            return p.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        logger.warning("No provider for symbol: %s", symbol)
        return []

    def fetch_ticker(self, symbol: str) -> Ticker | None:
        p = self._get_provider(symbol)
        if p:
            return p.fetch_ticker(symbol)
        return None

    def fetch_orderbook(self, symbol: str, limit: int = 20) -> OrderBook | None:
        p = self._get_provider(symbol)
        if p:
            return p.fetch_orderbook(symbol, limit=limit)
        return None
