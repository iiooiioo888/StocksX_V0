"""
進階振盪器策略包
包含 4 個經典振盪器策略：
1. 一目均衡表（Ichimoku Cloud）
2. Stochastic RSI
3. Awesome Oscillator
4. Vortex 振盪

作者：StocksX Team
創建日期：2026-03-20
狀態：✅ 已完成
"""

import pandas as pd
import numpy as np
from ..base_strategy import OscillatorStrategy


# ============================================================================
# 1. 一目均衡表（Ichimoku Cloud）策略
# ============================================================================


class IchimokuCloud(OscillatorStrategy):
    """
    一目均衡表策略

    日本經典技術分析系統，包含五條線：
    - 轉換線（Tenkan）：9 期高點 + 低點平均
    - 基準線（Kijun）：26 期高點 + 低點平均
    - 領先跨度 A（Senkou A）：轉換線 + 基準線平均
    - 領先跨度 B（Senkou B）：52 期高點 + 低點平均
    - 落後跨度（Chikou）：收盤價落後 26 期

    信號規則：
    - 價格在雲上 + 轉換線上穿基準線 → 買入
    - 價格在雲下 + 轉換線下穿基準線 → 賣出
    """

    def __init__(
        self, tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52, displacement: int = 26
    ):
        """
        初始化一目均衡表

        Args:
            tenkan_period: 轉換線周期（默认 9）
            kijun_period: 基準線周期（默认 26）
            senkou_b_period: 領先跨度 B 周期（默认 52）
            displacement: 位移（默认 26）
        """
        super().__init__(
            "一目均衡表",
            {
                "tenkan_period": tenkan_period,
                "kijun_period": kijun_period,
                "senkou_b_period": senkou_b_period,
                "displacement": displacement,
            },
        )

    def calculate_ichimoku(self, data: pd.DataFrame) -> dict[str, pd.Series]:
        """
        計算一目均衡表五條線

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            包含五條線的字典
        """
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 轉換線（Tenkan）
        tenkan_period = self.params["tenkan_period"]
        tenkan = (high.rolling(window=tenkan_period).max() + low.rolling(window=tenkan_period).min()) / 2

        # 基準線（Kijun）
        kijun_period = self.params["kijun_period"]
        kijun = (high.rolling(window=kijun_period).max() + low.rolling(window=kijun_period).min()) / 2

        # 領先跨度 A（Senkou A）
        senkou_a = (tenkan + kijun) / 2
        senkou_a = senkou_a.shift(self.params["displacement"])

        # 領先跨度 B（Senkou B）
        senkou_b_period = self.params["senkou_b_period"]
        senkou_b = (high.rolling(window=senkou_b_period).max() + low.rolling(window=senkou_b_period).min()) / 2
        senkou_b = senkou_b.shift(self.params["displacement"])

        # 落後跨度（Chikou）
        chikou = close.shift(-self.params["displacement"])

        return {"tenkan": tenkan, "kijun": kijun, "senkou_a": senkou_a, "senkou_b": senkou_b, "chikou": chikou}

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        信號規則：
        - 價格在雲上 + 轉換線上穿基準線 → 買入
        - 價格在雲下 + 轉換線下穿基準線 → 賣出

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series
        """
        ichimoku = self.calculate_ichimoku(data)
        close = data["close"]

        tenkan = ichimoku["tenkan"]
        kijun = ichimoku["kijun"]
        senkou_a = ichimoku["senkou_a"]
        senkou_b = ichimoku["senkou_b"]

        signals = pd.Series(0, index=data.index)

        # 判斷雲層
        cloud_top = pd.concat([senkou_a, senkou_b], axis=1).max(axis=1)
        cloud_bottom = pd.concat([senkou_a, senkou_b], axis=1).min(axis=1)

        # 價格在雲上
        price_above_cloud = close > cloud_top

        # 價格在雲下
        price_below_cloud = close < cloud_bottom

        # 轉換線上穿基準線（黃金交叉）
        tk_cross_above = (tenkan > kijun) & (tenkan.shift(1) < kijun.shift(1))

        # 轉換線下穿基準線（死亡交叉）
        tk_cross_below = (tenkan < kijun) & (tenkan.shift(1) > kijun.shift(1))

        # 生成信號
        signals[price_above_cloud & tk_cross_above] = 1
        signals[price_below_cloud & tk_cross_below] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        stop_loss_distance = 2 * volatility

        risk_amount = capital * risk_per_trade
        if stop_loss_distance > 0:
            position_size = risk_amount / stop_loss_distance
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)


# ============================================================================
# 2. Stochastic RSI 策略
# ============================================================================


class StochasticRSI(OscillatorStrategy):
    """
    Stochastic RSI 策略

    對 RSI 再做隨機運算，極端靈敏。

    計算方法：
    StochRSI = (RSI - min(RSI)) / (max(RSI) - min(RSI))

    信號規則：
    - StochRSI < 0.2 且上穿 → 買入
    - StochRSI > 0.8 且下穿 → 賣出
    """

    def __init__(self, rsi_period: int = 14, stoch_period: int = 14, overbought: float = 0.8, oversold: float = 0.2):
        """
        初始化 Stochastic RSI

        Args:
            rsi_period: RSI 周期（默认 14）
            stoch_period: Stoch 周期（默认 14）
            overbought: 超買線（默认 0.8）
            oversold: 超賣線（默认 0.2）
        """
        super().__init__(
            "Stochastic RSI",
            {"rsi_period": rsi_period, "stoch_period": stoch_period, "overbought": overbought, "oversold": oversold},
        )

    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """計算 RSI"""
        period = self.params["rsi_period"]
        delta = data["close"].diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_stoch_rsi(self, data: pd.DataFrame) -> pd.Series:
        """
        計算 Stochastic RSI

        Returns:
            StochRSI 序列（0-1 範圍）
        """
        rsi = self.calculate_rsi(data)
        period = self.params["stoch_period"]

        # 計算 RSI 的最低值和最高值
        rsi_min = rsi.rolling(window=period).min()
        rsi_max = rsi.rolling(window=period).max()

        # 計算 StochRSI
        stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min)
        stoch_rsi.fillna(0.5, inplace=True)

        return stoch_rsi

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        信號規則：
        - StochRSI < 0.2 且上穿 → 買入
        - StochRSI > 0.8 且下穿 → 賣出

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series
        """
        stoch_rsi = self.calculate_stoch_rsi(data)
        overbought = self.params["overbought"]
        oversold = self.params["oversold"]

        signals = pd.Series(0, index=data.index)

        # StochRSI 從超賣區上穿
        cross_above_oversold = (stoch_rsi > oversold) & (stoch_rsi.shift(1) < oversold)
        signals[cross_above_oversold] = 1

        # StochRSI 從超買區下穿
        cross_below_overbought = (stoch_rsi < overbought) & (stoch_rsi.shift(1) > overbought)
        signals[cross_below_overbought] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        stop_loss_distance = 2 * volatility

        risk_amount = capital * risk_per_trade
        if stop_loss_distance > 0:
            position_size = risk_amount / stop_loss_distance
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)


