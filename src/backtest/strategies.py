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


def ema_cross(rows: list[dict[str, Any]], fast: int = 12, slow: int = 26) -> list[int]:
    """
    指數均線交叉（EMA Cross）：
    - 快 EMA > 慢 EMA → 做多
    - 快 EMA < 慢 EMA → 做空
    """
    n = len(rows)
    if n < slow:
        return [0] * n
    closes = [r["close"] for r in rows]
    ema_f = _ema(closes, fast)
    ema_s = _ema(closes, slow)
    signals: list[int] = [0] * slow
    for i in range(slow, n):
        if ema_f[i] > ema_s[i] and ema_f[i - 1] <= ema_s[i - 1]:
            s = 1
        elif ema_f[i] < ema_s[i] and ema_f[i - 1] >= ema_s[i - 1]:
            s = -1
        else:
            s = signals[-1] if signals else 0
        signals.append(s)
    return signals


def donchian_channel(
    rows: list[dict[str, Any]], period: int = 20, breakout_mode: int = 1,
) -> list[int]:
    """
    唐奇安通道突破：
    - 收盤突破上軌（period 根最高價）→ 做多
    - 收盤跌破下軌（period 根最低價）→ 做空
    - breakout_mode=1: 突破即持倉；=0: 突破僅觸發，回到中線平倉
    """
    n = len(rows)
    if n < period:
        return [0] * n
    signals: list[int] = [0] * period
    for i in range(period, n):
        highs = [rows[j]["high"] for j in range(i - period, i)]
        lows = [rows[j]["low"] for j in range(i - period, i)]
        upper = max(highs)
        lower = min(lows)
        close = rows[i]["close"]
        prev_s = signals[-1]
        if close >= upper:
            s = 1
        elif close <= lower:
            s = -1
        else:
            s = prev_s if breakout_mode else 0
        signals.append(s)
    return signals


def supertrend(
    rows: list[dict[str, Any]], period: int = 10, multiplier: float = 3.0,
) -> list[int]:
    """
    超級趨勢（Supertrend）：
    基於 ATR 的趨勢跟蹤，價格突破上/下帶切換多空。
    """
    n = len(rows)
    if n < period + 1:
        return [0] * n
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]

    tr_list = [0.0]
    for i in range(1, n):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        tr_list.append(tr)

    atr = [0.0] * n
    atr[period] = sum(tr_list[1:period + 1]) / period
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr_list[i]) / period

    upper_band = [0.0] * n
    lower_band = [0.0] * n
    direction = [1] * n
    signals: list[int] = [0] * n

    for i in range(period, n):
        hl2 = (highs[i] + lows[i]) / 2
        basic_upper = hl2 + multiplier * atr[i]
        basic_lower = hl2 - multiplier * atr[i]
        upper_band[i] = min(basic_upper, upper_band[i - 1]) if upper_band[i - 1] != 0 and closes[i - 1] <= upper_band[i - 1] else basic_upper
        lower_band[i] = max(basic_lower, lower_band[i - 1]) if lower_band[i - 1] != 0 and closes[i - 1] >= lower_band[i - 1] else basic_lower

        if closes[i] > upper_band[i]:
            direction[i] = 1
        elif closes[i] < lower_band[i]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]

        if direction[i] != direction[i - 1]:
            signals[i] = direction[i]
        else:
            signals[i] = signals[i - 1]
    return signals


def dual_thrust(
    rows: list[dict[str, Any]], period: int = 4, k1: float = 0.5, k2: float = 0.5,
) -> list[int]:
    """
    雙推力（Dual Thrust）：
    基於前 N 根 K 線的 Range 計算上下閾值，突破做多/做空。
    """
    n = len(rows)
    if n < period + 1:
        return [0] * n
    signals: list[int] = [0] * (period + 1)
    for i in range(period + 1, n):
        hh = max(rows[j]["high"] for j in range(i - period, i))
        ll = min(rows[j]["low"] for j in range(i - period, i))
        hc = max(rows[j]["close"] for j in range(i - period, i))
        lc = min(rows[j]["close"] for j in range(i - period, i))
        range_val = max(hh - lc, hc - ll)
        open_price = rows[i]["open"]
        close = rows[i]["close"]
        upper = open_price + k1 * range_val
        lower = open_price - k2 * range_val
        prev_s = signals[-1]
        if close > upper:
            s = 1
        elif close < lower:
            s = -1
        else:
            s = prev_s
        signals.append(s)
    return signals


