"""
StocksX 策略基類
所有策略必須繼承自這些基類
"""

import pandas as pd
from typing import Any
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """策略基類"""

    def __init__(self, name: str, params: dict[str, Any], category: str = "unknown"):
        """
        初始化策略

        Args:
            name: 策略名稱
            params: 參數字典
            category: 策略類別
        """
        self.name = name
        self.params = params
        self.category = category

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series（1=買入，-1=賣出，0=持有）
        """
        pass

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """
        默認倉位計算（子類可覆蓋）
        根據策略類別使用不同的風險參數

        Args:
            signal: 交易信號（1, -1, 0）
            capital: 可用資金
            price: 當前價格
            volatility: 波動率

        Returns:
            倉位大小（股數）
        """
        if signal == 0:
            return 0

        # 不同策略類別使用不同的風險系數
        risk_coefficients = {
            "trend": 0.02,          # 趨勢策略：2% 風險，較寬松
            "oscillator": 0.015,    # 振盪器：1.5%，中頻交易
            "breakout": 0.025,      # 突破策略：2.5%，需要更大倉位捕捉突破
            "mean_reversion": 0.01, # 均值回歸：1%，高頻小倉
            "ai_ml": 0.015,         # AI/ML：1.5%，模型不確定性
            "risk": 0.03,           # 風險管理：3%，本身就是風控
            "microstructure": 0.01, # 微結構：1%，高頻
            "macro": 0.02,          # 宏觀：2%，低頻大倉
            "statistical": 0.015,   # 統計：1.5%
            "pattern": 0.02,        # 形態：2%
            "execution": 0.02,      # 執行：2%
            "unknown": 0.02,        # 默認
        }

        risk_pct = risk_coefficients.get(self.category, 0.02)
        risk_amount = capital * risk_pct

        if volatility > 0:
            position_size = risk_amount / (price * volatility)
        else:
            position_size = 0

        return round(position_size, 2)

    def get_params(self) -> dict[str, Any]:
        """獲取參數"""
        return self.params.copy()

    def set_params(self, **kwargs) -> None:
        """設置參數"""
        self.params.update(kwargs)


class StopLossMixin:
    """
    止損/止盈 Mixin
    策略可以通過繼承此類獲得止損/止盈能力
    """

    def __init__(self, *args, stop_loss_pct: float = 0.05, take_profit_pct: float = 0.10, trailing_stop: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_loss_pct = stop_loss_pct      # 默認 5% 止損
        self.take_profit_pct = take_profit_pct   # 默認 10% 止盈
        self.trailing_stop = trailing_stop        # 是否使用移動止損
        self._entry_price = None
        self._highest_price = None

    def check_stop_loss(self, current_price: float, entry_price: float) -> bool:
        """檢查是否觸發止損"""
        if entry_price is None or entry_price <= 0:
            return False
        drawdown = (current_price - entry_price) / entry_price
        return drawdown <= -self.stop_loss_pct

    def check_take_profit(self, current_price: float, entry_price: float) -> bool:
        """檢查是否觸發止盈"""
        if entry_price is None or entry_price <= 0:
            return False
        gain = (current_price - entry_price) / entry_price
        return gain >= self.take_profit_pct

    def check_trailing_stop(self, current_price: float) -> bool:
        """檢查移動止損"""
        if not self.trailing_stop or self._highest_price is None:
            return False
        drawdown = (current_price - self._highest_price) / self._highest_price
        return drawdown <= -self.stop_loss_pct

    def apply_stop_loss_to_signals(self, signals: pd.Series, data: pd.DataFrame) -> pd.Series:
        """
        在信號層面應用止損/止盈
        當持倉中觸發止損或止盈時，強制生成賣出信號
        """
        close = data["close"]
        enhanced_signals = signals.copy()

        in_position = False
        entry_price = 0.0
        highest_price = 0.0

        for i in range(len(signals)):
            current_price = close.iloc[i]

            if not in_position:
                # 檢查買入信號
                if signals.iloc[i] == 1:
                    in_position = True
                    entry_price = current_price
                    highest_price = current_price
            else:
                # 更新最高價（用於移動止損）
                highest_price = max(highest_price, current_price)

                # 檢查止損
                if self.check_stop_loss(current_price, entry_price):
                    enhanced_signals.iloc[i] = -1
                    in_position = False
                    continue

                # 檢查止盈
                if self.check_take_profit(current_price, entry_price):
                    enhanced_signals.iloc[i] = -1
                    in_position = False
                    continue

                # 檢查移動止損
                if self.trailing_stop and self.check_trailing_stop(current_price):
                    enhanced_signals.iloc[i] = -1
                    in_position = False
                    continue

                # 檢查賣出信號
                if signals.iloc[i] == -1:
                    in_position = False

        return enhanced_signals


class TrendFollowingStrategy(BaseStrategy):
    """趨勢跟隨策略基類"""

    def __init__(self, name: str, params: dict[str, Any]):
        super().__init__(name, params, category="trend")


class OscillatorStrategy(BaseStrategy):
    """振盪器策略基類"""

    def __init__(self, name: str, params: dict[str, Any]):
        super().__init__(name, params, category="oscillator")


class BreakoutStrategy(BaseStrategy):
    """突破策略基類"""

    def __init__(self, name: str, params: dict[str, Any]):
        super().__init__(name, params, category="breakout")


class MeanReversionStrategy(BaseStrategy):
    """均值回歸策略基類"""

    def __init__(self, name: str, params: dict[str, Any]):
        super().__init__(name, params, category="mean_reversion")


class AIMLStrategy(BaseStrategy):
    """AI/ML 策略基類"""

    def __init__(self, name: str, params: dict[str, Any]):
        super().__init__(name, params, category="ai_ml")


class RiskManagementStrategy(BaseStrategy):
    """風險管理策略基類"""

    def __init__(self, name: str, params: dict[str, Any]):
        super().__init__(name, params, category="risk")
