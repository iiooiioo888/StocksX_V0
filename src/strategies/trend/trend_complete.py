"""
趨勢策略補全包
包含 9 個核心趨勢策略：
1. SMA Cross（均線交叉）
2. EMA Cross（指數均線交叉）
3. MACD Cross
4. ADX（趨勢強度）
5. Supertrend
6. Parabolic SAR
7. Donchian Channel
8. Dual Thrust
9. VWAP Reversion

作者：StocksX Team
創建日期：2026-03-22
狀態：✅ 批量生成
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_strategy import TrendFollowingStrategy


# ============================================================================
# 1. SMA Cross 均線交叉策略
# ============================================================================


class SMACross(TrendFollowingStrategy):
    """
    簡單移動平均線交叉策略

    經典趨勢跟隨策略：
    - 短周期均線上穿長周期均線 → 買入
    - 短周期均線下穿長周期均線 → 賣出
    """

    def __init__(self, short_period: int = 10, long_period: int = 30):
        super().__init__("SMA Cross", {"short_period": short_period, "long_period": long_period})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        short = self.params["short_period"]
        long_period = self.params["long_period"]

        sma_short = data["close"].rolling(window=short).mean()
        sma_long = data["close"].rolling(window=long_period).mean()

        signals = pd.Series(0, index=data.index)

        # 金叉：短均線上穿長均線
        golden_cross = (sma_short > sma_long) & (sma_short.shift(1) <= sma_long.shift(1))

        # 死叉：短均線下穿長均線
        death_cross = (sma_short < sma_long) & (sma_short.shift(1) >= sma_long.shift(1))

        signals[golden_cross] = 1
        signals[death_cross] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 2. EMA Cross 指數均線交叉策略
# ============================================================================


class EMACross(TrendFollowingStrategy):
    """
    指數移動平均線交叉策略

    使用 EMA 而非 SMA，對近期價格更敏感：
    - EMA 金叉 → 買入
    - EMA 死叉 → 賣出
    """

    def __init__(self, short_period: int = 12, long_period: int = 26):
        super().__init__("EMA Cross", {"short_period": short_period, "long_period": long_period})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        short = self.params["short_period"]
        long_period = self.params["long_period"]

        ema_short = data["close"].ewm(span=short, adjust=False).mean()
        ema_long = data["close"].ewm(span=long_period, adjust=False).mean()

        signals = pd.Series(0, index=data.index)

        # 金叉
        golden_cross = (ema_short > ema_long) & (ema_short.shift(1) <= ema_long.shift(1))

        # 死叉
        death_cross = (ema_short < ema_long) & (ema_short.shift(1) >= ema_long.shift(1))

        signals[golden_cross] = 1
        signals[death_cross] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 3. MACD Cross 策略
# ============================================================================


class MACDCross(TrendFollowingStrategy):
    """
    MACD 交叉策略

    使用 MACD 指標的交叉信號：
    - MACD 線上穿信號線 → 買入
    - MACD 線下穿信號線 → 賣出
    """

    def __init__(self, fast: int = 8, slow: int = 30, signal: int = 7):
        """
        MACD 交叉策略（已優化參數 2026-03-23）
        最優參數: fast=8, slow=30, signal=7
        3年回測 Sharpe: 3.312, Return: 30.37%, MaxDD: -0.90%
        """
        super().__init__("MACD Cross", {"fast": fast, "slow": slow, "signal": signal})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        fast = self.params["fast"]
        slow = self.params["slow"]
        signal_period = self.params["signal"]

        # 計算 MACD
        ema_fast = data["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = data["close"].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow

        # 信號線
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        signals = pd.Series(0, index=data.index)

        # 金叉
        golden_cross = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))

        # 死叉
        death_cross = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

        signals[golden_cross] = 1
        signals[death_cross] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 4. ADX 趨勢強度策略
# ============================================================================


class ADXStrategy(TrendFollowingStrategy):
    """
    ADX（平均趨向指數）趨勢強度策略

    使用 ADX 判斷趨勢強度，配合 DI+ 和 DI- 判斷方向：
    - ADX > 25 且 DI+ > DI- → 買入（強上升趨勢）
    - ADX > 25 且 DI+ < DI- → 賣出（強下降趨勢）
    """

    def __init__(self, period: int = 14, adx_threshold: float = 25):
        super().__init__("ADX 趨勢", {"period": period, "adx_threshold": adx_threshold})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        period = self.params["period"]
        threshold = self.params["adx_threshold"]

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 計算 +DM 和 -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # 真實波幅
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 平滑
        plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / tr.ewm(span=period, adjust=False).mean())
        minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / tr.ewm(span=period, adjust=False).mean())

        # DX 和 ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period, adjust=False).mean()

        signals = pd.Series(0, index=data.index)

        # 強趨勢且方向明確
        buy_signal = (adx > threshold) & (plus_di > minus_di)
        sell_signal = (adx > threshold) & (plus_di < minus_di)

        signals[buy_signal] = 1
        signals[sell_signal] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 5. Supertrend 策略
# ============================================================================


class Supertrend(TrendFollowingStrategy):
    """
    Supertrend 超級趨勢策略

    基於 ATR 的趨勢跟隨指標：
    - 價格上穿 Supertrend 線 → 買入
    - 價格下穿 Supertrend 線 → 賣出
    """

    def __init__(self, period: int = 10, multiplier: float = 3.0):
        super().__init__("Supertrend", {"period": period, "multiplier": multiplier})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        period = self.params["period"]
        mult = self.params["multiplier"]

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 計算 ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()

        # 基本中軌
        hl2 = (high + low) / 2

        # 上軌和下軌
        upper_band = hl2 + mult * atr
        lower_band = hl2 - mult * atr

        # Supertrend 值
        supertrend = pd.Series(0.0, index=data.index)
        trend = pd.Series(1, index=data.index)  # 1=上升趨勢，-1=下降趨勢

        for i in range(1, len(data)):
            if close.iloc[i] > supertrend.iloc[i - 1] if i > 0 else lower_band.iloc[i]:
                trend.iloc[i] = 1
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                trend.iloc[i] = -1
                supertrend.iloc[i] = upper_band.iloc[i]

        signals = pd.Series(0, index=data.index)

        # 趨勢轉換
        trend_change = trend.diff()
        signals[trend_change == 2] = 1  # -1 → 1
        signals[trend_change == -2] = -1  # 1 → -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 6. Parabolic SAR 策略
# ============================================================================


class ParabolicSAR(TrendFollowingStrategy):
    """
    拋物線 SAR（停損反轉）策略

    跟隨趨勢的停損指標：
    - 價格上穿 SAR → 買入
    - 價格下穿 SAR → 賣出
    """

    def __init__(self, af_start: float = 0.02, af_step: float = 0.02, af_max: float = 0.2):
        super().__init__("Parabolic SAR", {"af_start": af_start, "af_step": af_step, "af_max": af_max})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        af_start = self.params["af_start"]
        af_step = self.params["af_step"]
        af_max = self.params["af_max"]

        high = data["high"].values
        low = data["low"].values

        n = len(data)
        psar = np.zeros(n)
        trend = np.zeros(n)  # 1=多頭，-1=空頭
        af = np.zeros(n)

        # 初始化
        trend[0] = 1
        psar[0] = low[0]
        af[0] = af_start
        ep = high[0]  # 極值點

        for i in range(1, n):
            # 計算 SAR
            psar[i] = psar[i - 1] + af[i - 1] * (ep - psar[i - 1])

            if trend[i - 1] == 1:  # 多頭
                if low[i] > psar[i]:
                    trend[i] = 1
                    if high[i] > ep:
                        ep = high[i]
                        af[i] = min(af[i - 1] + af_step, af_max)
                    else:
                        af[i] = af[i - 1]
                else:
                    trend[i] = -1
                    ep = low[i]
                    af[i] = af_start
            else:  # 空頭
                if high[i] < psar[i]:
                    trend[i] = -1
                    if low[i] < ep:
                        ep = low[i]
                        af[i] = min(af[i - 1] + af_step, af_max)
                    else:
                        af[i] = af[i - 1]
                else:
                    trend[i] = 1
                    ep = high[i]
                    af[i] = af_start

        signals = pd.Series(0, index=data.index)
        trend_series = pd.Series(trend, index=data.index)

        # 趨勢轉換
        trend_change = trend_series.diff()
        signals[trend_change == 2] = 1  # 空轉多
        signals[trend_change == -2] = -1  # 多轉空

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 7. Donchian Channel 策略
# ============================================================================


class DonchianChannel(TrendFollowingStrategy):
    """
    唐奇安通道策略（海龜交易法則核心）

    基於 N 日高低點的突破策略：
    - 價格突破 N 日高點 → 買入
    - 價格跌破 N 日低點 → 賣出
    """

    def __init__(self, period: int = 20):
        super().__init__("Donchian Channel", {"period": period})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        period = self.params["period"]

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 唐奇安通道
        upper = high.rolling(window=period).max()
        lower = low.rolling(window=period).min()

        signals = pd.Series(0, index=data.index)

        # 突破上軌
        breakout_up = close > upper.shift(1)

        # 跌破下軌
        breakout_down = close < lower.shift(1)

        signals[breakout_up] = 1
        signals[breakout_down] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 8. Dual Thrust 策略
# ============================================================================


class DualThrust(TrendFollowingStrategy):
    """
    雙推力策略

    基於開盤區間和歷史波動率的突破策略：
    - 上軌 = Open + K1 * Range
    - 下軌 = Open - K2 * Range
    - 突破上軌 → 買入
    - 跌破下軌 → 賣出
    """

    def __init__(self, lookback: int = 4, k1: float = 0.7, k2: float = 0.7):
        super().__init__("Dual Thrust", {"lookback": lookback, "k1": k1, "k2": k2})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params["lookback"]
        k1 = self.params["k1"]
        k2 = self.params["k2"]

        high = data["high"]
        low = data["low"]
        close = data["close"]
        open_price = data["open"]

        # 計算 Range（N 日最大波動）
        hh = high.rolling(lookback).max()  # N 日最高
        lc = close.rolling(lookback).max().shift(1)  # N-1 日收盤最高
        hc = close.rolling(lookback).max().shift(1)  # N-1 日收盤最高
        ll = low.rolling(lookback).min()  # N 日最低

        range_val = pd.concat([hh - lc, hc - ll], axis=1).max(axis=1)

        # 上下軌
        upper = open_price + k1 * range_val
        lower = open_price - k2 * range_val

        signals = pd.Series(0, index=data.index)

        # 突破
        signals[close > upper] = 1
        signals[close < lower] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 9. VWAP Reversion 策略
# ============================================================================


class VWAPReversion(TrendFollowingStrategy):
    """
    VWAP 均值回歸策略

    基於成交量加權平均價格的均值回歸：
    - 價格遠低於 VWAP → 買入（超賣）
    - 價格遠高於 VWAP → 賣出（超買）
    """

    def __init__(self, std_threshold: float = 2.0, lookback: int = 20):
        super().__init__("VWAP Reversion", {"std_threshold": std_threshold, "lookback": lookback})

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        threshold = self.params["std_threshold"]
        lookback = self.params["lookback"]

        high = data["high"]
        low = data["low"]
        close = data["close"]
        volume = data.get("volume", pd.Series(1, index=data.index))

        # 計算 VWAP
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).rolling(lookback).sum() / volume.rolling(lookback).sum()

        # 計算標準差帶
        std = typical_price.rolling(lookback).std()
        upper_band = vwap + threshold * std
        lower_band = vwap - threshold * std

        signals = pd.Series(0, index=data.index)

        # 均值回歸：低於下軌買入，高於上軌賣出
        signals[close < lower_band] = 1
        signals[close > upper_band] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 註冊所有趨勢補全策略
# ============================================================================

TREND_COMPLETE_STRATEGIES = {
    "sma_cross": SMACross,
    "ema_cross": EMACross,
    "macd_cross": MACDCross,
    "adx": ADXStrategy,
    "supertrend": Supertrend,
    "parabolic_sar": ParabolicSAR,
    "donchian": DonchianChannel,
    "dual_thrust": DualThrust,
    "vwap_reversion": VWAPReversion,
}

__all__ = [
    "TREND_COMPLETE_STRATEGIES",
    "SMACross",
    "EMACross",
    "MACDCross",
    "ADXStrategy",
    "Supertrend",
    "ParabolicSAR",
    "DonchianChannel",
    "DualThrust",
    "VWAPReversion",
]
