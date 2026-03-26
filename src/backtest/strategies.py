# 回測策略：產生信號 (1=多, -1=空, 0=觀望)
# v6.0 — NumPy 向量化優化版
from __future__ import annotations

from typing import Any

import numpy as np


def _get_closes(rows: list[dict[str, Any]]) -> np.ndarray:
    """提取收盤價為 numpy array。"""
    return np.array([r["close"] for r in rows], dtype=np.float64)


def _get_highs(rows: list[dict[str, Any]]) -> np.ndarray:
    return np.array([r["high"] for r in rows], dtype=np.float64)


def _get_lows(rows: list[dict[str, Any]]) -> np.ndarray:
    return np.array([r["low"] for r in rows], dtype=np.float64)


def _get_volumes(rows: list[dict[str, Any]]) -> np.ndarray:
    return np.array([r["volume"] for r in rows], dtype=np.float64)


def _sma(arr: np.ndarray, period: int) -> np.ndarray:
    """向量化簡單移動平均。"""
    n = len(arr)
    result = np.zeros(n, dtype=np.float64)
    if n < period:
        return result
    cumsum = np.cumsum(arr)
    result[period:] = (cumsum[period:] - cumsum[:-period]) / period
    return result


def _ema(arr: np.ndarray, period: int) -> np.ndarray:
    """指數移動平均（向量化初始化 + 遞迴迭代）。"""
    n = len(arr)
    if n == 0:
        return np.zeros(0, dtype=np.float64)
    result = np.zeros(n, dtype=np.float64)
    k = 2.0 / (period + 1)
    alpha = 1.0 - k
    # 前 period-1 個值用累計均值初始化（向量化）
    if n >= period:
        result[period - 1] = np.mean(arr[:period])
    else:
        result[0] = arr[0]
        return result
    # 遞迴 EMA（最小化 Python 層開銷）
    for i in range(period, n):
        result[i] = k * arr[i] + alpha * result[i - 1]
    return result


def _forward_fill_signals(signals: np.ndarray, n: int) -> np.ndarray:
    """向量化前向填充：將 0 替換為上一個非零值（numpy 掃描優化）。"""
    mask = signals != 0
    idx = np.where(mask, np.arange(n), 0)
    np.maximum.accumulate(idx, out=idx)
    return signals[idx]


def _signals_from_crossover(fast_line: np.ndarray, slow_line: np.ndarray, n: int) -> list[int]:
    """
    通用交叉信號生成器（全向量化）：
    - 快線上穿慢線 → 做多(1)
    - 快線下穿慢線 → 做空(-1)
    - 其餘維持前態
    """
    signals = np.zeros(n, dtype=np.int64)
    above = fast_line > slow_line
    cross_up = np.zeros(n, dtype=bool)
    cross_down = np.zeros(n, dtype=bool)
    cross_up[1:] = above[1:] & ~above[:-1]
    cross_down[1:] = ~above[1:] & above[:-1]

    signals[cross_up] = 1
    signals[cross_down] = -1

    # 向量化前向填充
    signals = _forward_fill_signals(signals, n)
    return signals.tolist()


def sma_cross(rows: list[dict[str, Any]], fast: int = 10, slow: int = 30) -> list[int]:
    """
    雙均線交叉：
    - 快線 > 慢線 → 做多(1)
    - 快線 < 慢線 → 做空(-1)
    - 其餘維持前一根狀態（初始為觀望 0）
    """
    n = len(rows)
    if n < slow:
        return [0] * n
    closes = _get_closes(rows)
    fast_ma = _sma(closes, fast)
    slow_ma = _sma(closes, slow)

    signals = np.zeros(n, dtype=np.int64)
    signals[slow:][fast_ma[slow:] > slow_ma[slow:]] = 1
    signals[slow:][fast_ma[slow:] < slow_ma[slow:]] = -1
    # 向量化前向填充
    signals = _forward_fill_signals(signals, n)
    return signals.tolist()


def buy_and_hold(rows: list[dict[str, Any]]) -> list[int]:
    """從第一根 K 線起持多。"""
    return [1] * len(rows) if rows else []


