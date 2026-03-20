# 即時監控數據服務
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import time
from typing import Any

from src.data.service import data_service

# 不需要導入策略函數，我們直接計算信號


def get_live_price(symbol: str) -> dict[str, Any] | None:
    """
    取得即時價格（帶緩存）

    Args:
        symbol: 交易對

    Returns:
        {
            "symbol": str,
            "price": float,
            "change_pct": float,
            "high_24h": float,
            "low_24h": float,
            "volume_24h": float,
            "timestamp": int
        }
    """
    return data_service.get_ticker(symbol)


def batch_get_live_prices(symbols: list[str]) -> dict[str, dict]:
    """
    批量取得即時價格

    Args:
        symbols: 交易對列表

    Returns:
        {symbol: price_data}
    """
    result = {}
    for symbol in symbols:
        try:
            price_data = get_live_price(symbol)
            if price_data:
                result[symbol] = price_data
        except Exception as e:
            logger.error(f"取得價格失敗 {symbol}: {e}")
    return result


def calculate_signal_for_symbol(
    symbol: str, strategy: str, strategy_params: dict[str, Any], timeframe: str = "1h"
) -> dict[str, Any] | None:
    """
    計算單一交易對的信號

    Args:
        symbol: 交易對
        strategy: 策略名稱
        strategy_params: 策略參數
        timeframe: 時間框架

    Returns:
        {
            "symbol": str,
            "strategy": str,
            "signal": int,  # 1=BUY, -1=SELL, 0=HOLD
            "action": str,  # "BUY", "SELL", "HOLD"
            "confidence": float,
            "price": float,
            "timestamp": int
        }
    """
    try:
        # 取得 K 線數據
        df = data_service.get_kline(symbol, timeframe=timeframe, limit=100)

        if df is None or len(df) < 50:
            return None

        # 轉換為 OHLCV 格式
        ohlcv = []
        for _, row in df.iterrows():
            ohlcv.append(
                {
                    "timestamp": int(row["timestamp"]),
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                }
            )

        # 根據策略計算信號
        current_price = df["close"].iloc[-1]

        if strategy == "sma_cross":
            fast_period = strategy_params.get("fast_period", 5)
            slow_period = strategy_params.get("slow_period", 20)

            # 計算 SMA
            sma_fast = df["close"].rolling(window=fast_period).mean()
            sma_slow = df["close"].rolling(window=slow_period).mean()

            # 檢查交叉
            fast_now = sma_fast.iloc[-1]
            slow_now = sma_slow.iloc[-1]
            fast_prev = sma_fast.iloc[-2]
            slow_prev = sma_slow.iloc[-2]

            signal = 0
            if fast_prev <= slow_prev and fast_now > slow_now:
                signal = 1  # 黃金交叉
            elif fast_prev >= slow_prev and fast_now < slow_now:
                signal = -1  # 死亡交叉

            confidence = abs(fast_now - slow_now) / slow_now * 1000 if slow_now > 0 else 0

            return {
                "symbol": symbol,
                "strategy": strategy,
                "signal": signal,
                "action": "BUY" if signal == 1 else ("SELL" if signal == -1 else "HOLD"),
                "confidence": min(confidence * 10, 95),
                "price": current_price,
                "timestamp": int(time.time() * 1000),
            }

        elif strategy == "rsi_signal":
            period = strategy_params.get("period", 14)
            oversold = strategy_params.get("oversold", 30)
            overbought = strategy_params.get("overbought", 70)

            # 計算 RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            current_rsi = rsi.iloc[-1]

            signal = 0
            if current_rsi < oversold:
                signal = 1  # 超賣
            elif current_rsi > overbought:
                signal = -1  # 超買

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

        elif strategy == "macd_cross":
            fast_period = strategy_params.get("fast_period", 12)
            slow_period = strategy_params.get("slow_period", 26)
            signal_period = strategy_params.get("signal_period", 9)

            # 計算 MACD
            exp1 = df["close"].ewm(span=fast_period, adjust=False).mean()
            exp2 = df["close"].ewm(span=slow_period, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal_period, adjust=False).mean()

            # 檢查交叉
            macd_now = macd.iloc[-1]
            signal_now = signal_line.iloc[-1]
            macd_prev = macd.iloc[-2]
            signal_prev = signal_line.iloc[-2]

            signal = 0
            if macd_prev <= signal_prev and macd_now > signal_now:
                signal = 1  # 黃金交叉
            elif macd_prev >= signal_prev and macd_now < signal_now:
                signal = -1  # 死亡交叉

            confidence = abs(macd_now - signal_now) / abs(signal_now) * 100 if signal_now != 0 else 0

            return {
                "symbol": symbol,
                "strategy": strategy,
                "signal": signal,
                "action": "BUY" if signal == 1 else ("SELL" if signal == -1 else "HOLD"),
                "confidence": min(confidence, 95),
                "price": current_price,
                "macd": macd_now,
                "signal_line": signal_now,
                "timestamp": int(time.time() * 1000),
            }

        elif strategy == "bollinger_signal":
            period = strategy_params.get("period", 20)
            std_dev = strategy_params.get("std_dev", 2.0)

            # 計算布林帶
            sma = df["close"].rolling(window=period).mean()
            std = df["close"].rolling(window=period).std()
            upper = sma + (std_dev * std)
            lower = sma - (std_dev * std)

            current_close = df["close"].iloc[-1]

            signal = 0
            if current_close < lower.iloc[-1]:
                signal = 1  # 低於下軌（超賣）
            elif current_close > upper.iloc[-1]:
                signal = -1  # 高於上軌（超買）

            # 計算在帶中的位置
            band_width = upper.iloc[-1] - lower.iloc[-1]
            if band_width > 0:
                position = (current_close - lower.iloc[-1]) / band_width
                confidence = abs(0.5 - position) * 2 * 100
            else:
                confidence = 0

            return {
                "symbol": symbol,
                "strategy": strategy,
                "signal": signal,
                "action": "BUY" if signal == 1 else ("SELL" if signal == -1 else "HOLD"),
                "confidence": confidence,
                "price": current_price,
                "upper_band": upper.iloc[-1],
                "lower_band": lower.iloc[-1],
                "timestamp": int(time.time() * 1000),
            }

        else:
            # 預設持有
            return {
                "symbol": symbol,
                "strategy": strategy,
                "signal": 0,
                "action": "HOLD",
                "confidence": 50,
                "price": current_price,
                "timestamp": int(time.time() * 1000),
            }

    except Exception as e:
        logger.error(f"計算信號失敗 {symbol}: {e}")
        return None


def batch_calculate_signals(watchlist: list[dict]) -> dict[str, dict]:
    """
    批量計算訂閱策略的信號

    Args:
        watchlist: 訂閱列表

    Returns:
        {watch_id: signal_data}
    """
    result = {}

    for w in watchlist:
        if not w.get("is_active", True):
            continue

        watch_id = w.get("id")
        symbol = w.get("symbol", "")
        strategy = w.get("strategy", "")
        strategy_params = w.get("strategy_params", {})
        timeframe = w.get("timeframe", "1h")

        # 計算信號
        signal = calculate_signal_for_symbol(
            symbol=symbol, strategy=strategy, strategy_params=strategy_params, timeframe=timeframe
        )

        if signal:
            result[watch_id] = signal

    return result
