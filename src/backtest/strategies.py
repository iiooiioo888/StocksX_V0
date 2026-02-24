# 回測策略：產生信號 (1=多, -1=空, 0=觀望)
from __future__ import annotations

from typing import Any


def sma_cross(rows: list[dict[str, Any]], fast: int = 10, slow: int = 30) -> list[int]:
    """
    雙均線交叉：
    - 快線 > 慢線 → 做多(1)
    - 快線 < 慢線 → 做空(-1)
    - 其餘維持前一根狀態（初始為觀望 0）
    """
    if len(rows) < slow:
        return [0] * len(rows)
    closes = [r["close"] for r in rows]
    signals: list[int] = []
    for i in range(len(rows)):
        if i < slow:
            signals.append(0)
            continue
        fast_ma = sum(closes[i - fast : i]) / fast
        slow_ma = sum(closes[i - slow : i]) / slow
        if fast_ma > slow_ma:
            s = 1
        elif fast_ma < slow_ma:
            s = -1
        else:
            s = signals[-1] if signals else 0
        signals.append(s)
    return signals


def buy_and_hold(rows: list[dict[str, Any]]) -> list[int]:
    """從第一根 K 線起持多。"""
    return [1] * len(rows) if rows else []


def _ema(prices: list[float], period: int) -> list[float]:
    k = 2.0 / (period + 1)
    out = [prices[0]] if prices else []
    for i in range(1, len(prices)):
        out.append(prices[i] * k + out[-1] * (1 - k))
    return out


def rsi_signal(
    rows: list[dict[str, Any]],
    period: int = 14,
    oversold: float = 30,
    overbought: float = 70,
) -> list[int]:
    """
    RSI：
    - 低於 oversold → 做多(1)
    - 高於 overbought → 做空(-1)
    - 其餘維持前態（觀望 / 多 / 空）
    """
    if len(rows) < period + 1:
        return [0] * len(rows)
    closes = [r["close"] for r in rows]
    signals = [0]
    for i in range(1, period):
        signals.append(0)
    for i in range(period, len(closes)):
        gains = []
        losses = []
        for j in range(i - period + 1, i + 1):
            chg = closes[j] - closes[j - 1]
            gains.append(max(chg, 0))
            losses.append(max(-chg, 0))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            rsi_val = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_val = 100 - (100 / (1 + rs))
        prev_s = signals[-1]
        if rsi_val < oversold:
            s = 1
        elif rsi_val > overbought:
            s = -1
        else:
            s = prev_s
        signals.append(s)
    return signals


def macd_cross(
    rows: list[dict[str, Any]],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> list[int]:
    """
    MACD：
    - 金叉(macd_line 由下往上突破 signal) → 做多(1)
    - 死叉(macd_line 由上往下跌破 signal) → 做空(-1)
    - 其餘維持前態
    """
    n = len(rows)
    if n < slow + signal:
        return [0] * n
    closes = [r["close"] for r in rows]
    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    macd_line = [ema_fast[i] - ema_slow[i] for i in range(n)]
    # signal line = EMA of MACD
    signal_line = _ema(macd_line, signal)
    sig: list[int] = [0] * (slow + signal - 1)
    for i in range(slow + signal - 1, n):
        if macd_line[i] > signal_line[i] and macd_line[i - 1] <= signal_line[i - 1]:
            s = 1
        elif macd_line[i] < signal_line[i] and macd_line[i - 1] >= signal_line[i - 1]:
            s = -1
        else:
            s = sig[-1] if sig else 0
        sig.append(s)
    return sig


def bollinger_signal(
    rows: list[dict[str, Any]],
    period: int = 20,
    std_dev: float = 2.0,
) -> list[int]:
    """
    布林帶：
    - 收盤價跌破下軌 → 做多(1)
    - 收盤價突破上軌 → 做空(-1)
    - 其餘維持前態
    """
    if len(rows) < period:
        return [0] * len(rows)
    closes = [r["close"] for r in rows]
    signals: list[int] = [0] * period
    for i in range(period, len(closes)):
        window = closes[i - period : i]
        ma = sum(window) / period
        var = sum((x - ma) ** 2 for x in window) / period
        std = (var ** 0.5) if var > 0 else 0
        upper = ma + std_dev * std
        lower = ma - std_dev * std
        prev_s = signals[-1]
        if closes[i] <= lower:
            s = 1
        elif closes[i] >= upper:
            s = -1
        else:
            s = prev_s
        signals.append(s)
    return signals


# 策略名稱與可優化參數網格（供 optimizer 使用）
STRATEGY_CONFIG = {
    "sma_cross": {
        "params": ["fast", "slow"],
        "param_grid": {"fast": [5, 10, 15, 20], "slow": [20, 30, 40, 50]},
        "defaults": {"fast": 10, "slow": 30},
    },
    "buy_and_hold": {
        "params": [],
        "param_grid": {},
        "defaults": {},
    },
    "rsi_signal": {
        "params": ["period", "oversold", "overbought"],
        "param_grid": {"period": [10, 14, 20], "oversold": [25, 30], "overbought": [70, 75]},
        "defaults": {"period": 14, "oversold": 30, "overbought": 70},
    },
    "macd_cross": {
        "params": ["fast", "slow", "signal"],
        "param_grid": {"fast": [8, 12], "slow": [26], "signal": [9]},
        "defaults": {"fast": 12, "slow": 26, "signal": 9},
    },
    "bollinger_signal": {
        "params": ["period", "std_dev"],
        "param_grid": {"period": [15, 20, 25], "std_dev": [1.5, 2.0, 2.5]},
        "defaults": {"period": 20, "std_dev": 2.0},
    },
}


def get_signal(strategy: str, rows: list[dict[str, Any]], **kwargs: Any) -> list[int]:
    """依策略名稱與參數產生信號。"""
    if strategy == "sma_cross":
        return sma_cross(rows, **kwargs)
    if strategy == "buy_and_hold":
        return buy_and_hold(rows)
    if strategy == "rsi_signal":
        return rsi_signal(rows, **kwargs)
    if strategy == "macd_cross":
        return macd_cross(rows, **kwargs)
    if strategy == "bollinger_signal":
        return bollinger_signal(rows, **kwargs)
    return [0] * len(rows)
