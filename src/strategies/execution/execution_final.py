"""
執行算法最終補全
包含 5 個進階執行策略：
1. Sniper Strategy（狙擊手策略）
2. Iceberg Orders（冰山訂單）
3. POV Strategy（參與率策略）
4. Arrival Price（到達價策略）
5. Implementation Shortfall Enhanced（增強版執行落差）

作者：StocksX Team
創建日期：2026-03-22
狀態：✅ 批量生成
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_strategy import BaseStrategy

from src.strategies.base_strategy import BaseStrategy

# ============================================================================
# 1. Sniper Strategy 狙擊手策略
# ============================================================================


class SniperStrategy(BaseStrategy):
    """
    狙擊手策略

    在特定時間點或條件下快速執行大額訂單：
    - 監控流動性突增
    - 在最佳時機快速下單
    - 最小化市場衝擊

    適用場景：大額訂單執行、事件驅動交易
    """

    def __init__(self, volume_threshold: float = 3.0, lookback: int = 20):
        super().__init__(
            "Sniper Strategy", {"volume_threshold": volume_threshold, "lookback": lookback}, category="execution"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        threshold = self.params["volume_threshold"]
        lookback = self.params["lookback"]

        close = data["close"]
        volume = data.get("volume", pd.Series(1, index=data.index))

        signals = pd.Series(0, index=data.index)

        # 計算成交量異常
        vol_ma = volume.rolling(lookback).mean()
        vol_std = volume.rolling(lookback).std()
        vol_zscore = (volume - vol_ma) / vol_std

        # 價格動量
        momentum = close.pct_change(5)

        # 狙擊信號：成交量異常 + 價格動量確認
        sniper_buy = (vol_zscore > threshold) & (momentum > 0.02)
        sniper_sell = (vol_zscore > threshold) & (momentum < -0.02)

        signals[sniper_buy] = 1
        signals[sniper_sell] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        # 狙擊策略使用較小倉位
        risk = capital * 0.01
        return risk / (price * volatility)

# ============================================================================
# 2. Iceberg Orders 冰山訂單策略
# ============================================================================


class IcebergOrders(BaseStrategy):
    """
    冰山訂單策略

    將大額訂單拆分爲小單執行，隱藏真實意圖：
    - 監控訂單簿深度
    - 根據流動性動態調整訂單大小
    - 避免暴露大額交易意圖

    適用場景：機構大額建倉/平倉
    """

    def __init__(self, max_visible_pct: float = 0.05, refresh_rate: int = 5):
        super().__init__(
            "Iceberg Orders", {"max_visible_pct": max_visible_pct, "refresh_rate": refresh_rate}, category="execution"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        max_visible = self.params["max_visible_pct"]
        refresh = self.params["refresh_rate"]

        close = data["close"]
        volume = data.get("volume", pd.Series(1, index=data.index))

        signals = pd.Series(0, index=data.index)

        # 計算隱含流動性
        vol_ma = volume.rolling(20).mean()

        # 價格穩定性（低波動適合冰山訂單）
        volatility = close.pct_change().rolling(20).std()
        low_vol = volatility < volatility.rolling(60).quantile(0.3)

        # 趨勢判斷
        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()

        # 冰山信號：低波動 + 趨勢明確
        iceberg_buy = low_vol & (ma20 > ma50) & (close > ma20)
        iceberg_sell = low_vol & (ma20 < ma50) & (close < ma20)

        signals[iceberg_buy] = 1
        signals[iceberg_sell] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        # 冰山訂單通常是大額，但分拆執行
        risk = capital * 0.03
        return risk / (price * volatility)

# ============================================================================
# 3. POV Strategy 參與率策略
# ============================================================================


class POVStrategy(BaseStrategy):
    """
    POV（Percentage of Volume）參與率策略

    根據市場成交量的一定比例執行訂單：
    - 設定目標參與率（如 10%）
    - 市場成交量大時多買，小時少買
    - 自動適應市場流動性

    適用場景：需要跟隨市場節奏的執行
    """

    def __init__(self, target_participation: float = 0.1, max_order_pct: float = 0.05):
        super().__init__(
            "POV Strategy",
            {"target_participation": target_participation, "max_order_pct": max_order_pct},
            category="execution",
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        target_part = self.params["target_participation"]

        close = data["close"]
        volume = data.get("volume", pd.Series(1, index=data.index))

        signals = pd.Series(0, index=data.index)

        # 計算相對成交量
        vol_ma = volume.rolling(20).mean()
        vol_ratio = volume / vol_ma

        # 價格趨勢
        ma20 = close.rolling(20).mean()
        trend = close / ma20 - 1

        # POV 信號：高成交量 + 趨勢確認
        pov_buy = (vol_ratio > 1.5) & (trend > 0.01)
        pov_sell = (vol_ratio > 1.5) & (trend < -0.01)

        signals[pov_buy] = 1
        signals[pov_sell] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)

# ============================================================================
# 4. Arrival Price 到達價策略
# ============================================================================


class ArrivalPrice(BaseStrategy):
    """
    到達價策略

    以訂單到達時的價格爲基準，最小化執行落差：
    - 記錄訂單到達時價格
    - 追蹤 VWAP/TWAP
    - 在價格優於基準時加速執行

    適用場景：對執行價格有明確基準的訂單
    """

    def __init__(self, benchmark: str = "vwap", tolerance: float = 0.01):
        super().__init__("Arrival Price", {"benchmark": benchmark, "tolerance": tolerance}, category="execution")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        benchmark = self.params["benchmark"]
        tolerance = self.params["tolerance"]

        high = data["high"]
        low = data["low"]
        close = data["close"]
        volume = data.get("volume", pd.Series(1, index=data.index))

        signals = pd.Series(0, index=data.index)

        # 計算 VWAP 作爲基準
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).rolling(20).sum() / volume.rolling(20).sum()

        # 價格相對於基準的位置
        price_vs_vwap = close / vwap - 1

        # 到達價信號：價格優於基準時執行
        arrival_buy = price_vs_vwap < -tolerance  # 價格低於 VWAP，買入好價
        arrival_sell = price_vs_vwap > tolerance  # 價格高於 VWAP，賣出好價

        signals[arrival_buy] = 1
        signals[arrival_sell] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)

# ============================================================================
# 5. Implementation Shortfall Enhanced 增強版執行落差策略
# ============================================================================


class ImplementationShortfallEnhanced(BaseStrategy):
    """
    增強版執行落差策略

    優化版的 IS 策略，平衡市場衝擊和機會成本：
    - 動態調整執行速度
    - 考慮價格動量和波動率
    - 最小化總執行成本

    適用場景：大額訂單的優化執行
    """

    def __init__(self, urgency: float = 0.5, risk_aversion: float = 0.3):
        super().__init__("IS Enhanced", {"urgency": urgency, "risk_aversion": risk_aversion}, category="execution")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        urgency = self.params["urgency"]
        risk_aversion = self.params["risk_aversion"]

        close = data["close"]
        volume = data.get("volume", pd.Series(1, index=data.index))

        signals = pd.Series(0, index=data.index)

        # 價格動量
        momentum_5d = close.pct_change(5)
        momentum_1d = close.pct_change()

        # 波動率
        volatility = close.pct_change().rolling(20).std()
        vol_percentile = volatility.rolling(60).rank(pct=True)

        # 流動性
        vol_ma = volume.rolling(20).mean()
        liquidity = volume / vol_ma

        # IS 信號：綜合動量、波動、流動性
        # 高動量 + 高流動 + 低波動 → 快速執行
        is_score = momentum_5d * urgency + liquidity * (1 - risk_aversion) - vol_percentile * risk_aversion

        is_buy = is_score > 0.1
        is_sell = is_score < -0.1

        signals[is_buy] = 1
        signals[is_sell] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.025
        return risk / (price * volatility)

# ============================================================================
# 註冊所有執行最終策略
# ============================================================================

EXECUTION_FINAL_STRATEGIES = {
    "sniper": SniperStrategy,
    "iceberg": IcebergOrders,
    "pov": POVStrategy,
    "arrival_price": ArrivalPrice,
    "is_enhanced": ImplementationShortfallEnhanced,
}

__all__ = [
    "EXECUTION_FINAL_STRATEGIES",
    "SniperStrategy",
    "IcebergOrders",
    "POVStrategy",
    "ArrivalPrice",
    "ImplementationShortfallEnhanced",
]
