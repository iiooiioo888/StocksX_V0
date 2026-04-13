"""
市場狀態檢測引擎 (Regime Detection)
======================================
使用 HMM（隱馬可夫模型）和統計方法識別牛市 / 熊市 / 震盪市

v6.0 新增功能
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np


class MarketRegime(Enum):
    """市場狀態枚舉。"""

    BULL = "bull"  # 牛市：趨勢向上，波動較低
    BEAR = "bear"  # 熊市：趨勢向下，波動較高
    SIDEWAYS = "sideways"  # 震盪：無明顯趨勢


@dataclass
class RegimeResult:
    """市場狀態檢測結果。"""

    current_regime: MarketRegime
    regime_history: list[MarketRegime]
    confidence: float
    bull_probability: float
    bear_probability: float
    sideways_probability: float
    avg_return_by_regime: dict[str, float]
    avg_vol_by_regime: dict[str, float]


def detect_regime_statistical(
    closes: list[float],
    lookback: int = 60,
    short_window: int = 20,
    long_window: int = 60,
    trend_threshold: float = 0.02,
    vol_threshold: float = 0.015,
) -> RegimeResult:
    """
    基於統計特徵的市場狀態檢測（無需額外依賴）。

    判斷邏輯：
    - 牛市：長期趨勢 > trend_threshold 且 波動率 < vol_threshold * 1.5
    - 熊市：長期趨勢 < -trend_threshold 且 波動率 > vol_threshold
    - 震盪：其餘情況

    Args:
        closes: 收盤價序列
        lookback: 回看窗口
        short_window: 短期均線窗口
        long_window: 長期均線窗口
        trend_threshold: 趨勢判斷閾值（年化）
        vol_threshold: 波動率閾值（日）
    """
    arr = np.array(closes, dtype=np.float64)
    n = len(arr)
    if n < long_window:
        return RegimeResult(
            current_regime=MarketRegime.SIDEWAYS,
            regime_history=[MarketRegime.SIDEWAYS] * n,
            confidence=0.0,
            bull_probability=0.33,
            bear_probability=0.33,
            sideways_probability=0.34,
            avg_return_by_regime={},
            avg_vol_by_regime={},
        )

    returns = np.diff(arr) / arr[:-1]
    regimes = [MarketRegime.SIDEWAYS] * long_window

    for i in range(long_window, n):
        # 計算趨勢
        start_idx = max(0, i - lookback)
        trend = (arr[i] - arr[start_idx]) / arr[start_idx]
        ann_trend = trend * (252 / max(i - start_idx, 1))

        # 計算波動率
        window_returns = returns[max(0, i - lookback) : i]
        vol = window_returns.std() if len(window_returns) > 1 else 0

        # 短期 vs 長期均線
        sma_short = arr[max(0, i - short_window) : i].mean()
        sma_long = arr[max(0, i - long_window) : i].mean()
        ma_ratio = (sma_short - sma_long) / sma_long if sma_long > 0 else 0

        # 狀態判斷
        if ann_trend > trend_threshold and ma_ratio > 0.01:
            regime = MarketRegime.BULL
        elif ann_trend < -trend_threshold and ma_ratio < -0.01:
            regime = MarketRegime.BEAR
        else:
            regime = MarketRegime.SIDEWAYS

        regimes.append(regime)

    # 計算各 regime 的統計
    bull_returns, bear_returns, side_returns = [], [], []
    bull_vols, bear_vols, side_vols = [], [], []

    for i in range(long_window, min(n - 1, len(returns))):
        r = returns[i]
        regime = regimes[i]
        vol = np.std(returns[max(0, i - 20) : i + 1]) if i >= 20 else 0
        if regime == MarketRegime.BULL:
            bull_returns.append(r)
            bull_vols.append(vol)
        elif regime == MarketRegime.BEAR:
            bear_returns.append(r)
            bear_vols.append(vol)
        else:
            side_returns.append(r)
            side_vols.append(vol)

    # 當前狀態（最近 lookback 窗口的多數投票）
    recent_regimes = regimes[-lookback:] if len(regimes) >= lookback else regimes
    bull_count = sum(1 for r in recent_regimes if r == MarketRegime.BULL)
    bear_count = sum(1 for r in recent_regimes if r == MarketRegime.BEAR)
    side_count = sum(1 for r in recent_regimes if r == MarketRegime.SIDEWAYS)
    total = len(recent_regimes)

    current = max(recent_regimes, key=lambda r: recent_regimes.count(r))
    confidence = max(bull_count, bear_count, side_count) / total

    return RegimeResult(
        current_regime=current,
        regime_history=regimes,
        confidence=round(confidence, 4),
        bull_probability=round(bull_count / total, 4),
        bear_probability=round(bear_count / total, 4),
        sideways_probability=round(side_count / total, 4),
        avg_return_by_regime={
            "bull": round(float(np.mean(bull_returns) * 252 * 100), 2) if bull_returns else 0.0,
            "bear": round(float(np.mean(bear_returns) * 252 * 100), 2) if bear_returns else 0.0,
            "sideways": round(float(np.mean(side_returns) * 252 * 100), 2) if side_returns else 0.0,
        },
        avg_vol_by_regime={
            "bull": round(float(np.mean(bull_vols) * np.sqrt(252) * 100), 2) if bull_vols else 0.0,
            "bear": round(float(np.mean(bear_vols) * np.sqrt(252) * 100), 2) if bear_vols else 0.0,
            "sideways": round(float(np.mean(side_vols) * np.sqrt(252) * 100), 2) if side_vols else 0.0,
        },
    )


def calculate_volatility_metrics(
    returns: list[float],
    window: int = 20,
) -> dict[str, Any]:
    """
    計算波動率相關指標。

    Returns:
        {
            "current_vol": float,        # 當前波動率（年化）
            "vol_mean": float,           # 歷史平均波動率
            "vol_percentile": float,     # 當前波動率在歷史中的百分位
            "vol_regime": str,           # "low" | "normal" | "high"
            "garch_vol": float,          # EWMA/GARCH 近似波動率
            "vol_trend": str,            # "rising" | "falling" | "stable"
        }
    """
    arr = np.array(returns, dtype=np.float64)
    n = len(arr)
    if n < window:
        return {
            "current_vol": 0.0,
            "vol_mean": 0.0,
            "vol_percentile": 50.0,
            "vol_regime": "normal",
            "garch_vol": 0.0,
            "vol_trend": "stable",
        }

    # 滾動波動率
    rolling_vol = np.zeros(n - window + 1)
    for i in range(len(rolling_vol)):
        rolling_vol[i] = arr[i : i + window].std() * np.sqrt(252)

    current_vol = float(rolling_vol[-1])
    vol_mean = float(rolling_vol.mean())
    vol_percentile = float((rolling_vol < current_vol).mean() * 100)

    # EWMA 波動率（類 GARCH）
    lam = 0.94
    ewma_vol_sq = arr[0] ** 2
    for i in range(1, n):
        ewma_vol_sq = lam * ewma_vol_sq + (1 - lam) * arr[i] ** 2
    garch_vol = float(np.sqrt(ewma_vol_sq * 252))

    # 波動率趨勢
    if len(rolling_vol) >= 10:
        recent_vol = rolling_vol[-10:].mean()
        older_vol = rolling_vol[-20:-10].mean() if len(rolling_vol) >= 20 else rolling_vol[:10].mean()
        if recent_vol > older_vol * 1.1:
            vol_trend = "rising"
        elif recent_vol < older_vol * 0.9:
            vol_trend = "falling"
        else:
            vol_trend = "stable"
    else:
        vol_trend = "stable"

    # 波動率 regime
    if vol_percentile > 75:
        vol_regime = "high"
    elif vol_percentile < 25:
        vol_regime = "low"
    else:
        vol_regime = "normal"

    return {
        "current_vol": round(current_vol * 100, 2),
        "vol_mean": round(vol_mean * 100, 2),
        "vol_percentile": round(vol_percentile, 1),
        "vol_regime": vol_regime,
        "garch_vol": round(garch_vol * 100, 2),
        "vol_trend": vol_trend,
    }
