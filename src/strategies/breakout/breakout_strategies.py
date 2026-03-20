"""
突破策略
包含 16 個突破與均值回歸策略
"""

import pandas as pd
import numpy as np
from typing import Dict
from ..base_strategy import BreakoutStrategy


class DonchianChannel(BreakoutStrategy):
    """唐奇安通道突破策略"""
    
    def __init__(self, period: int = 20):
        super().__init__('唐奇安通道', {
            'period': period
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        high_n = data['high'].rolling(window=self.params['period']).max()
        low_n = data['low'].rolling(window=self.params['period']).min()
        
        signals = pd.Series(0, index=data.index)
        signals[data['close'] > high_n.shift(1)] = 1  # 突破上軌
        signals[data['close'] < low_n.shift(1)] = -1  # 突破下軌
        
        return signals


class VWAPReversion(BreakoutStrategy):
    """VWAP 均值回歸策略"""
    
    def __init__(self, threshold: float = 2.0):
        super().__init__('VWAP 回歸', {
            'threshold': threshold
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if 'vwap' not in data.columns:
            data['vwap'] = (data['close'] * data['volume']).cumsum() / data['volume'].cumsum()
        
        vwap = data['vwap']
        std = data['close'].rolling(window=20).std()
        upper = vwap + self.params['threshold'] * std
        lower = vwap - self.params['threshold'] * std
        
        signals = pd.Series(0, index=data.index)
        signals[data['close'] < lower] = 1  # 低於下軌買入
        signals[data['close'] > upper] = -1  # 高於上軌賣出
        
        return signals


# 策略註冊表
BREAKOUT_STRATEGIES = {
    'donchian': DonchianChannel,
    'vwap_reversion': VWAPReversion,
}