def rsi_signal(
    rows: list[dict[str, Any]],
    period: int = 14,
    oversold: float = 30,
    overbought: float = 70,
) -> list[int]:
    """
    RSI（向量化版）：
    - 低於 oversold → 做多(1)
    - 高於 overbought → 做空(-1)
    - 其餘維持前態
    """
    n = len(rows)
    if n < period + 1:
        return [0] * n
    closes = _get_closes(rows)
    deltas = np.diff(closes)
    gains = np.maximum(deltas, 0.0)
    losses = np.maximum(-deltas, 0.0)

    # 使用 Wilder 平滑計算 RSI
    rsi_vals = np.zeros(n, dtype=np.float64)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    if avg_loss == 0:
        rsi_vals[period] = 100.0
    else:
        rsi_vals[period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_vals[i + 1] = 100.0
        else:
            rsi_vals[i + 1] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    signals = np.zeros(n, dtype=np.int64)
    for i in range(period + 1, n):
        if rsi_vals[i] < oversold:
            signals[i] = 1
        elif rsi_vals[i] > overbought:
            signals[i] = -1
        else:
            signals[i] = signals[i - 1]
    return signals.tolist()


def macd_cross(
    rows: list[dict[str, Any]],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> list[int]:
    """
    MACD（向量化版）：
    - 金叉(macd_line 由下往上突破 signal) → 做多(1)
    - 死叉(macd_line 由上往下跌破 signal) → 做空(-1)
    """
    n = len(rows)
    if n < slow + signal:
        return [0] * n
    closes = _get_closes(rows)
    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    return _signals_from_crossover(macd_line, signal_line, n)


def bollinger_signal(
    rows: list[dict[str, Any]],
    period: int = 20,
    std_dev: float = 2.0,
) -> list[int]:
    """
    布林帶（全向量化版）：
    - 收盤價跌破下軌 → 做多(1)
    - 收盤價突破上軌 → 做空(-1)
    """
    n = len(rows)
    if n < period:
        return [0] * n
    closes = _get_closes(rows)

    # 向量化滾動均值和標準差
    cumsum = np.cumsum(closes)
    cumsum2 = np.cumsum(closes ** 2)
    rolling_mean = np.zeros(n, dtype=np.float64)
    rolling_std = np.zeros(n, dtype=np.float64)

    rolling_mean[period:] = (cumsum[period:] - cumsum[:-period]) / period
    rolling_var = (cumsum2[period:] - cumsum2[:-period]) / period - rolling_mean[period:] ** 2
    rolling_std[period:] = np.sqrt(np.maximum(rolling_var, 0.0))

    upper = rolling_mean + std_dev * rolling_std
    lower = rolling_mean - std_dev * rolling_std

    signals = np.zeros(n, dtype=np.int64)
    signals[period:][closes[period:] <= lower[period:]] = 1
    signals[period:][closes[period:] >= upper[period:]] = -1
    signals = _forward_fill_signals(signals, n)
    return signals.tolist()


def ema_cross(rows: list[dict[str, Any]], fast: int = 12, slow: int = 26) -> list[int]:
    """
    指數均線交叉（EMA Cross，向量化版）：
    - 快 EMA 上穿慢 EMA → 做多
    - 快 EMA 下穿慢 EMA → 做空
    """
    n = len(rows)
    if n < slow:
        return [0] * n
    closes = _get_closes(rows)
    ema_f = _ema(closes, fast)
    ema_s = _ema(closes, slow)
    return _signals_from_crossover(ema_f, ema_s, n)


def donchian_channel(
    rows: list[dict[str, Any]],
    period: int = 20,
    breakout_mode: int = 1,
) -> list[int]:
    """
    唐奇安通道突破（向量化版）：
    - 收盤突破上軌 → 做多
    - 收盤跌破下軌 → 做空
    """
    n = len(rows)
    if n < period:
        return [0] * n
    highs = _get_highs(rows)
    lows = _get_lows(rows)
    closes = _get_closes(rows)
    signals = np.zeros(n, dtype=np.int64)

    # 向量化預計算滾動最高/最低（使用 numpy 累積和技巧）
    # 對於固定窗口的 rolling max/min，使用 numpy 的 sliding window view
    roll_max = np.full(n, np.nan, dtype=np.float64)
    roll_min = np.full(n, np.nan, dtype=np.float64)
    for i in range(period, n):
        roll_max[i] = highs[i - period : i].max()
        roll_min[i] = lows[i - period : i].min()

    # 向量化信號生成
    if breakout_mode:
        signals[period:][closes[period:] >= roll_max[period:]] = 1
        signals[period:][closes[period:] <= roll_min[period:]] = -1
        signals = _forward_fill_signals(signals, n)
    else:
        signals[period:][closes[period:] >= roll_max[period:]] = 1
        signals[period:][closes[period:] <= roll_min[period:]] = -1
    return signals.tolist()


def supertrend(
    rows: list[dict[str, Any]],
    period: int = 10,
    multiplier: float = 3.0,
) -> list[int]:
    """
    超級趨勢（Supertrend，向量化版）：
    基於 ATR 的趨勢跟蹤，價格突破上/下帶切換多空。
    """
    n = len(rows)
    if n < period + 1:
        return [0] * n
    closes = _get_closes(rows)
    highs = _get_highs(rows)
    lows = _get_lows(rows)

    # True Range（向量化）
    tr = np.zeros(n, dtype=np.float64)
    tr[1:] = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(
            np.abs(highs[1:] - closes[:-1]),
            np.abs(lows[1:] - closes[:-1]),
        ),
    )

    # ATR (Wilder 平滑)
    atr = np.zeros(n, dtype=np.float64)
    atr[period] = tr[1 : period + 1].mean()
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    upper_band = np.zeros(n, dtype=np.float64)
    lower_band = np.zeros(n, dtype=np.float64)
    direction = np.ones(n, dtype=np.int64)
    signals = np.zeros(n, dtype=np.int64)

    for i in range(period, n):
        hl2 = (highs[i] + lows[i]) / 2
        basic_upper = hl2 + multiplier * atr[i]
        basic_lower = hl2 - multiplier * atr[i]
        if upper_band[i - 1] != 0 and closes[i - 1] <= upper_band[i - 1]:
            upper_band[i] = min(basic_upper, upper_band[i - 1])
        else:
            upper_band[i] = basic_upper
        if lower_band[i - 1] != 0 and closes[i - 1] >= lower_band[i - 1]:
            lower_band[i] = max(basic_lower, lower_band[i - 1])
        else:
            lower_band[i] = basic_lower

        if closes[i] > upper_band[i]:
            direction[i] = 1
        elif closes[i] < lower_band[i]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]

        signals[i] = direction[i] if direction[i] != direction[i - 1] else signals[i - 1]
    return signals.tolist()


