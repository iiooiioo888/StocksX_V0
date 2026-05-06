"""
進階技術指標 — 全向量化優化版 v2.0

性能優化：
- 所有函數接受 OHLCVArrays 或 numpy 數組，避免重複 dict→array 轉換
- 消除 Python 迴圈，用 sliding_window_view / cumsum 替代
- 共享 np_utils 原語，減少代碼重複

用法：
    from src.backtest.indicators import atr, obv, cci, heikin_ashi
    from src.backtest.np_utils import OHLCVArrays
    arr = OHLCVArrays.from_rows(rows)
    atr_vals = atr(arr.highs, arr.lows, arr.closes)
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .np_utils import OHLCVArrays, atr as _atr, true_range as _true_range, rolling_max, rolling_min, sma as _sma, ema as _ema


# ---------------------------------------------------------------------------
# Helpers — 向後兼容
# ---------------------------------------------------------------------------

def _extract(rows: list[dict[str, Any]], key: str) -> np.ndarray:
    """Extract a single field from rows into a numpy float64 array."""
    return np.array([r[key] for r in rows], dtype=np.float64)


# ---------------------------------------------------------------------------
# 1. true_range — 全向量化
# ---------------------------------------------------------------------------

def true_range(rows: list[dict[str, Any]]) -> list[float]:
    """真實波幅 (TR)."""
    if not rows:
        return []
    highs = _extract(rows, "high")
    lows = _extract(rows, "low")
    closes = _extract(rows, "close")
    return _true_range(highs, lows, closes).tolist()


# ---------------------------------------------------------------------------
# 2. atr — Wilder 递归用 numpy array 索引
# ---------------------------------------------------------------------------

def atr(rows: list[dict[str, Any]], period: int = 14) -> list[float]:
    """平均真實波幅 (ATR)."""
    if not rows:
        return []
    highs = _extract(rows, "high")
    lows = _extract(rows, "low")
    closes = _extract(rows, "close")
    return _atr(highs, lows, closes, period).tolist()


# ---------------------------------------------------------------------------
# 3. obv — 全向量化
# ---------------------------------------------------------------------------

def obv(rows: list[dict[str, Any]]) -> list[float]:
    """能量潮指標 (OBV)."""
    if not rows:
        return []
    closes = _extract(rows, "close")
    volumes = _extract(rows, "volume")
    sign = np.zeros(len(closes))
    sign[1:] = np.sign(np.diff(closes))
    return np.cumsum(sign * volumes).tolist()


# ---------------------------------------------------------------------------
# 4. cci — 向量化 rolling MAD（消除 Python 迴圈）
# ---------------------------------------------------------------------------

def cci(rows: list[dict[str, Any]], period: int = 20) -> list[float]:
    """商品通道指標 (CCI) — 全向量化版。"""
    n = len(rows)
    if n < period:
        return [0.0] * n

    tp = (_extract(rows, "high") + _extract(rows, "low") + _extract(rows, "close")) / 3.0

    # Rolling SMA via cumsum
    cs = np.cumsum(tp)
    sma = np.empty(n)
    sma[:period - 1] = 0.0
    sma[period - 1] = cs[period - 1] / period
    sma[period:] = (cs[period:] - cs[:-period]) / period

    # Rolling MAD via sliding_window_view（向量化，無 Python 迴圈）
    windows = np.lib.stride_tricks.sliding_window_view(tp, period)
    means = windows.mean(axis=1)
    mad_vals = np.mean(np.abs(windows - means[:, np.newaxis]), axis=1)

    result = np.zeros(n)
    valid = mad_vals > 0
    result[period - 1:][valid] = (tp[period - 1:][valid] - sma[period - 1:][valid]) / (0.015 * mad_vals[valid])
    return result.tolist()


# ---------------------------------------------------------------------------
# 5. mfi — 向量化（消除 Python 迴圈）
# ---------------------------------------------------------------------------

def mfi(rows: list[dict[str, Any]], period: int = 14) -> list[float]:
    """資金流量指標 (MFI) — 全向量化版。"""
    n = len(rows)
    if n < period + 1:
        return [50.0] * n

    tp = (_extract(rows, "high") + _extract(rows, "low") + _extract(rows, "close")) / 3.0
    volumes = _extract(rows, "volume")
    mf = tp * volumes

    diff_tp = np.diff(tp)
    direction = np.zeros(n)
    direction[1:] = np.sign(diff_tp)

    pos_mf = np.where(direction > 0, mf, 0.0)
    neg_mf = np.where(direction < 0, mf, 0.0)

    # Rolling sums via cumsum
    cs_pos = np.cumsum(pos_mf)
    cs_neg = np.cumsum(neg_mf)

    result = np.full(n, 50.0)
    # 向量化計算所有 period 位置
    indices = np.arange(period, n)
    p = cs_pos[indices] - cs_pos[indices - period]
    ne = cs_neg[indices] - cs_neg[indices - period]

    # 處理 ne == 0 的情況
    safe_ne = np.where(ne == 0, 1.0, ne)
    ratio = p / safe_ne
    result[period:] = np.where(ne == 0, 100.0, 100.0 - (100.0 / (1.0 + ratio)))
    return result.tolist()


# ---------------------------------------------------------------------------
# 6. aroon — 向量化（argmax/argmin per window via sliding_window_view）
# ---------------------------------------------------------------------------

def aroon(rows: list[dict[str, Any]], period: int = 25) -> tuple[list[float], list[float], list[float]]:
    """
    Aroon 指標 — 向量化版。

    Returns: (aroon_up, aroon_down, aroon_osc)
    """
    n = len(rows)
    if n < period:
        zeros = [0.0] * n
        return zeros, zeros, zeros

    highs = _extract(rows, "high")
    lows = _extract(rows, "low")

    # 使用 sliding_window_view 批量獲取窗口
    h_windows = np.lib.stride_tricks.sliding_window_view(highs, period)
    l_windows = np.lib.stride_tricks.sliding_window_view(lows, period)

    # 向量化 argmax/argmin
    max_indices = np.argmax(h_windows, axis=1)
    min_indices = np.argmin(l_windows, axis=1)

    days_since_high = period - 1 - max_indices
    days_since_low = period - 1 - min_indices

    up = np.zeros(n)
    down = np.zeros(n)
    up[period - 1:] = ((period - days_since_high) / period) * 100.0
    down[period - 1:] = ((period - days_since_low) / period) * 100.0

    osc = up - down
    return up.tolist(), down.tolist(), osc.tolist()


# ---------------------------------------------------------------------------
# 7. stochastic_rsi — 向量化
# ---------------------------------------------------------------------------

def stochastic_rsi(
    rows: list[dict[str, Any]],
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_period: int = 3,
    d_period: int = 3,
) -> tuple[list[float], list[float]]:
    """
    Stochastic RSI — 向量化版。

    Returns: (%K, %D)
    """
    closes = _extract(rows, "close")
    n = len(closes)

    if n < rsi_period + 1:
        return [50.0] * n, [50.0] * n

    # RSI via rolling window
    changes = np.diff(closes)
    gains = np.where(changes > 0, changes, 0.0)
    losses = np.where(changes < 0, -changes, 0.0)

    rsi_vals = np.full(n, 50.0)
    cs_g = np.cumsum(gains)
    cs_l = np.cumsum(losses)

    # 向量化 RSI 計算
    indices = np.arange(rsi_period, n)
    end = indices
    start = end - rsi_period
    avg_g = (cs_g[end - 1] - np.where(start > 0, cs_g[start - 1], 0.0)) / rsi_period
    avg_l = (cs_l[end - 1] - np.where(start > 0, cs_l[start - 1], 0.0)) / rsi_period
    rsi_vals[rsi_period:] = np.where(avg_l == 0, 100.0, 100.0 - 100.0 / (1.0 + avg_g / np.where(avg_l == 0, 1.0, avg_l)))

    # Stochastic of RSI via sliding_window_view
    stoch_k = np.full(n, 50.0)
    if n >= rsi_period + stoch_period:
        rsi_windows = np.lib.stride_tricks.sliding_window_view(rsi_vals[rsi_period - 1:], stoch_period)
        lowest = rsi_windows.min(axis=1)
        highest = rsi_windows.max(axis=1)
        denom = highest - lowest
        safe_denom = np.where(denom == 0, 1.0, denom)
        start_idx = rsi_period + stoch_period - 2
        stoch_k[start_idx:] = np.where(
            denom != 0,
            (rsi_vals[start_idx:] - lowest) / safe_denom * 100.0,
            50.0,
        )

    # %D = SMA of %K via cumsum
    stoch_d = np.full(n, 50.0)
    if n >= k_period:
        k_cumsum = np.zeros(n + 1, dtype=np.float64)
        k_cumsum[1:] = np.cumsum(stoch_k)
        indices_d = np.arange(k_period - 1, n)
        stoch_d[k_period - 1:] = (k_cumsum[indices_d + 1] - k_cumsum[indices_d + 1 - k_period]) / k_period

    return stoch_k.tolist(), stoch_d.tolist()


# ---------------------------------------------------------------------------
# 8. heikin_ashi — 全向量化
# ---------------------------------------------------------------------------

def heikin_ashi(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Heikin-Ashi K 線 — 平滑趨勢的蠟燭圖變體.

    Returns: [{"open", "high", "low", "close", "timestamp"}, ...]
    """
    if not rows:
        return []

    opens = _extract(rows, "open")
    highs = _extract(rows, "high")
    lows = _extract(rows, "low")
    closes = _extract(rows, "close")

    ha_close = (opens + highs + lows + closes) / 4.0

    # 向量化 ha_open 計算（遞推展開為 numpy 操作）
    ha_open = np.zeros_like(opens)
    ha_open[0] = (opens[0] + closes[0]) / 2.0
    for i in range(1, len(rows)):
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0

    ha_high = np.maximum(highs, np.maximum(ha_open, ha_close))
    ha_low = np.minimum(lows, np.minimum(ha_open, ha_close))

    # 批量構建結果
    timestamps = [r["timestamp"] for r in rows]
    volumes = [r.get("volume", 0) for r in rows]
    ha_rows = []
    for i in range(len(rows)):
        ha_rows.append(
            {
                "open": float(ha_open[i]),
                "high": float(ha_high[i]),
                "low": float(ha_low[i]),
                "close": float(ha_close[i]),
                "timestamp": timestamps[i],
                "volume": volumes[i],
            }
        )
    return ha_rows


