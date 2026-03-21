"""
執行算法策略包
包含 4 個執行策略

作者：StocksX Team
創建日期：2026-03-21
狀態：🔄 批量實作中
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_strategy import BaseStrategy


# ============================================================================
# 1. VWAP 執行
# ============================================================================

class VWAPExecution(BaseStrategy):
    """
    VWAP 執行策略
    
    跟隨成交量加權平均價格執行，
    價格低於 VWAP 時買入，高於時賣出。
    """
    
    def __init__(self, lookback: int = 20):
        """
        初始化 VWAP 執行策略
        
        Args:
            lookback: 回看週期
        """
        super().__init__('VWAP 執行', {
            'lookback': lookback
        }, category='execution')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        
        # 計算 VWAP
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        volume = data['volume']
        
        vwap = (typical_price * volume).rolling(window=lookback).sum() / \
               volume.rolling(window=lookback).sum()
        
        signals = pd.Series(0, index=data.index)
        
        # 價格低於 VWAP → 買入
        signals[data['close'] < vwap * 0.99] = 1
        
        # 價格高於 VWAP → 賣出
        signals[data['close'] > vwap * 1.01] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
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
# 2. TWAP 執行
# ============================================================================

class TWAPExecution(BaseStrategy):
    """
    TWAP 執行策略
    
    時間加權平均價格執行，
    均勻分拆訂單。
    """
    
    def __init__(self, intervals: int = 10, lookback: int = 50):
        """
        初始化 TWAP 執行策略
        
        Args:
            intervals: 分拆間隔數
            lookback: 回看週期
        """
        super().__init__('TWAP 執行', {
            'intervals': intervals,
            'lookback': lookback
        }, category='execution')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        
        # 計算均價
        avg_price = data['close'].rolling(window=lookback).mean()
        
        signals = pd.Series(0, index=data.index)
        
        # 價格低於均價 → 買入
        signals[data['close'] < avg_price * 0.98] = 1
        
        # 價格高於均價 → 賣出
        signals[data['close'] > avg_price * 1.02] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        # TWAP 均勻分拆
        intervals = self.params['intervals']
        base_position = capital * 0.02 / intervals
        
        if volatility > 0:
            position_size = base_position / (2 * volatility)
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)


# ============================================================================
# 3. 做市策略
# ============================================================================

class MarketMaking(BaseStrategy):
    """
    做市策略
    
    同時提供買賣報價，
    賺取買賣價差。
    """
    
    def __init__(self, spread_pct: float = 0.001, order_size: float = 0.01):
        """
        初始化做市策略
        
        Args:
            spread_pct: 報價價差
            order_size: 訂單大小比例
        """
        super().__init__('做市策略', {
            'spread_pct': spread_pct,
            'order_size': order_size
        }, category='execution')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        spread = self.params['spread_pct']
        
        # 計算中間價
        mid_price = (data['high'] + data['low']) / 2
        
        signals = pd.Series(0, index=data.index)
        
        # 價格接近買入價 → 買入掛單
        bid_price = mid_price * (1 - spread / 2)
        near_bid = abs(data['close'] - bid_price) / bid_price < spread
        
        # 價格接近賣出價 → 賣出掛單
        ask_price = mid_price * (1 + spread / 2)
        near_ask = abs(data['close'] - ask_price) / ask_price < spread
        
        signals[near_bid] = 1
        signals[near_ask] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        order_size = self.params['order_size']
        position_value = capital * order_size
        
        shares = int(position_value / price)
        return max(0, shares)


# ============================================================================
# 4. Implementation Shortfall
# ============================================================================

class ImplementationShortfall(BaseStrategy):
    """
    Implementation Shortfall 執行策略
    
    最小化執行價格與決策價格的差異。
    """
    
    def __init__(self, target_weight: float = 0.5, urgency: float = 0.5):
        """
        初始化 IS 執行策略
        
        Args:
            target_weight: 目標權重
            urgency: 執行緊急性
        """
        super().__init__('Implementation Shortfall', {
            'target_weight': target_weight,
            'urgency': urgency
        }, category='execution')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        urgency = self.params['urgency']
        
        # 計算價格動量
        momentum = data['close'].pct_change(periods=5)
        
        signals = pd.Series(0, index=data.index)
        
        # 動量為正且緊急性高 → 快速買入
        signals[(momentum > 0.01) & (urgency > 0.7)] = 1
        
        # 動量為負且緊急性高 → 快速賣出
        signals[(momentum < -0.01) & (urgency > 0.7)] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        target_weight = self.params['target_weight']
        urgency = self.params['urgency']
        
        # 根據緊急性調整倉位
        position_pct = target_weight * (0.5 + urgency * 0.5)
        position_value = capital * position_pct
        
        shares = int(position_value / price)
        return max(0, shares)


# ============================================================================
# 策略註冊表
# ============================================================================

EXECUTION_STRATEGIES = {
    'vwap': VWAPExecution,
    'twap': TWAPExecution,
    'market_making': MarketMaking,
    'implementation_shortfall': ImplementationShortfall,
}


# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("執行算法測試")
    print("=" * 60)
    
    np.random.seed(42)
    n = 300
    dates = pd.date_range('2024-01-01', periods=n, freq='D')
    
    returns = np.random.randn(n) * 0.02
    close = 100 * np.cumprod(1 + returns)
    
    data = pd.DataFrame({
        'open': close,
        'high': close * 1.02,
        'low': close * 0.98,
        'close': close,
        'volume': np.random.randint(1000000, 10000000, n)
    }, index=dates)
    
    for name, cls in EXECUTION_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
