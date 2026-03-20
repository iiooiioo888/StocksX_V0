# 數據服務層 - 整合真實數據源（延遲初始化）
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import time

import pandas as pd

try:
    import ccxt

    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class DataService:
    """數據服務類 - 整合所有真實數據源（延遲初始化）"""

    def __init__(self) -> None:
        self._binance = None
        self._binance_futures = None
        # 緩存
        self.price_cache: dict[str, dict] = {}
        self.kline_cache: dict[str, pd.DataFrame] = {}
        self.depth_cache: dict[str, dict] = {}
        self.last_update: dict[str, float] = {}

    def _get_exchange(self, symbol: str):
        """根據 symbol 類型選擇正確的交易所實例（現貨/永續）."""
        if ":" in symbol:
            return self.binance_futures
        return self.binance

    @staticmethod
    def _to_binance_symbol(symbol: str) -> str:
        """將通用 symbol 轉為 Binance 格式：BTC/USDT:USDT → BTCUSDT."""
        return symbol.replace("/", "").split(":")[0]

    @property
    def binance(self):
        if self._binance is None and CCXT_AVAILABLE:
            self._binance = ccxt.binance(
                {
                    "options": {"defaultType": "spot"},
                    "timeout": 10000,
                }
            )
        return self._binance

    @property
    def binance_futures(self):
        if self._binance_futures is None and CCXT_AVAILABLE:
            self._binance_futures = ccxt.binance(
                {
                    "options": {"defaultType": "future"},
                    "timeout": 10000,
                }
            )
        return self._binance_futures

    # ════════════════════════════════════════════════════════════
    # 價格數據
    # ════════════════════════════════════════════════════════════

    def get_ticker(self, symbol: str) -> dict | None:
        """取得真實Ticker 數據"""
        try:
            # 從 WebSocket 緩存取得
            if symbol in self.price_cache:
                cache_age = time.time() - self.last_update.get(symbol, 0)
                if cache_age < 5:  # 5 秒內有效
                    return self.price_cache[symbol]

            # 從 CCXT 取得（自動選擇現貨/永續）
            exchange = self._get_exchange(symbol)
            if exchange:
                binance_symbol = self._to_binance_symbol(symbol)
                ticker = exchange.fetch_ticker(binance_symbol)

                data = {
                    "symbol": symbol,
                    "price": ticker.get("last", 0),
                    "change_pct": ticker.get("percentage", 0),
                    "high_24h": ticker.get("high", 0),
                    "low_24h": ticker.get("low", 0),
                    "volume_24h": ticker.get("baseVolume", 0),
                    "quote_volume_24h": ticker.get("quoteVolume", 0),
                    "timestamp": int(time.time() * 1000),
                }

                # 更新緩存
                self.price_cache[symbol] = data
                self.last_update[symbol] = time.time()

                return data

            return None
        except Exception as e:
            logger.warning("ticker_fetch_failed", extra={"symbol": symbol, "error": str(e)})
            return None

    def get_tickers_batch(self, symbols: list[str]) -> dict[str, dict]:
        """批量取得 Ticker 數據"""
        result = {}
        for symbol in symbols:
            data = self.get_ticker(symbol)
            if data:
                result[symbol] = data
        return result

    # ════════════════════════════════════════════════════════════
    # K 線數據
    # ════════════════════════════════════════════════════════════

    def get_kline(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> pd.DataFrame | None:
        """取得真實 K 線數據"""
        try:
            cache_key = f"{symbol}_{timeframe}_{limit}"

            # 檢查緩存（5 分鐘有效）
            if cache_key in self.kline_cache:
                cache_age = time.time() - self.last_update.get(cache_key, 0)
                if cache_age < 300:
                    return self.kline_cache[cache_key]

            # 從 CCXT 取得（自動選擇現貨/永續）
            exchange = self._get_exchange(symbol)
            if exchange:
                binance_symbol = self._to_binance_symbol(symbol)
                ohlcv = exchange.fetch_ohlcv(binance_symbol, timeframe, limit=limit)

                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["time"] = pd.to_datetime(df["timestamp"], unit="ms")
                df["symbol"] = symbol

                # 更新緩存
                self.kline_cache[cache_key] = df
                self.last_update[cache_key] = time.time()

                return df

            return None
        except Exception as e:
            logger.warning("kline_fetch_failed", extra={"symbol": symbol, "error": str(e)})
            return None

    # ════════════════════════════════════════════════════════════
    # 訂單簿深度
    # ════════════════════════════════════════════════════════════

    def get_orderbook(self, symbol: str, limit: int = 20) -> dict | None:
        """取得真實訂單簿數據"""
        try:
            # 檢查緩存（1 秒有效）
            if symbol in self.depth_cache:
                cache_age = time.time() - self.last_update.get(symbol, 0)
                if cache_age < 1:
                    return self.depth_cache[symbol]

            # 從 CCXT 取得（自動選擇現貨/永續）
            exchange = self._get_exchange(symbol)
            if exchange:
                binance_symbol = self._to_binance_symbol(symbol)
                orderbook = exchange.fetch_order_book(binance_symbol, limit=limit)

                data = {
                    "symbol": symbol,
                    "bids": orderbook.get("bids", []),
                    "asks": orderbook.get("asks", []),
                    "timestamp": int(time.time() * 1000),
                }

                # 更新緩存
                self.depth_cache[symbol] = data
                self.last_update[symbol] = time.time()

                return data

            return None
        except Exception as e:
            logger.warning("orderbook_fetch_failed", extra={"symbol": symbol, "error": str(e)})
            return None

    # ════════════════════════════════════════════════════════════
    # 鏈上數據
    # ════════════════════════════════════════════════════════════

    def get_onchain_data(self, symbol: str) -> dict | None:
        """取得鏈上數據（巨鯨動向、交易所流量等）"""
        try:
            if not REQUESTS_AVAILABLE:
                return None

            # 使用 Blockchain.com API（比特幣）
            if "BTC" in symbol:
                response = requests.get("https://blockchain.info/ticker", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    usd_data = data.get("USD", {})
                    return {
                        "symbol": symbol,
                        "price_usd": usd_data.get("last", 0),
                        "volume_24h": usd_data.get("24hvol", 0),
                        "timestamp": int(time.time() * 1000),
                    }

            return None
        except Exception as e:
            logger.warning(f"取得鏈上數據失敗 {symbol}: {e}")
            return None

    def get_whale_transactions(self, symbol: str, limit: int = 24) -> pd.DataFrame | None:
        """取得巨鯨交易數據（⚠️ 模擬數據，僅供演示）"""
        try:
            import random
            from datetime import datetime, timedelta

            # ⚠️ 此為模擬數據，真實場景請接入 Whale Alert / Arkham 等 API
            now = datetime.now()
            timestamps = [now - timedelta(hours=i) for i in range(limit)]

            if "BTC" in symbol:
                whale_buy = [random.uniform(50, 500) for _ in range(limit)]
                whale_sell = [random.uniform(50, 500) for _ in range(limit)]
            elif "ETH" in symbol:
                whale_buy = [random.uniform(500, 5000) for _ in range(limit)]
                whale_sell = [random.uniform(500, 5000) for _ in range(limit)]
            else:
                whale_buy = [random.uniform(10000, 100000) for _ in range(limit)]
                whale_sell = [random.uniform(10000, 100000) for _ in range(limit)]

            df = pd.DataFrame({"時間": timestamps, "巨鯨買入": whale_buy, "巨鯨賣出": whale_sell})

            return df
        except Exception as e:
            logger.warning(f"取得巨鯨數據失敗 {symbol}: {e}")
            return None

    # ════════════════════════════════════════════════════════════
    # 情緒數據
    # ════════════════════════════════════════════════════════════

    def get_fear_greed_index(self) -> dict | None:
        """取得恐懼貪婪指數（真實 API）"""
        try:
            if not REQUESTS_AVAILABLE:
                return None

            response = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("data"):
                    fng_data = data["data"][0]
                    return {
                        "value": int(fng_data.get("value", 50)),
                        "classification": fng_data.get("value_classification", "Neutral"),
                        "timestamp": fng_data.get("timestamp", int(time.time())),
                    }

            return None
        except Exception as e:
            logger.warning(f"取得恐懼貪婪指數失敗：{e}")
            return None

    def get_social_sentiment(self, symbol: str) -> dict | None:
        """取得社群情緒數據"""
        try:
            # 使用 LunarCrush API 或其他服務（此處為模擬真實數據結構）
            import random

            return {
                "symbol": symbol,
                "twitter_positive": random.uniform(40, 70),
                "twitter_negative": random.uniform(20, 50),
                "reddit_positive": random.uniform(35, 65),
                "reddit_negative": random.uniform(25, 55),
                "timestamp": int(time.time() * 1000),
            }
        except Exception as e:
            logger.warning(f"取得社群情緒失敗 {symbol}: {e}")
            return None

    # ════════════════════════════════════════════════════════════
    # 交易信號計算
    # ════════════════════════════════════════════════════════════

    def calculate_signal(self, symbol: str, strategy: str = "sma_cross") -> dict | None:
        """計算真實交易信號"""
        try:
            # 取得 K 線數據
            df = self.get_kline(symbol, timeframe="1h", limit=100)
            if df is None or len(df) < 50:
                return None

            current_price = df["close"].iloc[-1]

            if strategy == "sma_cross":
                # 計算 SMA
                sma_fast = df["close"].rolling(window=5).mean()
                sma_slow = df["close"].rolling(window=20).mean()

                # 檢查交叉
                fast_now = sma_fast.iloc[-1]
                slow_now = sma_slow.iloc[-1]
                fast_prev = sma_fast.iloc[-2]
                slow_prev = sma_slow.iloc[-2]

                signal = 0  # 0=觀望，1=買入，-1=賣出

                # 黃金交叉
                if fast_prev <= slow_prev and fast_now > slow_now:
                    signal = 1
                # 死亡交叉
                elif fast_prev >= slow_prev and fast_now < slow_now:
                    signal = -1

                confidence = abs(fast_now - slow_now) / slow_now * 100

                return {
                    "symbol": symbol,
                    "strategy": strategy,
                    "signal": signal,
                    "action": "BUY" if signal == 1 else ("SELL" if signal == -1 else "HOLD"),
                    "confidence": min(confidence * 10, 95),  # 歸一化到 0-95
                    "price": current_price,
                    "timestamp": int(time.time() * 1000),
                }

            elif strategy == "rsi":
                # 計算 RSI
                delta = df["close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))

                current_rsi = rsi.iloc[-1]

                signal = 0
                if current_rsi < 30:
                    signal = 1  # 超賣，買入
                elif current_rsi > 70:
                    signal = -1  # 超買，賣出

                confidence = abs(50 - current_rsi) / 50 * 100

                return {
                    "symbol": symbol,
                    "strategy": strategy,
                    "signal": signal,
                    "action": "BUY" if signal == 1 else ("SELL" if signal == -1 else "HOLD"),
                    "confidence": confidence,
                    "price": current_price,
                    "rsi": current_rsi,
                    "timestamp": int(time.time() * 1000),
                }

            return None
        except Exception as e:
            logger.error(f"計算信號失敗 {symbol}: {e}")
            return None


# 延遲初始化：首次呼叫時才建立實例
_data_service_instance: DataService | None = None


def get_data_service() -> DataService:
    """取得數據服務實例（延遲初始化）."""
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance


# 向後兼容：data_service 屬性代理
class _LazyDataService:
    """屬性代理，延遲初始化 DataService，保持舊程式碼兼容。"""

    def __getattr__(self, name: str):
        return getattr(get_data_service(), name)


data_service = _LazyDataService()
