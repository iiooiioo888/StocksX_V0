"""
統計策略包
包含 6 個統計策略

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

from src.strategies.base_strategy import BaseStrategy

# ============================================================================
# 1. 協整配對
# ============================================================================


class CointegrationPair(BaseStrategy):
    """
    協整配對交易策略

    尋找協整的資產對，進行配對交易。
    """

    def __init__(self, lookback: int = 60, threshold: float = 2.0):
        """
        初始化協整配對策略

        Args:
            lookback: 回看週期
            threshold: 交易閾值（標準差）
        """
        super().__init__("協整配對", {"lookback": lookback, "threshold": threshold}, category="statistical")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params["lookback"]
        threshold = self.params["threshold"]

        # 計算價差（簡化：使用價格與均值的偏離）
        spread = data["close"] - data["close"].rolling(window=lookback).mean()
        spread_std = spread.rolling(window=lookback).std()

        zscore = spread / (spread_std + 1e-10)

        signals = pd.Series(0, index=data.index)

        # 價差低於 -2σ → 買入
        signals[zscore < -threshold] = 1

        # 價差高於 +2σ → 賣出
        signals[zscore > threshold] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.015
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 2. Kalman 濾波
# ============================================================================


class KalmanFilter(BaseStrategy):
    """
    Kalman 濾波追蹤策略

    使用 Kalman 濾波估計真實價格，
    偏離時交易。
    """

    def __init__(self, process_variance: float = 1e-5, measurement_variance: float = 0.1):
        """
        初始化 Kalman 濾波策略

        Args:
            process_variance: 過程方差
            measurement_variance: 測量方差
        """
        super().__init__(
            "Kalman 濾波",
            {"process_variance": process_variance, "measurement_variance": measurement_variance},
            category="statistical",
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（簡化版）"""
        # 簡化：使用 EMA 模擬 Kalman 濾波
        Q = self.params["process_variance"]
        R = self.params["measurement_variance"]

        # 計算 EMA（簡化 Kalman）
        alpha = Q / (Q + R)
        kalman = data["close"].ewm(alpha=alpha, adjust=False).mean()

        signals = pd.Series(0, index=data.index)

        # 價格高於估計值 → 賣出
        signals[data["close"] > kalman * 1.02] = -1

        # 價格低於估計值 → 買入
        signals[data["close"] < kalman * 0.98] = 1

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
# 3. GARCH 波動率模型
# ============================================================================


class GARCHVolatility(BaseStrategy):
    """
    GARCH 波動率模型策略

    使用 GARCH 模型預測波動率，
    波動率低時買入，高時賣出。
    """

    def __init__(self, p: int = 1, q: int = 1, lookback: int = 252):
        """
        初始化 GARCH 策略

        Args:
            p: GARCH 階數
            q: ARCH 階數
            lookback: 回看天數
        """
        super().__init__("GARCH 波動率模型", {"p": p, "q": q, "lookback": lookback}, category="statistical")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params["lookback"]

        # 計算實現波動率（簡化 GARCH）
        returns = data["close"].pct_change()
        realized_vol = returns.rolling(window=lookback).std() * np.sqrt(252)

        # 波動率分位數
        vol_percentile = realized_vol.rolling(window=lookback).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])

        signals = pd.Series(0, index=data.index)

        # 波動率低（<30% 分位）→ 買入
        signals[vol_percentile < 0.3] = 1

        # 波動率高（>70% 分位）→ 賣出
        signals[vol_percentile > 0.7] = -1

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
# 4. 馬可夫體制轉換
# ============================================================================


class MarkovRegime(BaseStrategy):
    """
    馬可夫體制轉換策略

    識別市場體制（牛市/熊市/震盪），
    根據體制調整策略。
    """

    def __init__(self, lookback: int = 60):
        """
        初始化馬可夫體制策略

        Args:
            lookback: 回看週期
        """
        super().__init__("馬可夫體制轉換", {"lookback": lookback}, category="statistical")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params["lookback"]

        # 計算動量和波動率
        momentum = data["close"].pct_change(periods=lookback)
        volatility = data["close"].pct_change().rolling(window=lookback).std()

        # 簡化體制識別
        # 牛市：動量正 + 波動率低
        # 熊市：動量負 + 波動率高
        # 震盪：動量接近 0

        signals = pd.Series(0, index=data.index)

        # 牛市體制
        bull = (momentum > 0.05) & (volatility < volatility.median())
        signals[bull] = 1

        # 熊市體制
        bear = (momentum < -0.05) & (volatility > volatility.median())
        signals[bear] = -1

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
# 5. 變點偵測
# ============================================================================


class ChangePointDetection(BaseStrategy):
    """
    變點偵測策略

    使用 CUSUM 等方法偵測市場結構變化，
    變點後跟隨新趨勢。
    """

    def __init__(self, threshold: float = 0.05, lookback: int = 50):
        """
        初始化變點偵測策略

        Args:
            threshold: 變點閾值
            lookback: 回看週期
        """
        super().__init__("變點偵測", {"threshold": threshold, "lookback": lookback}, category="statistical")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        threshold = self.params["threshold"]
        lookback = self.params["lookback"]

        # 計算 CUSUM（簡化）
        returns = data["close"].pct_change()
        mean_return = returns.rolling(window=lookback).mean()
        std_return = returns.rolling(window=lookback).std()

        # CUSUM 統計量
        cusum_pos = ((returns - mean_return) / (std_return + 1e-10)).cumsum()
        cusum_neg = -cusum_pos

        signals = pd.Series(0, index=data.index)

        # 檢測變點
        change_up = cusum_pos.diff() > threshold
        change_down = cusum_neg.diff() > threshold

        signals[change_up] = 1
        signals[change_down] = -1

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

STAT_STRATEGIES = {
    "cointegration": CointegrationPair,
    "kalman": KalmanFilter,
    "garch": GARCHVolatility,
    "markov": MarkovRegime,
    "changepoint": ChangePointDetection,
}

# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("統計策略測試")
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

    for name, cls in STAT_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")

    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
