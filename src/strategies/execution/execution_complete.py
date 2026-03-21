"""
執行算法補全 - Batch 2
包含 4 個執行策略

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
from base_strategy import BaseStrategy


# ============================================================================
# 1. 統計套利
# ============================================================================

class StatisticalArbitrage(BaseStrategy):
    """
    統計套利策略
    
    識別統計上錯誤定價的資產，
    進行配對交易。
    """
    
    def __init__(self, lookback: int = 60, z_threshold: float = 2.0):
        super().__init__('統計套利', {
            'lookback': lookback,
            'z_threshold': z_threshold
        }, category='execution')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        z_thresh = self.params['z_threshold']
        
        # 簡化：使用自身價格序列模擬配對
        returns = data['close'].pct_change()
        
        # 計算價差（與均值的偏離）
        spread = returns - returns.rolling(window=lookback).mean()
        spread_std = spread.rolling(window=lookback).std()
        zscore = spread / (spread_std + 1e-10)
        
        signals = pd.Series(0, index=data.index)
        
        # 價差低於 -2σ → 買入（預期回歸）
        signals[zscore < -z_thresh] = 1
        
        # 價差高於 +2σ → 賣出（預期回歸）
        signals[zscore > z_thresh] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.015 / (2.5 * volatility * price + 1e-10))


# ============================================================================
# 2. 延遲套利
# ============================================================================

class LatencyArbitrage(BaseStrategy):
    """
    延遲套利策略
    
    利用市場間價格發現的延遲，
    快速交易獲利。
    """
    
    def __init__(self, threshold: float = 0.005):
        super().__init__('延遲套利', {
            'threshold': threshold
        }, category='execution')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        threshold = self.params['threshold']
        
        # 簡化：檢測價格突然變化
        returns = data['close'].pct_change()
        
        signals = pd.Series(0, index=data.index)
        
        # 價格突然上漲 > 0.5% → 賣出（預期回調）
        signals[returns > threshold] = -1
        
        # 價格突然下跌 > -0.5% → 買入（預期反彈）
        signals[returns < -threshold] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.01 / (3 * volatility * price + 1e-10))


# ============================================================================
# 3. 閃崩偵測
# ============================================================================

class FlashCrashDetection(BaseStrategy):
    """
    閃崩偵測策略
    
    識別市場閃崩並反向交易，
    流動性恢復後獲利。
    """
    
    def __init__(self, crash_threshold: float = 0.05, recovery_threshold: float = 0.02):
        super().__init__('閃崩偵測', {
            'crash_threshold': crash_threshold,
            'recovery_threshold': recovery_threshold
        }, category='execution')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        crash_thresh = self.params['crash_threshold']
        recovery_thresh = self.params['recovery_threshold']
        
        returns = data['close'].pct_change()
        
        signals = pd.Series(0, index=data.index)
        
        # 閃崩：價格突然下跌 > 5%
        crash = returns < -crash_thresh
        signals[crash] = 1  # 反向買入
        
        # 恢復：價格反彈 > 2%
        recovery = returns > recovery_thresh
        signals[recovery & (returns.shift(1) < -crash_thresh)] = -1  # 平倉
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (3 * volatility * price + 1e-10))


# ============================================================================
# 4. ETF NAV 套利
# ============================================================================

class ETFNavArbitrage(BaseStrategy):
    """
    ETF NAV 套利策略
    
    當 ETF 價格與 NAV 偏離時，
    進行套利交易。
    """
    
    def __init__(self, premium_threshold: float = 0.01):
        super().__init__('ETF NAV 套利', {
            'premium_threshold': premium_threshold
        }, category='execution')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        threshold = self.params['premium_threshold']
        
        # 簡化：使用移動平均模擬 NAV
        nav = data['close'].rolling(window=20).mean()
        premium = (data['close'] - nav) / nav
        
        signals = pd.Series(0, index=data.index)
        
        # 溢價 > 1% → 賣出 ETF
        signals[premium > threshold] = -1
        
        # 折價 > -1% → 買入 ETF
        signals[premium < -threshold] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.01 / (2 * volatility * price + 1e-10))


# ============================================================================
# 策略註冊表
# ============================================================================

EXECUTION_COMPLETE_STRATEGIES = {
    'stat_arb': StatisticalArbitrage,
    'latency_arb': LatencyArbitrage,
    'flash_crash': FlashCrashDetection,
    'etf_nav': ETFNavArbitrage,
}


# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("執行算法補全測試")
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
    
    for name, cls in EXECUTION_COMPLETE_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")
    
    print("\n" + "=" * 60)
    print("測試完成！執行算法 8/8 完成！✅")
    print("=" * 60)
