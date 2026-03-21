"""
StocksX 策略基類
所有策略必須繼承自這些基類
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """策略基類"""
    
    def __init__(self, name: str, params: Dict[str, Any], category: str = 'unknown'):
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
    
    @abstractmethod
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """
        計算倉位大小
        
        Args:
            signal: 交易信號（1, -1, 0）
            capital: 可用資金
            price: 當前價格
            volatility: 波動率
            
        Returns:
            倉位大小（股數）
        """
        pass
    
    def get_params(self) -> Dict[str, Any]:
        """獲取參數"""
        return self.params.copy()
    
    def set_params(self, **kwargs) -> None:
        """設置參數"""
        self.params.update(kwargs)


class TrendFollowingStrategy(BaseStrategy):
    """趨勢跟隨策略基類"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        super().__init__(name, params, category='trend')


class OscillatorStrategy(BaseStrategy):
    """振盪器策略基類"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        super().__init__(name, params, category='oscillator')


class BreakoutStrategy(BaseStrategy):
    """突破策略基類"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        super().__init__(name, params, category='breakout')


class MeanReversionStrategy(BaseStrategy):
    """均值回歸策略基類"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        super().__init__(name, params, category='mean_reversion')


class AIMLStrategy(BaseStrategy):
    """AI/ML 策略基類"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        super().__init__(name, params, category='ai_ml')


class RiskManagementStrategy(BaseStrategy):
    """風險管理策略基類"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        super().__init__(name, params, category='risk')