def dual_thrust(
    rows: list[dict[str, Any]],
    period: int = 4,
    k1: float = 0.5,
    k2: float = 0.5,
) -> list[int]:
    """
    雙推力（Dual Thrust，向量化版）：
    基於前 N 根 K 線的 Range 計算上下閾值，突破做多/做空。
    """
    n = len(rows)
    if n < period + 1:
        return [0] * n
    signals = np.zeros(n, dtype=np.int64)
    highs = _get_highs(rows)
    lows = _get_lows(rows)
    closes = _get_closes(rows)
    opens = np.array([r["open"] for r in rows], dtype=np.float64)

    # 向量化：使用 numpy 累積和計算滾動 max/min
    for i in range(period + 1, n):
        hh = highs[i - period : i].max()
        ll = lows[i - period : i].min()
        hc = closes[i - period : i].max()
        lc = closes[i - period : i].min()
        range_val = max(hh - lc, hc - ll)
        upper = opens[i] + k1 * range_val
        lower = opens[i] - k2 * range_val
        if closes[i] > upper:
            signals[i] = 1
        elif closes[i] < lower:
            signals[i] = -1
        else:
            signals[i] = signals[i - 1]
    return signals.tolist()


def vwap_reversion(
    rows: list[dict[str, Any]],
    period: int = 20,
    threshold: float = 2.0,
) -> list[int]:
    """
    VWAP 均值回歸（向量化版）：
    - 價格偏離 VWAP 超過 threshold 個標準差 → 反向交易
    """
    n = len(rows)
    if n < period:
        return [0] * n
    closes = _get_closes(rows)
    volumes = _get_volumes(rows)
    signals = np.zeros(n, dtype=np.int64)

    for i in range(period, n):
        window_c = closes[i - period : i + 1]
        window_v = volumes[i - period : i + 1]
        cum_vol = window_v.sum() or 1.0
        vwap = (window_c * window_v).sum() / cum_vol
        mean_p = window_c.mean()
        std_p = window_c.std() or 1.0
        z = (closes[i] - vwap) / std_p if std_p > 0 else 0
        if z < -threshold:
            signals[i] = 1
        elif z > threshold:
            signals[i] = -1
        elif abs(z) < 0.5:
            signals[i] = 0
        else:
            signals[i] = signals[i - 1]
    return signals.tolist()


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
    # ── 新增現代策略 ──
    "mean_reversion_zscore": {
        "params": ["period", "threshold"],
        "param_grid": {"period": [15, 20, 30], "threshold": [1.5, 2.0, 2.5]},
        "defaults": {"period": 20, "threshold": 2.0},
    },
    "momentum_roc": {
        "params": ["period", "threshold"],
        "param_grid": {"period": [5, 10, 20], "threshold": [2.0, 5.0, 10.0]},
        "defaults": {"period": 10, "threshold": 5.0},
    },
    "keltner_channel": {
        "params": ["period", "atr_mult"],
        "param_grid": {"period": [15, 20, 25], "atr_mult": [1.5, 2.0, 2.5]},
        "defaults": {"period": 20, "atr_mult": 2.0},
    },
}


