# 即時價格與策略信號
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

from src.config import STRATEGY_LABELS


def get_live_price(symbol: str, exchange: str = "okx") -> dict[str, Any] | None:
    """取得即時價格（最新一根 K 線）"""
    try:
        if exchange == "yfinance":
            import yfinance as yf
            t = yf.Ticker(symbol)
            df = t.history(period="1d", interval="1m")
            if df.empty:
                return None
            last = df.iloc[-1]
            return {
                "price": float(last["Close"]),
                "open": float(last["Open"]),
                "high": float(last["High"]),
                "low": float(last["Low"]),
                "volume": float(last["Volume"]),
                "timestamp": int(last.name.timestamp() * 1000) if hasattr(last.name, "timestamp") else int(time.time() * 1000),
            }
        else:
            import ccxt
            from src.data.sources.crypto_ccxt import _create_exchange
            ex, actual_id = _create_exchange(exchange)
            ticker = ex.fetch_ticker(symbol)
            return {
                "price": ticker.get("last", 0),
                "open": ticker.get("open", 0),
                "high": ticker.get("high", 0),
                "low": ticker.get("low", 0),
                "volume": ticker.get("baseVolume", 0),
                "change_pct": ticker.get("percentage", 0),
                "timestamp": ticker.get("timestamp", int(time.time() * 1000)),
            }
    except Exception as e:
        logger.warning("get_live_price failed for %s: %s", symbol, e)
        return None


def get_current_signal(symbol: str, exchange: str, timeframe: str,
                       strategy: str, strategy_params: dict) -> dict[str, Any]:
    """計算當前策略信號"""
    from src.backtest import strategies as strat_mod

    try:
        if exchange == "yfinance":
            from src.data.traditional import TraditionalDataFetcher
            fetcher = TraditionalDataFetcher()
        else:
            from src.data.crypto import CryptoDataFetcher
            fetcher = CryptoDataFetcher(exchange)

        until_ms = int(time.time() * 1000)
        tf_ms = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000,
                 "4h": 14_400_000, "1d": 86_400_000}.get(timeframe, 3_600_000)
        since_ms = until_ms - 100 * tf_ms

        rows = fetcher.get_ohlcv(symbol, timeframe, since_ms, until_ms, fill_gaps=True)
        if not rows:
            return {"signal": 0, "signal_text": "無數據", "bars": 0, "price": 0}

        signals = strat_mod.get_signal(strategy, rows, **strategy_params)
        current_signal = signals[-1] if signals else 0
        prev_signal = signals[-2] if len(signals) > 1 else 0
        price = rows[-1]["close"]
        signal_changed = current_signal != prev_signal

        signal_text = {1: "🟢 做多", -1: "🔴 做空", 0: "⚪ 觀望"}.get(current_signal, "⚪ 觀望")

        return {
            "signal": current_signal,
            "prev_signal": prev_signal,
            "signal_text": signal_text,
            "signal_changed": signal_changed,
            "price": price,
            "bars": len(rows),
            "timestamp": rows[-1]["timestamp"],
        }
    except Exception as e:
        return {"signal": 0, "signal_text": f"❌ 錯誤: {str(e)[:50]}", "bars": 0, "price": 0}
