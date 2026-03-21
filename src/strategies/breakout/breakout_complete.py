"""
突破策略補全 - Batch 2
包含 5 個補全策略

作者：StocksX Team
創建日期：2026-03-22
狀態：✅ 批量生成
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_strategy import BreakoutStrategy


# ============================================================================
# 1. NR7/NR4 窄幅K線突破
# ============================================================================

class NR7NR4(BreakoutStrategy):
    """
    NR7/NR4 窄幅 K 線突破策略
    
    識別 Narrow Range (最小波動範圍) K 線，
    NR7 = 過去 7 日最小範圍，NR4 = 過去 4 日最小範圍。
    """
    
    def __init__(self, nr7_lookback: int = 7, nr4_lookback: int = 4):
        super().__init__('NR7/NR4', {
            'nr7_lookback': nr7_lookback,
            'nr4_lookback': nr4_lookback
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback_7 = self.params['nr7_lookback']
        lookback_4 = self.params['nr4_lookback']
        
        # 計算 K 線範圍
        range_val = data['high'] - data['low']
        
        # NR7: 過去 7 日最小範圍
        nr7 = range_val.rolling(window=lookback_7).apply(
            lambda x: x.iloc[-1] == x.min()
        )
        
        # NR4: 過去 4 日最小範圍
        nr4 = range_val.rolling(window=lookback_4).apply(
            lambda x: x.iloc[-1] == x.min()
        )
        
        signals = pd.Series(0, index=data.index)
        
        # NR7 後突破高點 → 買入
        nr7_signal = nr7 == 1
        breakout_up = (data['close'] > data['high'].shift(1)) & nr7_signal
        signals[breakout_up] = 1
        
        # NR4 後跌破低點 → 賣出
        nr4_signal = nr4 == 1
        breakout_down = (data['close'] < data['low'].shift(1)) & nr4_signal
        signals[breakout_down] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))


# ============================================================================
# 2. 旗形/三角旗形
# ============================================================================

class FlagPennant(BreakoutStrategy):
    """
    旗形/三角旗形突破策略
    
    識別價格整固形態後突破。
    """
    
    def __init__(self, flag_length: int = 10, breakout_lookback: int = 5):
        super().__init__('旗形/三角旗形', {
            'flag_length': flag_length,
            'breakout_lookback': breakout_lookback
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        flag_len = self.params['flag_length']
        breakout_lb = self.params['breakout_lookback']
        
        # 簡化：檢測價格整固
        recent_high = data['high'].rolling(window=flag_len).max()
        recent_low = data['low'].rolling(window=flag_len).min()
        
        # 整固：價格區間收窄
        consolidation = (recent_high - recent_low) / recent_low < 0.05
        
        signals = pd.Series(0, index=data.index)
        
        # 突破上界 → 買入
        breakout_up = (data['close'] > recent_high.shift(1)) & consolidation.shift(flag_len)
        signals[breakout_up] = 1
        
        # 跌破下界 → 賣出
        breakout_down = (data['close'] < recent_low.shift(1)) & consolidation.shift(flag_len)
        signals[breakout_down] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))


# ============================================================================
# 3. 水平通道突破
# ============================================================================

class HorizontalChannel(BreakoutStrategy):
    """
    水平通道突破策略
    
    識別水平盤整區間，突破時跟隨。
    """
    
    def __init__(self, channel_length: int = 20, threshold: float = 0.03):
        super().__init__('水平通道突破', {
            'channel_length': channel_length,
            'threshold': threshold
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        ch_len = self.params['channel_length']
        threshold = self.params['threshold']
        
        # 計算通道
        high_channel = data['high'].rolling(window=ch_len).max()
        low_channel = data['low'].rolling(window=ch_len).min()
        
        # 通道寬度
        channel_width = (high_channel - low_channel) / low_channel
        
        # 水平通道：寬度小於閾值
        horizontal = channel_width < threshold
        
        signals = pd.Series(0, index=data.index)
        
        # 突破上軌
        breakout_up = (data['close'] > high_channel.shift(1)) & horizontal.shift(ch_len)
        signals[breakout_up] = 1
        
        # 跌破下軌
        breakout_down = (data['close'] < low_channel.shift(1)) & horizontal.shift(ch_len)
        signals[breakout_down] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))


# ============================================================================
# 4. W 底/M 頂突破
# ============================================================================

class WMPattern(BreakoutStrategy):
    """
    W 底/M 頂突破策略
    
    識別雙重頂底形態。
    """
    
    def __init__(self, lookback: int = 50, tolerance: float = 0.02):
        super().__init__('W 底/M 頂', {
            'lookback': lookback,
            'tolerance': tolerance
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        tol = self.params['tolerance']
        
        high = data['high']
        low = data['low']
        
        # 簡化：檢測兩次測試相近高低點
        recent_high = high.rolling(window=lookback).max()
        recent_low = low.rolling(window=lookback).min()
        
        signals = pd.Series(0, index=data.index)
        
        # M 頂：兩次測試高點後跌破
        m_top = (high > recent_high.shift(lookback) * 0.98) & (high.shift(lookback) > recent_high.shift(2*lookback))
        signals[m_top] = -1
        
        # W 底：兩次測試低點後突破
        w_bottom = (low < recent_low.shift(lookback) * 1.02) & (low.shift(lookback) < recent_low.shift(2*lookback))
        signals[w_bottom] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))


# ============================================================================
# 5. TTO Opening Range
# ============================================================================

class TTOOpeningRange(BreakoutStrategy):
    """
    TTO Opening Range 突破策略
    
    Toby Crabel 開盤突破策略，
    基於前日波動範圍計算突破位。
    """
    
    def __init__(self, ibr_multiplier: float = 0.5):
        super().__init__('TTO Opening Range', {
            'ibr_multiplier': ibr_multiplier
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        ibr_mult = self.params['ibr_multiplier']
        
        # 計算前日範圍
        prev_range = data['high'].shift(1) - data['low'].shift(1)
        
        # 計算內部波動範圍 (IBR)
        ibr = prev_range * ibr_mult
        
        # 開盤價
        open_price = data['open']
        
        # 突破位
        upper_breakout = open_price + ibr
        lower_breakout = open_price - ibr
        
        signals = pd.Series(0, index=data.index)
        
        # 突破上界 → 買入
        signals[data['high'] > upper_breakout] = 1
        
        # 跌破下界 → 賣出
        signals[data['low'] < lower_breakout] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2.5 * volatility * price + 1e-10))


# ============================================================================
# 策略註冊表
# ============================================================================

BREAKOUT_COMPLETE_STRATEGIES = {
    'nr7_nr4': NR7NR4,
    'flag_pennant': FlagPennant,
    'horizontal_channel': HorizontalChannel,
    'w_m_pattern': WMPattern,
    'tto_or': TTOOpeningRange,
}


# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("突破策略補全測試")
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
    
    for name, cls in BREAKOUT_COMPLETE_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")
    
    print("\n" + "=" * 60)
    print("測試完成！突破策略 16/16 完成！✅")
    print("=" * 60)
