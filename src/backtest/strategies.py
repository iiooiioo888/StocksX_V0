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
    "ichimoku": {
        "params": ["tenkan", "kijun", "senkou_b"],
        "param_grid": {"tenkan": [9], "kijun": [26], "senkou_b": [52]},
        "defaults": {"tenkan": 9, "kijun": 26, "senkou_b": 52},
    },
    "stochastic": {
        "params": ["k_period", "d_period", "oversold", "overbought"],
        "param_grid": {"k_period": [9, 14], "d_period": [3], "oversold": [20], "overbought": [80]},
        "defaults": {"k_period": 14, "d_period": 3, "oversold": 20.0, "overbought": 80.0},
    },
    "williams_r": {
        "params": ["period", "oversold", "overbought"],
        "param_grid": {"period": [10, 14, 21], "oversold": [-80], "overbought": [-20]},
        "defaults": {"period": 14, "oversold": -80.0, "overbought": -20.0},
    },
    "adx_trend": {
        "params": ["period", "threshold"],
        "param_grid": {"period": [10, 14, 20], "threshold": [20, 25, 30]},
        "defaults": {"period": 14, "threshold": 25.0},
    },
    "parabolic_sar": {
        "params": ["af_start", "af_step", "af_max"],
        "param_grid": {"af_start": [0.02], "af_step": [0.02], "af_max": [0.20]},
        "defaults": {"af_start": 0.02, "af_step": 0.02, "af_max": 0.20},
    },
}

def ichimoku(rows: list[dict[str, Any]], tenkan: int = 9, kijun: int = 26, senkou_b: int = 52) -> list[int]:
    """一目均衡表：轉換線 > 基準線做多，< 做空，價格在雲帶之上確認。"""
    n = len(rows)
    if n < senkou_b:
        return [0] * n
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    closes = [r["close"] for r in rows]

    def _midline(h, l, p, i):
        return (max(h[max(0, i - p + 1):i + 1]) + min(l[max(0, i - p + 1):i + 1])) / 2

    signals: list[int] = [0] * senkou_b
    for i in range(senkou_b, n):
        tenkan_val = _midline(highs, lows, tenkan, i)
        kijun_val = _midline(highs, lows, kijun, i)
        senkou_a = (tenkan_val + kijun_val) / 2
        senkou_b_val = _midline(highs, lows, senkou_b, i)
        cloud_top = max(senkou_a, senkou_b_val)
        cloud_bot = min(senkou_a, senkou_b_val)
        prev_s = signals[-1]
        if tenkan_val > kijun_val and closes[i] > cloud_top:
            s = 1
        elif tenkan_val < kijun_val and closes[i] < cloud_bot:
            s = -1
        else:
            s = prev_s
        signals.append(s)
    return signals


def stochastic(rows: list[dict[str, Any]], k_period: int = 14, d_period: int = 3,
               oversold: float = 20, overbought: float = 80) -> list[int]:
    """隨機指標（KD）：K 線從超賣區上穿 D 線做多，從超買區下穿做空。"""
    n = len(rows)
    if n < k_period + d_period:
        return [0] * n
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    closes = [r["close"] for r in rows]
    k_vals = [0.0] * n
    for i in range(k_period - 1, n):
        hh = max(highs[i - k_period + 1:i + 1])
        ll = min(lows[i - k_period + 1:i + 1])
        k_vals[i] = ((closes[i] - ll) / (hh - ll) * 100) if hh != ll else 50
    d_vals = [0.0] * n
    for i in range(k_period + d_period - 2, n):
        d_vals[i] = sum(k_vals[i - d_period + 1:i + 1]) / d_period

    signals: list[int] = [0] * (k_period + d_period)
    for i in range(k_period + d_period, n):
        prev_s = signals[-1]
        if k_vals[i] > d_vals[i] and k_vals[i - 1] <= d_vals[i - 1] and k_vals[i] < oversold + 20:
            s = 1
        elif k_vals[i] < d_vals[i] and k_vals[i - 1] >= d_vals[i - 1] and k_vals[i] > overbought - 20:
            s = -1
        else:
            s = prev_s
        signals.append(s)
    return signals


