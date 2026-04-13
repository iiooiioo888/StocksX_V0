"""
突破策略包
包含 14 個突破策略

作者：StocksX Team
創建日期：2026-03-21
狀態：🔄 批量實作中
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_strategy import BreakoutStrategy

from src.strategies.base_strategy import BreakoutStrategy

# ============================================================================
# 1. 雙推力突破策略
# ============================================================================


class DualThrustBreakout(BreakoutStrategy):
    """
    雙推力突破策略

    基於開盤區間和波動率計算上下軌，
    價格突破上軌買入，突破下軌賣出。
    """

    def __init__(self, lookback: int = 4, k1: float = 0.5, k2: float = 0.5):
        """
        初始化雙推力策略

        Args:
            lookback: 回看天數
            k1: 上軌係數
            k2: 下軌係數
        """
        super().__init__("雙推力突破", {"lookback": lookback, "k1": k1, "k2": k2})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params["lookback"]
        k1 = self.params["k1"]
        k2 = self.params["k2"]

        # 計算過去 N 日的 HH, LL
        hh = data["high"].rolling(window=lookback).max()
        ll = data["low"].rolling(window=lookback).min()
        close_prev = data["close"].shift(1)

        # 計算上下軌
        range_val = hh - ll
        upper_bound = close_prev + k1 * range_val
        lower_bound = close_prev - k2 * range_val

        signals = pd.Series(0, index=data.index)

        # 上穿買入
        cross_above = (data["close"] > upper_bound) & (data["close"].shift(1) <= upper_bound)
        signals[cross_above] = 1

        # 下穿賣出
        cross_below = (data["close"] < lower_bound) & (data["close"].shift(1) >= lower_bound)
        signals[cross_below] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 2. 開盤區間突破 (ORB)
# ============================================================================


class OpeningRangeBreakout(BreakoutStrategy):
    """
    開盤區間突破策略

    基於前一日高低點作為區間，
    突破區間時跟隨交易。
    """

    def __init__(self, stop_loss_pct: float = 0.02):
        """
        初始化 ORB 策略

        Args:
            stop_loss_pct: 止損百分比
        """
        super().__init__("開盤區間突破", {"stop_loss_pct": stop_loss_pct})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        prev_high = data["high"].shift(1)
        prev_low = data["low"].shift(1)

        signals = pd.Series(0, index=data.index)

        # 突破買入
        breakout_long = (data["high"] > prev_high) & (data["high"].shift(1) <= prev_high)
        signals[breakout_long] = 1

        # 突破賣出
        breakout_short = (data["low"] < prev_low) & (data["low"].shift(1) >= prev_low)
        signals[breakout_short] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2.5 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 3. 樞軸點突破
# ============================================================================


class PivotBreakout(BreakoutStrategy):
    """
    樞軸點突破策略

    計算樞軸點及其支撐/阻力位，
    突破阻力買入，跌破支撐賣出。
    """

    def __init__(self, lookback: int = 1):
        """
        初始化樞軸點策略

        Args:
            lookback: 回看天數
        """
        super().__init__("樞軸點突破", {"lookback": lookback})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        high = data["high"].shift(1)
        low = data["low"].shift(1)
        close = data["close"].shift(1)

        # 計算樞軸點
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low  # 第一阻力位
        s1 = 2 * pivot - high  # 第一支撐位

        signals = pd.Series(0, index=data.index)

        # 突破阻力買入
        breakout_r1 = (data["high"] > r1) & (data["high"].shift(1) <= r1)
        signals[breakout_r1] = 1

        # 跌破支撐賣出
        breakout_s1 = (data["low"] < s1) & (data["low"].shift(1) >= s1)
        signals[breakout_s1] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 4. 布林帶擠壓
# ============================================================================


class BollingerSqueeze(BreakoutStrategy):
    """
    布林帶擠壓策略

    當布林帶收窄（擠壓）時，預示即將突破，
    在擠壓後突破時跟隨交易。
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0, squeeze_threshold: float = 0.05):
        """
        初始化布林帶擠壓策略

        Args:
            period: 布林帶週期
            std_dev: 標準差倍數
            squeeze_threshold: 擠壓閾值（帶寬/價格）
        """
        super().__init__("布林帶擠壓", {"period": period, "std_dev": std_dev, "squeeze_threshold": squeeze_threshold})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        period = self.params["period"]
        std_dev = self.params["std_dev"]
        threshold = self.params["squeeze_threshold"]

        # 計算布林帶
        sma = data["close"].rolling(window=period).mean()
        std = data["close"].rolling(window=period).std()
        upper = sma + std_dev * std
        lower = sma - std_dev * std

        # 計算帶寬
        bandwidth = (upper - lower) / sma

        # 檢測擠壓（帶寬小於閾值）
        squeeze = bandwidth < threshold

        signals = pd.Series(0, index=data.index)

        # 擠壓後突破上軌
        squeeze_ended = squeeze.shift(1) & ~squeeze
        breakout_up = (data["close"] > upper) & squeeze_ended
        signals[breakout_up] = 1

        # 擠壓後跌破下軌
        breakout_down = (data["close"] < lower) & squeeze_ended
        signals[breakout_down] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 5. 成交量突破
# ============================================================================