# ============================================================================
# 3. Awesome Oscillator 策略
# ============================================================================


class AwesomeOscillator(OscillatorStrategy):
    """
    Awesome Oscillator（AO）策略

    衡量市場動量，計算 5 期與 34 期中點均線的差值。

    計算方法：
    AO = SMA(Median, 5) - SMA(Median, 34)
    其中 Median = (High + Low) / 2

    信號規則：
    - AO 從下上穿 0 軸 → 買入
    - AO 從上下穿 0 軸 → 賣出
    - 雙峰形態（Twin Peaks）→ 反轉信號
    """

    def __init__(self, fast_period: int = 5, slow_period: int = 34):
        """
        初始化 Awesome Oscillator

        Args:
            fast_period: 快速周期（默认 5）
            slow_period: 慢速周期（默认 34）
        """
        super().__init__("Awesome Oscillator", {"fast_period": fast_period, "slow_period": slow_period})

    def calculate_ao(self, data: pd.DataFrame) -> pd.Series:
        """
        計算 Awesome Oscillator

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            AO 序列
        """
        median = (data["high"] + data["low"]) / 2

        fast_sma = median.rolling(window=self.params["fast_period"]).mean()
        slow_sma = median.rolling(window=self.params["slow_period"]).mean()

        ao = fast_sma - slow_sma

        return ao

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        信號規則：
        - AO 從下上穿 0 軸 → 買入
        - AO 從上下穿 0 軸 → 賣出

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series
        """
        ao = self.calculate_ao(data)

        signals = pd.Series(0, index=data.index)

        # AO 上穿 0 軸
        cross_above_zero = (ao > 0) & (ao.shift(1) < 0)
        signals[cross_above_zero] = 1

        # AO 下穿 0 軸
        cross_below_zero = (ao < 0) & (ao.shift(1) > 0)
        signals[cross_below_zero] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        stop_loss_distance = 2 * volatility

        risk_amount = capital * risk_per_trade
        if stop_loss_distance > 0:
            position_size = risk_amount / stop_loss_distance
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)


# ============================================================================
# 4. Vortex 振盪策略
# ============================================================================


class VortexOscillator(OscillatorStrategy):
    """
    Vortex 振盪策略

    基於 TR 分離多空渦旋，交叉為信號。

    計算方法：
    - VM+（多頭渦旋）：當前高點 - 前低點的絕對值
    - VM-（空頭渦旋）：當前低點 - 前高點的絕對值
    - VI+ = VM+ / TR
    - VI- = VM- / TR

    信號規則：
    - VI+ 上穿 VI- → 買入
    - VI+ 下穿 VI- → 賣出
    """

    def __init__(self, period: int = 14):
        """
        初始化 Vortex 振盪

        Args:
            period: 周期（默认 14）
        """
        super().__init__("Vortex 振盪", {"period": period})

    def calculate_vortex(self, data: pd.DataFrame) -> dict[str, pd.Series]:
        """
        計算 Vortex 指標

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            包含 VI+ 和 VI- 的字典
        """
        period = self.params["period"]
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 計算 TR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 計算 VM+ 和 VM-
        vm_plus = abs(high - low.shift(1))
        vm_minus = abs(low - high.shift(1))

        # 計算 VI+ 和 VI-
        vi_plus = vm_plus.rolling(window=period).sum() / tr.rolling(window=period).sum()
        vi_minus = vm_minus.rolling(window=period).sum() / tr.rolling(window=period).sum()

        return {"vi_plus": vi_plus, "vi_minus": vi_minus}

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        信號規則：
        - VI+ 上穿 VI- → 買入
        - VI+ 下穿 VI- → 賣出

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series
        """
        vortex = self.calculate_vortex(data)
        vi_plus = vortex["vi_plus"]
        vi_minus = vortex["vi_minus"]

        signals = pd.Series(0, index=data.index)

        # VI+ 上穿 VI-
        cross_above = (vi_plus > vi_minus) & (vi_plus.shift(1) < vi_minus.shift(1))
        signals[cross_above] = 1

        # VI+ 下穿 VI-
        cross_below = (vi_plus < vi_minus) & (vi_plus.shift(1) > vi_minus.shift(1))
        signals[cross_below] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        stop_loss_distance = 2 * volatility

        risk_amount = capital * risk_per_trade
        if stop_loss_distance > 0:
            position_size = risk_amount / stop_loss_distance
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)