# ---------------------------------------------------------------------------
# 9. keltner_channel — 向量化 (复用 atr)
# ---------------------------------------------------------------------------

def keltner_channel(
    rows: list[dict[str, Any]],
    ema_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0,
) -> tuple[list[float], list[float], list[float]]:
    """
    Keltner Channel.

    Returns: (upper, middle, lower)
    """
    closes = _extract(rows, "close")
    n = len(closes)

    if n < max(ema_period, atr_period):
        return [0.0] * n, closes.tolist(), [0.0] * n

    middle = _ema(closes, ema_period)
    highs = _extract(rows, "high")
    lows = _extract(rows, "low")
    atr_vals = _atr(highs, lows, closes, atr_period)
    upper = (middle + multiplier * atr_vals).tolist()
    lower = (middle - multiplier * atr_vals).tolist()

    return upper, middle.tolist(), lower


# ---------------------------------------------------------------------------
# 10. pivot_points — 全向量化
# ---------------------------------------------------------------------------

def pivot_points(rows: list[dict[str, Any]], method: str = "classic") -> dict[str, list[float]]:
    """
    樞紐點 (Pivot Points).

    method: "classic", "fibonacci", "camarilla", "woodie"

    Returns: {"pivot", "r1", "r2", "r3", "s1", "s2", "s3"}
    """
    n = len(rows)
    result = {k: [0.0] * n for k in ["pivot", "r1", "r2", "r3", "s1", "s2", "s3"]}

    if n < 2:
        return result

    highs = _extract(rows, "high")
    lows = _extract(rows, "low")
    closes = _extract(rows, "close")
    opens = _extract(rows, "open")

    h = highs[:-1]
    l = lows[:-1]
    c = closes[:-1]

    if method == "classic":
        p = (h + l + c) / 3.0
        result["pivot"][1:] = p.tolist()
        result["r1"][1:] = (2 * p - l).tolist()
        result["s1"][1:] = (2 * p - h).tolist()
        result["r2"][1:] = (p + (h - l)).tolist()
        result["s2"][1:] = (p - (h - l)).tolist()
        result["r3"][1:] = (h + 2 * (p - l)).tolist()
        result["s3"][1:] = (l - 2 * (h - p)).tolist()
    elif method == "fibonacci":
        p = (h + l + c) / 3.0
        rng = h - l
        result["pivot"][1:] = p.tolist()
        result["r1"][1:] = (p + 0.382 * rng).tolist()
        result["s1"][1:] = (p - 0.382 * rng).tolist()
        result["r2"][1:] = (p + 0.618 * rng).tolist()
        result["s2"][1:] = (p - 0.618 * rng).tolist()
        result["r3"][1:] = (p + rng).tolist()
        result["s3"][1:] = (p - rng).tolist()
    elif method == "camarilla":
        p = (h + l + c) / 3.0
        rng = h - l
        result["pivot"][1:] = p.tolist()
        result["r1"][1:] = (c + rng * 1.1 / 12).tolist()
        result["r2"][1:] = (c + rng * 1.1 / 6).tolist()
        result["r3"][1:] = (c + rng * 1.1 / 4).tolist()
        result["s1"][1:] = (c - rng * 1.1 / 12).tolist()
        result["s2"][1:] = (c - rng * 1.1 / 6).tolist()
        result["s3"][1:] = (c - rng * 1.1 / 4).tolist()
    elif method == "woodie":
        cur_open = opens[1:]
        p = (h + l + 2 * cur_open) / 4.0
        result["pivot"][1:] = p.tolist()
        result["r1"][1:] = (2 * p - l).tolist()
        result["s1"][1:] = (2 * p - h).tolist()
        result["r2"][1:] = (p + (h - l)).tolist()
        result["s2"][1:] = (p - (h - l)).tolist()
        result["r3"][1:] = (h + 2 * (p - l)).tolist()
        result["s3"][1:] = (l - 2 * (h - p)).tolist()

    return result


