"""
形態策略包
包含 5 個形態策略

作者：StocksX Team
創建日期：2026-03-21
狀態：🔄 批量實作中
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_strategy import BaseStrategy


# ============================================================================
# 1. 頭肩頂/底
# ============================================================================


class HeadShoulders(BaseStrategy):
    """
    頭肩頂/底形態策略

    識別頭肩頂（看跌）和頭肩底（看漲）形態。
    """

    def __init__(self, lookback: int = 50):
        """
        初始化頭肩頂底策略

        Args:
            lookback: 回看週期
        """
        super().__init__("頭肩頂/底", {"lookback": lookback}, category="pattern")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（簡化版）"""
        lookback = self.params["lookback"]

        # 簡化：檢測三次測試高低點
        high = data["high"]
        low = data["low"]

        # 尋找局部高點
        local_high = (high > high.shift(1)) & (high > high.shift(-1))
        local_low = (low < low.shift(1)) & (low < low.shift(-1))

        signals = pd.Series(0, index=data.index)

        # 簡化：價格跌破頸線（近期低點）時賣出
        neckline = low.rolling(window=lookback).min()
        break_below = low < neckline.shift(1)
        signals[break_below] = -1

        # 價格突破頸線時買入
        neckline_high = high.rolling(window=lookback).max()
        break_above = high > neckline_high.shift(1)
        signals[break_above] = 1

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
# 2. 跳空回補
# ============================================================================


class GapFill(BaseStrategy):
    """
    跳空回補策略

    價格跳空後傾向回補缺口，
    逆向交易。
    """

    def __init__(self, gap_threshold: float = 0.02):
        """
        初始化跳空回補策略

        Args:
            gap_threshold: 跳空閾值（2%）
        """
        super().__init__("跳空回補", {"gap_threshold": gap_threshold}, category="pattern")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        threshold = self.params["gap_threshold"]

        # 計算跳空
        gap_up = data["low"] > data["high"].shift(1) * (1 + threshold)
        gap_down = data["high"] < data["low"].shift(1) * (1 - threshold)

        signals = pd.Series(0, index=data.index)

        # 向上跳空後賣出（預期回補）
        signals[gap_up] = -1

        # 向下跳空後買入（預期回補）
        signals[gap_down] = 1

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
# 3. K 線組合
# ============================================================================


class CandlestickPatterns(BaseStrategy):
    """
    K 線組合策略

    識別常見 K 線形態：
    - 十字星
    - 吞沒形態
    - 晨星/暮星
    """

    def __init__(self, doji_threshold: float = 0.001):
        """
        初始化 K 線策略

        Args:
            doji_threshold: 十字星閾值
        """
        super().__init__("K 線組合", {"doji_threshold": doji_threshold}, category="pattern")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        threshold = self.params["doji_threshold"]

        open_price = data["open"]
        close = data["close"]
        high = data["high"]
        low = data["low"]

        # 計算實體和影線
        body = abs(close - open_price)
        range_val = high - low

        signals = pd.Series(0, index=data.index)

        # 十字星：實體很小
        doji = (body / (range_val + 1e-10)) < threshold

        # 陽吞陰（看漲）
        bullish_engulf = (
            (close > open_price)
            & (close.shift(1) < open_price.shift(1))
            & (close > open_price.shift(1))
            & (open_price < close.shift(1))
        )

        # 陰吞陽（看跌）
        bearish_engulf = (
            (close < open_price)
            & (close.shift(1) > open_price.shift(1))
            & (close < open_price.shift(1))
            & (open_price > close.shift(1))
        )

        signals[bullish_engulf] = 1
        signals[bearish_engulf] = -1

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
# 4. 市場結構
# ============================================================================


class MarketStructure(BaseStrategy):
    """
    市場結構策略

    識別 HH（更高高點）、HL（更高低點）、
    LL（更低低點）、LH（更低高點）。
    """

    def __init__(self, lookback: int = 20):
        """
        初始化市場結構策略

        Args:
            lookback: 回看週期
        """
        super().__init__("市場結構", {"lookback": lookback}, category="pattern")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params["lookback"]

        high = data["high"]
        low = data["low"]

        # 計算近期高低點
        recent_high = high.rolling(window=lookback).max()
        recent_low = low.rolling(window=lookback).min()

        signals = pd.Series(0, index=data.index)

        # 突破前高（HH）→ 買入
        break_high = high > recent_high.shift(1)
        signals[break_high] = 1

        # 跌破前低（LL）→ 賣出
        break_low = low < recent_low.shift(1)
        signals[break_low] = -1

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
# 5. 楔形形態
# ============================================================================


class WedgePattern(BaseStrategy):
    """
    楔形形態策略

    識別上升楔形（看跌）和下降楔形（看漲）。
    """

    def __init__(self, lookback: int = 30):
        """
        初始化楔形策略

        Args:
            lookback: 回看週期
        """
        super().__init__("楔形形態", {"lookback": lookback}, category="pattern")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（簡化版）"""
        lookback = self.params["lookback"]

        # 計算趨勢線（簡化：使用線性回歸）
        x = np.arange(lookback)

        signals = pd.Series(0, index=data.index)

        # 簡化：檢測價格整固後突破
        # 計算價格區間
        high_range = data["high"].rolling(window=lookback).max()
        low_range = data["low"].rolling(window=lookback).min()

        # 區間收窄
        squeeze = (high_range - low_range) / low_range < 0.1

        # 突破
        breakout_up = (data["close"] > high_range.shift(1)) & squeeze.shift(lookback)
        breakout_down = (data["close"] < low_range.shift(1)) & squeeze.shift(lookback)

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
# 策略註冊表
# ============================================================================

PATTERN_STRATEGIES = {
    "head_shoulders": HeadShoulders,
    "gap_fill": GapFill,
    "candlestick": CandlestickPatterns,
    "market_structure": MarketStructure,
    "wedge": WedgePattern,
}


# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("形態策略測試")
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

    for name, cls in PATTERN_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")

    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