def vwap_reversion(
    rows: list[dict[str, Any]], period: int = 20, threshold: float = 2.0,
) -> list[int]:
    """
    VWAP 均值回歸：
    - 價格偏離 VWAP 超過 threshold 個標準差 → 反向交易
    - 高於 VWAP+threshold*std → 做空（超買回歸）
    - 低於 VWAP-threshold*std → 做多（超賣回歸）
    """
    n = len(rows)
    if n < period:
        return [0] * n
    signals: list[int] = [0] * period
    for i in range(period, n):
        window = rows[i - period:i + 1]
        cum_vol = sum(r["volume"] for r in window) or 1
        cum_pv = sum(r["close"] * r["volume"] for r in window)
        vwap = cum_pv / cum_vol
        prices = [r["close"] for r in window]
        mean_p = sum(prices) / len(prices)
        var_p = sum((p - mean_p) ** 2 for p in prices) / len(prices)
        std_p = var_p ** 0.5 if var_p > 0 else 1
        close = rows[i]["close"]
        z = (close - vwap) / std_p if std_p > 0 else 0
        prev_s = signals[-1]
        if z < -threshold:
            s = 1
        elif z > threshold:
            s = -1
        elif abs(z) < 0.5:
            s = 0
        else:
            s = prev_s
        signals.append(s)
    return signals


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
    "ema_cross": {
        "params": ["fast", "slow"],
        "param_grid": {"fast": [8, 12, 15], "slow": [21, 26, 34]},
        "defaults": {"fast": 12, "slow": 26},
    },
    "donchian_channel": {
        "params": ["period", "breakout_mode"],
        "param_grid": {"period": [10, 20, 30], "breakout_mode": [1]},
        "defaults": {"period": 20, "breakout_mode": 1},
    },
    "supertrend": {
        "params": ["period", "multiplier"],
        "param_grid": {"period": [7, 10, 14], "multiplier": [2.0, 3.0, 4.0]},
        "defaults": {"period": 10, "multiplier": 3.0},
    },
    "dual_thrust": {
        "params": ["period", "k1", "k2"],
        "param_grid": {"period": [3, 4, 5], "k1": [0.4, 0.5, 0.6], "k2": [0.4, 0.5, 0.6]},
        "defaults": {"period": 4, "k1": 0.5, "k2": 0.5},
    },
    "vwap_reversion": {
        "params": ["period", "threshold"],
        "param_grid": {"period": [15, 20, 30], "threshold": [1.5, 2.0, 2.5]},
        "defaults": {"period": 20, "threshold": 2.0},
    },
}

_STRATEGY_FUNCS = {
    "sma_cross": sma_cross,
    "buy_and_hold": buy_and_hold,
    "rsi_signal": rsi_signal,
    "macd_cross": macd_cross,
    "bollinger_signal": bollinger_signal,
    "ema_cross": ema_cross,
    "donchian_channel": donchian_channel,
    "supertrend": supertrend,
    "dual_thrust": dual_thrust,
    "vwap_reversion": vwap_reversion,
}


def get_signal(strategy: str, rows: list[dict[str, Any]], **kwargs: Any) -> list[int]:
    """依策略名稱與參數產生信號。"""
    func = _STRATEGY_FUNCS.get(strategy)
    if func:
        if strategy == "buy_and_hold":
            return func(rows)
        return func(rows, **kwargs)
    return [0] * len(rows)