class VolumeBreakout(BreakoutStrategy):
    """
    成交量突破策略

    價格突破伴隨成交量放大，
    確認突破有效性。
    """

    def __init__(self, lookback: int = 20, volume_multiplier: float = 2.0):
        """
        初始化成交量突破策略

        Args:
            lookback: 成交量均線週期
            volume_multiplier: 成交量倍數閾值
        """
        super().__init__("成交量突破", {"lookback": lookback, "volume_multiplier": volume_multiplier})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params["lookback"]
        vol_mult = self.params["volume_multiplier"]

        # 計算成交量均線
        vol_ma = data["volume"].rolling(window=lookback).mean()

        # 高成交量
        high_volume = data["volume"] > vol_mult * vol_ma

        # 價格突破（20 日高）
        price_high = data["high"].rolling(window=lookback).max()
        breakout_up = (data["close"] > price_high.shift(1)) & high_volume

        # 價格跌破（20 日低）
        price_low = data["low"].rolling(window=lookback).min()
        breakout_down = (data["close"] < price_low.shift(1)) & high_volume

        signals = pd.Series(0, index=data.index)
        signals[breakout_up] = 1
        signals[breakout_down] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 6. 斐波那契回撤突破
# ============================================================================


class FibonacciBreakout(BreakoutStrategy):
    """
    斐波那契回撤突破策略

    計算斐波那契回撤位，
    在關鍵位置突破時交易。
    """

    def __init__(self, lookback: int = 50):
        """
        初始化斐波那契策略

        Args:
            lookback: 回看週期
        """
        super().__init__("斐波那契回撤突破", {"lookback": lookback})

        # 斐波那契比例
        self.fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params["lookback"]

        # 找到過去 N 日的高低點
        high = data["high"].rolling(window=lookback).max()
        low = data["low"].rolling(window=lookback).min()

        # 計算回撤位
        range_val = high - low

        signals = pd.Series(0, index=data.index)

        # 簡化：在 0.618 回撤位反彈買入
        fib_618 = low + 0.618 * range_val
        bounce_up = (data["low"] <= fib_618) & (data["close"] > data["open"])
        signals[bounce_up] = 1

        # 在 0.618 回撤位跌破賣出
        fib_618_down = high - 0.618 * range_val
        bounce_down = (data["high"] >= fib_618_down) & (data["close"] < data["open"])
        signals[bounce_down] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 7. 杯柄形態
# ============================================================================


class CupAndHandle(BreakoutStrategy):
    """
    杯柄形態突破策略

    識別杯柄形態並在突破時買入。
    """

    def __init__(self, cup_length: int = 30, handle_length: int = 10):
        """
        初始化杯柄形態策略

        Args:
            cup_length: 杯部長度
            handle_length: 柄部長度
        """
        super().__init__("杯柄形態", {"cup_length": cup_length, "handle_length": handle_length})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（簡化版）"""
        cup_len = self.params["cup_length"]
        handle_len = self.params["handle_length"]

        signals = pd.Series(0, index=data.index)

        # 簡化：檢測價格整固後突破
        # 計算近期高低點
        recent_high = data["high"].rolling(window=cup_len).max()
        recent_low = data["low"].rolling(window=handle_len).min()

        # 價格在區間內整固
        consolidation = (data["close"] > recent_low * 0.95) & (data["close"] < recent_high * 1.05)

        # 突破
        breakout = (data["close"] > recent_high) & consolidation.shift(handle_len).any()
        signals[breakout] = 1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 8. 三重頂/底突破
# ============================================================================


class TripleTopBottom(BreakoutStrategy):
    """
    三重頂/底突破策略

    識別三重頂或三重底形態，
    突破頸線時交易。
    """

    def __init__(self, lookback: int = 50, tolerance: float = 0.02):
        """
        初始化三重頂底策略

        Args:
            lookback: 回看週期
            tolerance: 價格容忍度（2%）
        """
        super().__init__("三重頂/底突破", {"lookback": lookback, "tolerance": tolerance})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（簡化版）"""
        lookback = self.params["lookback"]
        tol = self.params["tolerance"]

        signals = pd.Series(0, index=data.index)

        # 簡化：檢測多次測試同一價位後突破
        recent_high = data["high"].rolling(window=lookback).max()
        recent_low = data["low"].rolling(window=lookback).min()

        # 三重頂：多次測試高點後跌破
        triple_top = data["close"] < recent_low.shift(lookback)
        signals[triple_top] = -1

        # 三重底：多次測試低點後突破
        triple_bottom = data["close"] > recent_high.shift(lookback)
        signals[triple_bottom] = 1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 9. 橫盤均值回歸
# ============================================================================


class SidewaysReversion(BreakoutStrategy):
    """
    橫盤均值回歸策略

    在橫盤區間內低買高賣，
    突破區間時止損。
    """

    def __init__(self, lookback: int = 20, threshold: float = 0.02):
        """
        初始化橫盤回歸策略

        Args:
            lookback: 回看週期
            threshold: 偏離閾值
        """
        super().__init__("橫盤均值回歸", {"lookback": lookback, "threshold": threshold})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params["lookback"]
        threshold = self.params["threshold"]

        # 計算均值和標準差
        sma = data["close"].rolling(window=lookback).mean()
        std = data["close"].rolling(window=lookback).std()

        # 計算 Z-Score
        zscore = (data["close"] - sma) / (std + 1e-10)

        signals = pd.Series(0, index=data.index)

        # 低於均值 2 個標準差買入
        signals[zscore < -2] = 1

        # 高於均值 2 個標準差賣出
        signals[zscore > 2] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.015
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2.5 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 策略註冊表
# ============================================================================

BREAKOUT_STRATEGIES = {
    "dual_thrust": DualThrustBreakout,
    "orb": OpeningRangeBreakout,
    "pivot": PivotBreakout,
    "bollinger_squeeze": BollingerSqueeze,
    "volume_breakout": VolumeBreakout,
    "fibonacci": FibonacciBreakout,
    "cup_handle": CupAndHandle,
    "triple_top_bottom": TripleTopBottom,
    "sideways_reversion": SidewaysReversion,
}

# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("突破策略測試")
    print("=" * 60)

    # 創建測試數據
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

    # 測試各策略
    for name, cls in BREAKOUT_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")

    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
