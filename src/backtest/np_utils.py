"""
NumPy 向量化工具集 — 共享高性能計算原語

所有回測引擎和策略共用的底層計算，避免重複實現和重複數組創建。
"""
from __future__ import annotations

from typing import Any

import numpy as np


# ─── 結構化數組緩存 ───

class OHLCVArrays:
    """
    預提取的 OHLCV numpy 數組，避免重複從 dict 列表提取。
    使用方式：
        arr = OHLCVArrays.from_rows(rows)
        closes = arr.closes  # 直接使用，無需重複提取
    """
    __slots__ = ("timestamps", "opens", "highs", "lows", "closes", "volumes", "_n")

    def __init__(
        self,
        timestamps: np.ndarray,
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
    ) -> None:
        self.timestamps = timestamps
        self.opens = opens
        self.highs = highs
        self.lows = lows
        self.closes = closes
        self.volumes = volumes
        self._n = len(closes)

    @classmethod
    def from_rows(cls, rows: list[dict[str, Any]]) -> "OHLCVArrays":
        """從 dict 列表一次性提取所有字段為 numpy 數組。"""
        n = len(rows)
        timestamps = np.empty(n, dtype=np.int64)
        opens = np.empty(n, dtype=np.float64)
        highs = np.empty(n, dtype=np.float64)
        lows = np.empty(n, dtype=np.float64)
        closes = np.empty(n, dtype=np.float64)
        volumes = np.empty(n, dtype=np.float64)
        for i, r in enumerate(rows):
            timestamps[i] = r["timestamp"]
            opens[i] = r["open"]
            highs[i] = r["high"]
            lows[i] = r["low"]
            closes[i] = r["close"]
            volumes[i] = r.get("volume", 0.0)
        return cls(timestamps, opens, highs, lows, closes, volumes)

    @property
    def n(self) -> int:
        return self._n

    def __len__(self) -> int:
        return self._n


# ─── 移動平均 ───

def sma(arr: np.ndarray, period: int) -> np.ndarray:
    """向量化簡單移動平均（cumsum 技巧）。"""
    n = len(arr)
    result = np.zeros(n, dtype=np.float64)
    if n < period:
        return result
    cs = np.cumsum(arr)
    result[period - 1] = cs[period - 1] / period
    result[period:] = (cs[period:] - cs[:-period]) / period
    return result


def ema(arr: np.ndarray, period: int) -> np.ndarray:
    """指數移動平均（向量化初始化 + 遞迴）。"""
    n = len(arr)
    if n == 0:
        return np.zeros(0, dtype=np.float64)
    result = np.zeros(n, dtype=np.float64)
    k = 2.0 / (period + 1)
    alpha = 1.0 - k
    if n >= period:
        result[period - 1] = np.mean(arr[:period])
    else:
        result[0] = arr[0]
        return result
    for i in range(period, n):
        result[i] = k * arr[i] + alpha * result[i - 1]
    return result


# ─── 滾動窗口 ───

def rolling_max(arr: np.ndarray, period: int) -> np.ndarray:
    """向量化滾動最大值（sliding_window_view）。"""
    n = len(arr)
    if n < period:
        return np.full(n, np.nan, dtype=np.float64)
    result = np.full(n, np.nan, dtype=np.float64)
    windows = np.lib.stride_tricks.sliding_window_view(arr, period)
    result[period - 1:] = windows.max(axis=1)
    return result


def rolling_min(arr: np.ndarray, period: int) -> np.ndarray:
    """向量化滾動最小值（sliding_window_view）。"""
    n = len(arr)
    if n < period:
        return np.full(n, np.nan, dtype=np.float64)
    result = np.full(n, np.nan, dtype=np.float64)
    windows = np.lib.stride_tricks.sliding_window_view(arr, period)
    result[period - 1:] = windows.min(axis=1)
    return result


def rolling_sum(arr: np.ndarray, period: int) -> np.ndarray:
    """向量化滾動求和（cumsum 技巧）。"""
    n = len(arr)
    result = np.zeros(n, dtype=np.float64)
    if n < period:
        return result
    cs = np.cumsum(arr)
    result[period - 1] = cs[period - 1]
    result[period:] = cs[period:] - cs[:-period]
    return result


def rolling_std(arr: np.ndarray, period: int) -> np.ndarray:
    """向量化滾動標準差。"""
    n = len(arr)
    result = np.zeros(n, dtype=np.float64)
    if n < period:
        return result
    cs = np.cumsum(arr)
    cs2 = np.cumsum(arr ** 2)
    mean = np.zeros(n, dtype=np.float64)
    mean[period - 1] = cs[period - 1] / period
    mean[period:] = (cs[period:] - cs[:-period]) / period
    var = np.zeros(n, dtype=np.float64)
    var[period - 1] = cs2[period - 1] / period - mean[period - 1] ** 2
    var[period:] = (cs2[period:] - cs2[:-period]) / period - mean[period:] ** 2
    result[period - 1:] = np.sqrt(np.maximum(var[period - 1:], 0.0))
    return result


# ─── True Range / ATR ───

def true_range(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """向量化 True Range（直接操作數組）。"""
    n = len(highs)
    tr = highs - lows
    if n > 1:
        tr[1:] = np.maximum(
            tr[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1]),
            ),
        )
    return tr


def atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> np.ndarray:
    """平均真實波幅（Wilder 平滑）。"""
    tr = true_range(highs, lows, closes)
    n = len(tr)
    result = np.zeros(n, dtype=np.float64)
    if n < period:
        return result
    result[period - 1] = np.mean(tr[:period])
    for i in range(period, n):
        result[i] = (result[i - 1] * (period - 1) + tr[i]) / period
    return result


# ─── 信號處理 ───

def forward_fill_signals(signals: np.ndarray) -> np.ndarray:
    """向量化前向填充：將 0 替換為上一個非零值。"""
    n = len(signals)
    mask = signals != 0
    idx = np.where(mask, np.arange(n), 0)
    np.maximum.accumulate(idx, out=idx)
    return signals[idx]


def crossover_signals(fast: np.ndarray, slow: np.ndarray) -> np.ndarray:
    """通用交叉信號：快線上穿→1，下穿→-1，其餘前向填充。"""
    n = len(fast)
    signals = np.zeros(n, dtype=np.int64)
    above = fast > slow
    cross_up = np.zeros(n, dtype=bool)
    cross_down = np.zeros(n, dtype=bool)
    cross_up[1:] = above[1:] & ~above[:-1]
    cross_down[1:] = ~above[1:] & above[:-1]
    signals[cross_up] = 1
    signals[cross_down] = -1
    return forward_fill_signals(signals)


# ─── 向量化滾動 MAD（替代 Python 迴圈） ───

def rolling_mad(arr: np.ndarray, period: int) -> np.ndarray:
    """向量化滾動 Mean Absolute Deviation。"""
    n = len(arr)
    result = np.zeros(n, dtype=np.float64)
    if n < period:
        return result
    # 使用 sliding_window_view 批量計算
    windows = np.lib.stride_tricks.sliding_window_view(arr, period)
    means = windows.mean(axis=1)
    result[period - 1:] = np.mean(np.abs(windows - means[:, np.newaxis]), axis=1)
    return result