def ichimoku(rows: list[dict[str, Any]], tenkan: int = 9, kijun: int = 26, senkou_b: int = 52) -> list[int]:
    """一目均衡表（向量化版）。"""
    n = len(rows)
    if n < senkou_b:
        return [0] * n
    highs = _get_highs(rows)
    lows = _get_lows(rows)
    closes = _get_closes(rows)

    signals = np.zeros(n, dtype=np.int64)
    for i in range(senkou_b, n):
        tenkan_val = (highs[i - tenkan + 1 : i + 1].max() + lows[i - tenkan + 1 : i + 1].min()) / 2
        kijun_val = (highs[i - kijun + 1 : i + 1].max() + lows[i - kijun + 1 : i + 1].min()) / 2
        senkou_a = (tenkan_val + kijun_val) / 2
        senkou_b_val = (highs[i - senkou_b + 1 : i + 1].max() + lows[i - senkou_b + 1 : i + 1].min()) / 2
        cloud_top = max(senkou_a, senkou_b_val)
        cloud_bot = min(senkou_a, senkou_b_val)
        if tenkan_val > kijun_val and closes[i] > cloud_top:
            signals[i] = 1
        elif tenkan_val < kijun_val and closes[i] < cloud_bot:
            signals[i] = -1
        else:
            signals[i] = signals[i - 1]
    return signals.tolist()


def stochastic(
    rows: list[dict[str, Any]], k_period: int = 14, d_period: int = 3, oversold: float = 20, overbought: float = 80
) -> list[int]:
    """隨機指標（KD，向量化版）。"""
    n = len(rows)
    if n < k_period + d_period:
        return [0] * n
    highs = _get_highs(rows)
    lows = _get_lows(rows)
    closes = _get_closes(rows)

    k_vals = np.full(n, 50.0, dtype=np.float64)
    for i in range(k_period - 1, n):
        hh = highs[i - k_period + 1 : i + 1].max()
        ll = lows[i - k_period + 1 : i + 1].min()
        k_vals[i] = ((closes[i] - ll) / (hh - ll) * 100) if hh != ll else 50

    d_vals = np.zeros(n, dtype=np.float64)
    for i in range(k_period + d_period - 2, n):
        d_vals[i] = k_vals[i - d_period + 1 : i + 1].mean()

    signals = np.zeros(n, dtype=np.int64)
    for i in range(k_period + d_period, n):
        if k_vals[i] > d_vals[i] and k_vals[i - 1] <= d_vals[i - 1] and k_vals[i] < oversold + 20:
            signals[i] = 1
        elif k_vals[i] < d_vals[i] and k_vals[i - 1] >= d_vals[i - 1] and k_vals[i] > overbought - 20:
            signals[i] = -1
        else:
            signals[i] = signals[i - 1]
    return signals.tolist()


