"""
突破策略最終補全
包含 2 個最後突破策略：
1. Inside Bar Breakout（內包線突破）
2. Ascending/Descending Triangle（上升/下降三角形）

作者：StocksX Team
創建日期：2026-03-22
狀態：✅ 批量生成
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

from src.strategies.base_strategy import BreakoutStrategy

# ============================================================================
# 1. Inside Bar Breakout 內包線突破策略
# ============================================================================

class InsideBarBreakout(BreakoutStrategy):
    """
    內包線突破策略
    
    內包線（Inside Bar）表示市場猶豫，突破後通常有強烈走勢：
    - 內包線：當日高點 < 前日高點 且 當日低點 > 前日低點
    - 向上突破內包線高點 → 買入
    - 向下跌破內包線低點 → 賣出
    
    適用場景：震盪後的突破交易
    """
    
    def __init__(self, lookback: int = 3):
        super().__init__('Inside Bar Breakout', {
            'lookback': lookback
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        
        high = data['high']
        low = data['low']
        close = data['close']
        
        signals = pd.Series(0, index=data.index)
        
        # 檢測內包線
        # 當日高點 < 前日高點 且 當日低點 > 前日低點
        inside_bar = (high < high.shift(1)) & (low > low.shift(1))
        
        # 記錄內包線的高低點
        inside_high = high.where(inside_bar, np.nan).rolling(lookback, min_periods=1).max()
        inside_low = low.where(inside_bar, np.nan).rolling(lookback, min_periods=1).min()
        
        # 突破信號
        breakout_up = close > inside_high.shift(1)
        breakout_down = close < inside_low.shift(1)
        
        # 確認有內包線形態
        has_inside = inside_bar.rolling(lookback).sum() > 0
        
        signals[breakout_up & has_inside] = 1
        signals[breakout_down & has_inside] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)

# ============================================================================
# 2. Triangle Pattern 三角形整理突破策略
# ============================================================================

class TrianglePattern(BreakoutStrategy):
    """
    三角形整理突破策略
    
    識別上升三角形、下降三角形、對稱三角形的突破：
    - 上升三角形：水平阻力 + 上升支撐 → 看漲突破
    - 下降三角形：水平支撐 + 下降阻力 → 看跌突破
    - 對稱三角形：收斂的支撐和阻力 → 等待突破方向
    
    適用場景：整理形態後的趨勢交易
    """
    
    def __init__(self, triangle_length: int = 5, breakout_confirm: int = 2):
        super().__init__('Triangle Pattern', {
            'triangle_length': triangle_length,
            'breakout_confirm': breakout_confirm
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        tri_len = self.params['triangle_length']
        confirm = self.params['breakout_confirm']
        
        high = data['high']
        low = data['low']
        close = data['close']
        
        signals = pd.Series(0, index=data.index)
        
        # 計算局部高點和低點
        local_high = high.rolling(tri_len, center=True).max()
        local_low = low.rolling(tri_len, center=True).min()
        
        # 檢測高點是否持平（水平阻力）
        high_flat = local_high.rolling(tri_len).std() < local_high.rolling(tri_len).mean() * 0.02
        
        # 檢測低點是否上升（上升支撐）
        low_rising = local_low > local_low.shift(tri_len)
        
        # 檢測高點是否下降（下降阻力）
        high_falling = local_high < local_high.shift(tri_len)
        
        # 檢測低點是否持平（水平支撐）
        low_flat = local_low.rolling(tri_len).std() < local_low.rolling(tri_len).mean() * 0.02
        
        # 上升三角形：水平阻力 + 上升支撐
        ascending_triangle = high_flat & low_rising
        
        # 下降三角形：下降阻力 + 水平支撐
        descending_triangle = high_falling & low_flat
        
        # 突破確認
        resistance = local_high.shift(tri_len)
        support = local_low.shift(tri_len)
        
        # 連續確認天數
        confirm_up = close.rolling(confirm).min() > resistance
        confirm_down = close.rolling(confirm).max() < support
        
        # 上升三角形突破 → 買入
        signals[ascending_triangle & confirm_up] = 1
        
        # 下降三角形突破 → 賣出
        signals[descending_triangle & confirm_down] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)

# ============================================================================
# 註冊所有突破最終策略
# ============================================================================

BREAKOUT_FINAL_STRATEGIES = {
    'inside_bar': InsideBarBreakout,
    'triangle': TrianglePattern,
}

__all__ = ['BREAKOUT_FINAL_STRATEGIES', 'InsideBarBreakout', 'TrianglePattern']