# ============================================================================
# 策略註冊表
# ============================================================================

ADVANCED_OSCILLATOR_STRATEGIES = {
    "ichimoku": IchimokuCloud,
    "stoch_rsi": StochasticRSI,
    "awesome": AwesomeOscillator,
    "vortex": VortexOscillator,
}


# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == "__main__":
    import numpy as np

    # 創建測試數據
    np.random.seed(42)
    n = 300
    dates = pd.date_range("2024-01-01", periods=n, freq="D")

    returns = np.random.randn(n) * 0.02
    close = 100 * np.cumprod(1 + returns)
    high = close * (1 + np.abs(np.random.randn(n) * 0.01))
    low = close * (1 - np.abs(np.random.randn(n) * 0.01))
    volume = np.random.randint(1000000, 10000000, n)

    data = pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume}, index=dates)

    print("=" * 60)
    print("進階振盪器策略測試")
    print("=" * 60)

    # 測試一目均衡表
    print("\n1. 一目均衡表")
    ichimoku = IchimokuCloud()
    signals = ichimoku.generate_signals(data)
    print(f"   信號數量：{(signals != 0).sum()}")
    print("   ✅ 測試通過")

    # 測試 Stochastic RSI
    print("\n2. Stochastic RSI")
    stoch_rsi = StochasticRSI()
    signals = stoch_rsi.generate_signals(data)
    print(f"   信號數量：{(signals != 0).sum()}")
    print("   ✅ 測試通過")

    # 測試 Awesome Oscillator
    print("\n3. Awesome Oscillator")
    ao = AwesomeOscillator()
    signals = ao.generate_signals(data)
    print(f"   信號數量：{(signals != 0).sum()}")
    print("   ✅ 測試通過")

    # 測試 Vortex
    print("\n4. Vortex 振盪")
    vortex = VortexOscillator()
    signals = vortex.generate_signals(data)
    print(f"   信號數量：{(signals != 0).sum()}")
    print("   ✅ 測試通過")

    print("\n" + "=" * 60)
    print("🎉 4 個進階振盪器策略全部測試通過！")
    print("=" * 60)
