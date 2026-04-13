"""
形態策略補全 - Batch 2
包含 5 個形態策略

作者：StocksX Team
創建日期：2026-03-22
狀態：✅ 批量生成
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_strategy import BaseStrategy

from src.strategies.base_strategy import BaseStrategy

# ============================================================================
# 1. 鑽石頂/底
# ============================================================================


class DiamondPattern(BaseStrategy):
    """
    鑽石頂/底形態策略

    識別鑽石形態（收斂後擴張），
    突破時交易。
    """

    def __init__(self, lookback: int = 40):
        super().__init__("鑽石頂/底", {"lookback": lookback}, category="pattern")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params["lookback"]

        high = data["high"]
        low = data["low"]

        # 簡化：檢測波動率先收斂後擴張
        range_val = high - low
        range_ma = range_val.rolling(window=lookback // 2).mean()

        # 收斂：近期範圍小於長期範圍
        squeeze = range_ma < range_ma.rolling(window=lookback).mean()

        signals = pd.Series(0, index=data.index)

        # 收斂後突破高點 → 買入
        breakout_up = (high > high.rolling(window=lookback).max().shift(1)) & squeeze.shift(lookback)
        signals[breakout_up] = 1

        # 收斂後跌破低點 → 賣出
        breakout_down = (low < low.rolling(window=lookback).min().shift(1)) & squeeze.shift(lookback)
        signals[breakout_down] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 2. Elliott 波浪計數
# ============================================================================


class ElliottWave(BaseStrategy):
    """
    Elliott 波浪計數策略

    識別 Elliott 波浪模式（5 浪推動 + 3 浪調整），
    在第 3 浪買入，第 5 浪賣出。
    """

    def __init__(self, wave_length: int = 20):
        super().__init__("Elliott 波浪", {"wave_length": wave_length}, category="pattern")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        wave_len = self.params["wave_length"]

        # 簡化：使用價格動量模擬波浪
        momentum = data["close"].pct_change(periods=wave_len)

        # 檢測波浪階段（簡化）
        # 第 1 浪：動量轉正
        # 第 3 浪：動量最強
        # 第 5 浪：動量減弱

        signals = pd.Series(0, index=data.index)

        # 動量強（模擬第 3 浪）→ 買入
        signals[momentum > 0.1] = 1

        # 動量減弱（模擬第 5 浪）→ 賣出
        signals[(momentum < 0.05) & (momentum.shift(wave_len) > 0.1)] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 3. 諧波模式
# ============================================================================


class HarmonicPatterns(BaseStrategy):
    """
    諧波模式策略

    識別 Gartley、Butterfly、Bat、Crab 等諧波模式，
    在 D 點反轉交易。
    """

    def __init__(self, tolerance: float = 0.05):
        super().__init__("諧波模式", {"tolerance": tolerance}, category="pattern")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        tol = self.params["tolerance"]

        high = data["high"]
        low = data["low"]

        # 簡化：檢測價格回撤到斐波那契水平
        # XA 段
        xa_high = high.rolling(window=50).max()
        xa_low = low.rolling(window=50).min()

        # 0.618 回撤位
        fib_618 = xa_low + 0.618 * (xa_high - xa_low)

        signals = pd.Series(0, index=data.index)

        # 價格回撤到 0.618 → 買入
        near_fib = (low <= fib_618 * 1.01) & (low >= fib_618 * 0.99)
        signals[near_fib] = 1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 4. Wyckoff 方法
# ============================================================================


class WyckoffMethod(BaseStrategy):
    """
    Wyckoff 方法策略

    識別 Wyckoff 積累/分發階段，
    在 Spring 或 Upthrust 時交易。
    """

    def __init__(self, lookback: int = 50):
        super().__init__("Wyckoff 方法", {"lookback": lookback}, category="pattern")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params["lookback"]

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 簡化：檢測 Spring（假跌破）和 Upthrust（假突破）
        range_high = high.rolling(window=lookback).max()
        range_low = low.rolling(window=lookback).min()

        signals = pd.Series(0, index=data.index)

        # Spring: 跌破支撐後快速收回 → 買入
        spring = (low < range_low.shift(1)) & (close > range_low.shift(1))
        signals[spring] = 1

        # Upthrust: 突破阻力後快速回落 → 賣出
        upthrust = (high > range_high.shift(1)) & (close < range_high.shift(1))
        signals[upthrust] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 5. Volume Profile 形態
# ============================================================================


class VolumeProfileShape(BaseStrategy):
    """
    Volume Profile 形態策略

    分析成交量分佈形態，
    識別 POC、Value Area 等。
    """

    def __init__(self, lookback: int = 100, va_percentage: float = 0.7):
        super().__init__(
            "Volume Profile 形態", {"lookback": lookback, "va_percentage": va_percentage}, category="pattern"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params["lookback"]
        va_pct = self.params["va_percentage"]

        close = data["close"]
        volume = data["volume"]

        # 計算 POC（成交量加權平均價）
        poc = (close * volume).rolling(window=lookback).sum() / volume.rolling(window=lookback).sum()

        # 計算價值區域
        std = close.rolling(window=lookback).std()
        va_upper = poc + std * 1.28  # 70% 置信區間
        va_lower = poc - std * 1.28

        signals = pd.Series(0, index=data.index)

        # 價格低於價值區域 → 買入
        signals[close < va_lower] = 1

        # 價格高於價值區域 → 賣出
        signals[close > va_upper] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 策略註冊表
# ============================================================================

PATTERN_COMPLETE_STRATEGIES = {
    "diamond": DiamondPattern,
    "elliott": ElliottWave,
    "harmonic": HarmonicPatterns,
    "wyckoff": WyckoffMethod,
    "volume_profile": VolumeProfileShape,
}

# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("形態策略補全測試")
    print("=" * 60)

    np.random.seed(42)
    n = 300
    dates = pd.date_range("2024-01-01", periods=n, freq="D")

    returns = np.random.randn(n) * 0.02
    close = 100 * np.cumprod(1 + returns)

    data = pd.DataFrame(
        {
            "open": close,
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": np.random.randint(1000000, 10000000, n),
        },
        index=dates,
    )

    for name, cls in PATTERN_COMPLETE_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")

    print("\n" + "=" * 60)
    print("測試完成！形態策略 10/10 完成！✅")
    print("=" * 60)
