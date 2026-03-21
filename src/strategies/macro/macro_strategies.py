"""
宏觀策略包
包含 11 個宏觀策略

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
# 1. 季節性策略
# ============================================================================

class SeasonalStrategy(BaseStrategy):
    """
    季節性策略
    
    基於歷史季節性模式交易，
    如「一月效應」、「聖誕老人行情」等。
    """
    
    def __init__(self, lookback_years: int = 10):
        """
        初始化季節性策略
        
        Args:
            lookback_years: 回看年數
        """
        super().__init__('季節性策略', {
            'lookback_years': lookback_years
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        signals = pd.Series(0, index=data.index)
        
        # 獲取月份
        month = data.index.month
        
        # 季節性模式（簡化）
        # 1 月、4 月、11 月、12 月通常表現較好
        bullish_months = [1, 4, 11, 12]
        bearish_months = [5, 6, 7, 8, 9]
        
        for m in bullish_months:
            signals[month == m] = 1
        
        for m in bearish_months:
            signals[month == m] = -1
        
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
# 2. 美元指數聯動
# ============================================================================

class DXYCorrelation(BaseStrategy):
    """
    美元指數聯動策略
    
    基於美元指數與資產的負相關性交易。
    """
    
    def __init__(self, lookback: int = 60, threshold: float = 0.5):
        """
        初始化美元指數聯動策略
        
        Args:
            lookback: 相關性計算週期
            threshold: 相關性閾值
        """
        super().__init__('美元指數聯動', {
            'lookback': lookback,
            'threshold': threshold
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（簡化版）"""
        lookback = self.params['lookback']
        threshold = self.params['threshold']
        
        # 計算價格變化率
        returns = data['close'].pct_change()
        
        # 計算動量
        momentum = returns.rolling(window=lookback).sum()
        
        signals = pd.Series(0, index=data.index)
        
        # 動量強時買入
        signals[momentum > threshold] = 1
        signals[momentum < -threshold] = -1
        
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
# 3. 收益率曲線策略
# ============================================================================

class YieldCurve(BaseStrategy):
    """
    收益率曲線策略
    
    基於長短期利差預測經濟週期，
    曲線倒掛時賣出，陡峭時買入。
    """
    
    def __init__(self, short_rate: float = 0.02, long_rate: float = 0.04):
        """
        初始化收益率曲線策略
        
        Args:
            short_rate: 短期利率基準
            long_rate: 長期利率基準
        """
        super().__init__('收益率曲線策略', {
            'short_rate': short_rate,
            'long_rate': long_rate
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        # 簡化：使用價格動量模擬利差變化
        short_ma = data['close'].rolling(window=10).mean()
        long_ma = data['close'].rolling(window=50).mean()
        
        spread = (short_ma - long_ma) / long_ma
        
        signals = pd.Series(0, index=data.index)
        
        # 利差擴大（曲線陡峭）→ 買入
        signals[spread > 0.02] = 1
        
        # 利差縮小（曲線平坦）→ 賣出
        signals[spread < -0.02] = -1
        
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
# 4. VIX 期貨交易
# ============================================================================

class VIXTrading(BaseStrategy):
    """
    VIX 恐慌指數交易策略
    
    VIX 高時賣出股票，VIX 低時買入。
    """
    
    def __init__(self, high_vix: float = 30, low_vix: float = 15):
        """
        初始化 VIX 策略
        
        Args:
            high_vix: 高 VIX 閾值
            low_vix: 低 VIX 閾值
        """
        super().__init__('VIX 期貨交易', {
            'high_vix': high_vix,
            'low_vix': low_vix
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        high_vix = self.params['high_vix']
        low_vix = self.params['low_vix']
        
        # 簡化：使用波動率模擬 VIX
        volatility = data['close'].pct_change().rolling(window=20).std() * np.sqrt(252) * 100
        
        signals = pd.Series(0, index=data.index)
        
        # VIX 高（恐慌）→ 賣出
        signals[volatility > high_vix] = -1
        
        # VIX 低（平靜）→ 買入
        signals[volatility < low_vix] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        # VIX 高時減少倉位
        if signal == -1:
            risk_per_trade = 0.01
        else:
            risk_per_trade = 0.02
        
        risk_amount = capital * risk_per_trade
        
        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)


# ============================================================================
# 5. 跨國權益輪動
# ============================================================================

class CountryRotation(BaseStrategy):
    """
    跨國權益輪動策略
    
    根據各國市場動量輪動配置。
    """
    
    def __init__(self, lookback: int = 3, momentum_period: int = 12):
        """
        初始化輪動策略
        
        Args:
            lookback: 回看月數
            momentum_period: 動量週期
        """
        super().__init__('跨國權益輪動', {
            'lookback': lookback,
            'momentum_period': momentum_period
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        momentum_period = self.params['momentum_period']
        
        # 計算動量
        momentum = data['close'].pct_change(periods=momentum_period)
        
        signals = pd.Series(0, index=data.index)
        
        # 動量為正時買入
        signals[momentum > 0] = 1
        
        # 動量為負時賣出
        signals[momentum < 0] = -1
        
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
# 策略註冊表
# ============================================================================

MACRO_STRATEGIES = {
    'seasonal': SeasonalStrategy,
    'dxy_corr': DXYCorrelation,
    'yield_curve': YieldCurve,
    'vix': VIXTrading,
    'country_rotation': CountryRotation,
}


# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("宏觀策略測試")
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
    
    for name, cls in MACRO_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