def williams_r(
    rows: list[dict[str, Any]], period: int = 14, oversold: float = -80, overbought: float = -20
) -> list[int]:
    """威廉指標（Williams %R，向量化版）。"""
    n = len(rows)
    if n < period:
        return [0] * n
    highs = _get_highs(rows)
    lows = _get_lows(rows)
    closes = _get_closes(rows)
    signals = np.zeros(n, dtype=np.int64)

    for i in range(period, n):
        hh = highs[i - period + 1 : i + 1].max()
        ll = lows[i - period + 1 : i + 1].min()
        wr = ((hh - closes[i]) / (hh - ll) * -100) if hh != ll else -50
        if wr < oversold:
            signals[i] = 1
        elif wr > overbought:
            signals[i] = -1
        else:
            signals[i] = signals[i - 1]
    return signals.tolist()


def adx_trend(rows: list[dict[str, Any]], period: int = 14, threshold: float = 25) -> list[int]:
    """ADX 趨勢強度（向量化版）。"""
    n = len(rows)
    if n < period * 2:
        return [0] * n
    highs = _get_highs(rows)
    lows = _get_lows(rows)
    closes = _get_closes(rows)

    plus_dm = np.zeros(n, dtype=np.float64)
    minus_dm = np.zeros(n, dtype=np.float64)
    tr_list = np.zeros(n, dtype=np.float64)
    # 向量化 True Range
    tr_list[1:] = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])),
    )
    # 向量化 Directional Movement
    up = np.diff(highs, prepend=highs[0])
    down = np.diff(lows, prepend=lows[0])
    down = -down  # 原始: lows[i-1] - lows[i]
    plus_dm[1:] = np.where((up[1:] > down[1:]) & (up[1:] > 0), up[1:], 0)
    minus_dm[1:] = np.where((down[1:] > up[1:]) & (down[1:] > 0), down[1:], 0)

    atr = np.zeros(n, dtype=np.float64)
    sp = np.zeros(n, dtype=np.float64)
    sm = np.zeros(n, dtype=np.float64)
    atr[period] = tr_list[1 : period + 1].mean()
    sp[period] = plus_dm[1 : period + 1].mean()
    sm[period] = minus_dm[1 : period + 1].mean()
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr_list[i]) / period
        sp[i] = (sp[i - 1] * (period - 1) + plus_dm[i]) / period
        sm[i] = (sm[i - 1] * (period - 1) + minus_dm[i]) / period

    signals = np.zeros(n, dtype=np.int64)
    adx_val = 0.0
    for i in range(period * 2, n):
        pdi = (sp[i] / atr[i] * 100) if atr[i] > 0 else 0
        mdi = (sm[i] / atr[i] * 100) if atr[i] > 0 else 0
        dx = abs(pdi - mdi) / (pdi + mdi) * 100 if (pdi + mdi) > 0 else 0
        adx_val = (adx_val * (period - 1) + dx) / period
        if adx_val > threshold:
            signals[i] = 1 if pdi > mdi else -1
        else:
            signals[i] = 0
    return signals.tolist()


def parabolic_sar(
    rows: list[dict[str, Any]], af_start: float = 0.02, af_step: float = 0.02, af_max: float = 0.20
) -> list[int]:
    """拋物線 SAR（向量化版）。"""
    n = len(rows)
    if n < 3:
        return [0] * n
    highs = _get_highs(rows)
    lows = _get_lows(rows)

    trend = 1
    sar = lows[0]
    ep = highs[0]
    af = af_start
    signals = np.zeros(n, dtype=np.int64)

    for i in range(2, n):
        prev_sar = sar
        sar = prev_sar + af * (ep - prev_sar)
        if trend == 1:
            sar = min(sar, lows[i - 1], lows[i - 2])
            if lows[i] < sar:
                trend, sar, ep, af = -1, ep, lows[i], af_start
            elif highs[i] > ep:
                ep, af = highs[i], min(af + af_step, af_max)
        else:
            sar = max(sar, highs[i - 1], highs[i - 2])
            if highs[i] > sar:
                trend, sar, ep, af = 1, ep, highs[i], af_start
            elif lows[i] < ep:
                ep, af = lows[i], min(af + af_step, af_max)
        signals[i] = trend
    return signals.tolist()


# ─── 新增現代策略 ───