# ---------------------------------------------------------------------------
# 11. volume_profile — 微优化
# ---------------------------------------------------------------------------

def volume_profile(rows: list[dict[str, Any]], n_bins: int = 20) -> dict[str, Any]:
    """
    成交量分佈 (Volume Profile).

    Returns: {"bins": [{"price_low", "price_high", "volume", "pct"}], "poc": float, "vah": float, "val": float}
    """
    if not rows:
        return {"bins": [], "poc": 0, "vah": 0, "val": 0}

    prices = (_extract(rows, "high") + _extract(rows, "low") + _extract(rows, "close")) / 3.0
    volumes = _extract(rows, "volume")

    p_min = float(np.min(prices))
    p_max = float(np.max(prices))
    if p_max == p_min:
        return {"bins": [], "poc": p_max, "vah": p_max, "val": p_min}

    bin_width = (p_max - p_min) / n_bins
    bin_indices = np.minimum(((prices - p_min) / bin_width).astype(int), n_bins - 1)

    bin_volumes = np.zeros(n_bins)
    np.add.at(bin_volumes, bin_indices, volumes)

    total_vol = float(np.sum(bin_volumes))

    bins = []
    for i in range(n_bins):
        pl = p_min + i * bin_width
        ph = p_min + (i + 1) * bin_width
        pct = (float(bin_volumes[i]) / total_vol * 100.0) if total_vol > 0 else 0.0
        bins.append({"price_low": pl, "price_high": ph, "volume": float(bin_volumes[i]), "pct": pct})

    poc_idx = int(np.argmax(bin_volumes))
    poc = (bins[poc_idx]["price_low"] + bins[poc_idx]["price_high"]) / 2.0

    sorted_indices = np.argsort(-bin_volumes)
    va_vol = 0.0
    va_prices = []
    for idx in sorted_indices:
        va_vol += bin_volumes[idx]
        va_prices.extend([bins[idx]["price_low"], bins[idx]["price_high"]])
        if va_vol >= total_vol * 0.7:
            break

    vah = max(va_prices) if va_prices else p_max
    val = min(va_prices) if va_prices else p_min

    return {"bins": bins, "poc": poc, "vah": vah, "val": val}