def williams_r(rows: list[dict[str, Any]], period: int = 14,
               oversold: float = -80, overbought: float = -20) -> list[int]:
    """威廉指標（Williams %R）：< oversold 做多，> overbought 做空。"""
    n = len(rows)
    if n < period:
        return [0] * n
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    closes = [r["close"] for r in rows]
    signals: list[int] = [0] * period
    for i in range(period, n):
        hh = max(highs[i - period + 1:i + 1])
        ll = min(lows[i - period + 1:i + 1])
        wr = ((hh - closes[i]) / (hh - ll) * -100) if hh != ll else -50
        prev_s = signals[-1]
        if wr < oversold:
            s = 1
        elif wr > overbought:
            s = -1
        else:
            s = prev_s
        signals.append(s)
    return signals


def adx_trend(rows: list[dict[str, Any]], period: int = 14, threshold: float = 25) -> list[int]:
    """ADX 趨勢強度：ADX > threshold 時，+DI > -DI 做多，反之做空。"""
    n = len(rows)
    if n < period * 2:
        return [0] * n
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    closes = [r["close"] for r in rows]

    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    tr_list = [0.0] * n
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm[i] = up if up > down and up > 0 else 0
        minus_dm[i] = down if down > up and down > 0 else 0
        tr_list[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))

    atr = [0.0] * n
    sp = [0.0] * n
    sm = [0.0] * n
    atr[period] = sum(tr_list[1:period + 1]) / period
    sp[period] = sum(plus_dm[1:period + 1]) / period
    sm[period] = sum(minus_dm[1:period + 1]) / period
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr_list[i]) / period
        sp[i] = (sp[i - 1] * (period - 1) + plus_dm[i]) / period
        sm[i] = (sm[i - 1] * (period - 1) + minus_dm[i]) / period

    signals: list[int] = [0] * (period * 2)
    adx_val = 0.0
    for i in range(period * 2, n):
        pdi = (sp[i] / atr[i] * 100) if atr[i] > 0 else 0
        mdi = (sm[i] / atr[i] * 100) if atr[i] > 0 else 0
        dx = abs(pdi - mdi) / (pdi + mdi) * 100 if (pdi + mdi) > 0 else 0
        adx_val = (adx_val * (period - 1) + dx) / period
        prev_s = signals[-1]
        if adx_val > threshold:
            s = 1 if pdi > mdi else -1
        else:
            s = 0
        signals.append(s)
    return signals


def parabolic_sar(rows: list[dict[str, Any]], af_start: float = 0.02, af_step: float = 0.02,
                  af_max: float = 0.20) -> list[int]:
    """拋物線 SAR：價格突破 SAR 點翻轉方向。"""
    n = len(rows)
    if n < 3:
        return [0] * n
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]

    trend = 1
    sar = lows[0]
    ep = highs[0]
    af = af_start
    signals: list[int] = [0, 0]

    for i in range(2, n):
        prev_sar = sar
        sar = prev_sar + af * (ep - prev_sar)
        if trend == 1:
            sar = min(sar, lows[i - 1], lows[i - 2])
            if lows[i] < sar:
                trend = -1
                sar = ep
                ep = lows[i]
                af = af_start
            else:
                if highs[i] > ep:
                    ep = highs[i]
                    af = min(af + af_step, af_max)
        else:
            sar = max(sar, highs[i - 1], highs[i - 2])
            if highs[i] > sar:
                trend = 1
                sar = ep
                ep = highs[i]
                af = af_start
            else:
                if lows[i] < ep:
                    ep = lows[i]
                    af = min(af + af_step, af_max)
        signals.append(trend)
    return signals


_STRATEGY_FUNCS = {
    "sma_cross": sma_cross, "buy_and_hold": buy_and_hold,
    "rsi_signal": rsi_signal, "macd_cross": macd_cross,
    "bollinger_signal": bollinger_signal, "ema_cross": ema_cross,
    "donchian_channel": donchian_channel, "supertrend": supertrend,
    "dual_thrust": dual_thrust, "vwap_reversion": vwap_reversion,
    "ichimoku": ichimoku, "stochastic": stochastic,
    "williams_r": williams_r, "adx_trend": adx_trend,
    "parabolic_sar": parabolic_sar,
}


def get_signal(strategy: str, rows: list[dict[str, Any]], **kwargs: Any) -> list[int]:
    """依策略名稱與參數產生信號。"""
    func = _STRATEGY_FUNCS.get(strategy)
    if func:
        if strategy == "buy_and_hold":
            return func(rows)
        return func(rows, **kwargs)
    return [0] * len(rows)