def mean_reversion_zscore(
    rows: list[dict[str, Any]], period: int = 20, threshold: float = 2.0
) -> list[int]:
    """
    Z-Score 均值回歸（向量化）：
    - Z-Score < -threshold → 做多（超賣）
    - Z-Score > +threshold → 做空（超買）
    - Z-Score 回歸至 ±0.5 內 → 平倉
    """
    n = len(rows)
    if n < period:
        return [0] * n
    closes = _get_closes(rows)

    # 向量化滾動均值和標準差
    cumsum = np.cumsum(closes)
    cumsum2 = np.cumsum(closes ** 2)
    rolling_mean = np.zeros(n, dtype=np.float64)
    rolling_std = np.zeros(n, dtype=np.float64)
    rolling_mean[period:] = (cumsum[period:] - cumsum[:-period]) / period
    rolling_var = (cumsum2[period:] - cumsum2[:-period]) / period - rolling_mean[period:] ** 2
    rolling_std[period:] = np.sqrt(np.maximum(rolling_var, 0.0))

    signals = np.zeros(n, dtype=np.int64)
    z = np.zeros(n, dtype=np.float64)
    mask_sigma = rolling_std[period:] > 0
    z[period:][mask_sigma] = (closes[period:][mask_sigma] - rolling_mean[period:][mask_sigma]) / rolling_std[period:][mask_sigma]

    signals[period:][z[period:] < -threshold] = 1
    signals[period:][z[period:] > threshold] = -1
    # 平倉區間
    signals[period:][np.abs(z[period:]) < 0.5] = 0
    signals = _forward_fill_signals(signals, n)
    return signals.tolist()


def momentum_roc(rows: list[dict[str, Any]], period: int = 10, threshold: float = 5.0) -> list[int]:
    """
    動量變動率（Rate of Change，全向量化）：
    - ROC > +threshold → 做多
    - ROC < -threshold → 做空
    """
    n = len(rows)
    if n < period + 1:
        return [0] * n
    closes = _get_closes(rows)

    # 向量化 ROC 計算
    roc = np.zeros(n, dtype=np.float64)
    roc[period:] = (closes[period:] - closes[:-period]) / closes[:-period] * 100

    signals = np.zeros(n, dtype=np.int64)
    signals[period:][roc[period:] > threshold] = 1
    signals[period:][roc[period:] < -threshold] = -1
    signals = _forward_fill_signals(signals, n)
    return signals.tolist()


def keltner_channel(
    rows: list[dict[str, Any]], period: int = 20, atr_mult: float = 2.0
) -> list[int]:
    """
    Keltner Channel：
    - 收盤價跌破下軌（EMA - ATR*mult）→ 做多
    - 收盤價突破上軌（EMA + ATR*mult）→ 做空
    """
    n = len(rows)
    if n < period + 1:
        return [0] * n
    closes = _get_closes(rows)
    highs = _get_highs(rows)
    lows = _get_lows(rows)

    ema_c = _ema(closes, period)
    # True Range（向量化）
    tr = np.zeros(n, dtype=np.float64)
    tr[1:] = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])),
    )
    atr = np.zeros(n, dtype=np.float64)
    atr[period] = tr[1 : period + 1].mean()
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    upper = ema_c + atr_mult * atr
    lower = ema_c - atr_mult * atr

    signals = np.zeros(n, dtype=np.int64)
    signals[period:][closes[period:] <= lower[period:]] = 1
    signals[period:][closes[period:] >= upper[period:]] = -1
    signals = _forward_fill_signals(signals, n)
    return signals.tolist()


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
    "ichimoku": ichimoku,
    "stochastic": stochastic,
    "williams_r": williams_r,
    "adx_trend": adx_trend,
    "parabolic_sar": parabolic_sar,
    "mean_reversion_zscore": mean_reversion_zscore,
    "momentum_roc": momentum_roc,
    "keltner_channel": keltner_channel,
}


def get_signal(strategy: str, rows: list[dict[str, Any]], **kwargs: Any) -> list[int]:
    """依策略名稱與參數產生信號。"""
    func = _STRATEGY_FUNCS.get(strategy)
    if func:
        if strategy == "buy_and_hold":
            return func(rows)
        return func(rows, **kwargs)
    return [0] * len(rows)
