"""
宏觀策略補全 - Batch 2
包含 7 個宏觀策略

作者：StocksX Team
創建日期：2026-03-22
狀態：✅ 批量生成
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from src.strategies.base_strategy import BaseStrategy

# ============================================================================
# 1. 利差交易 (Carry Trade)
# ============================================================================

class CarryTrade(BaseStrategy):
    """
    利差交易策略
    
    借入低利率貨幣，投資高利率貨幣，
    賺取利率差。
    """
    
    def __init__(self, rate_threshold: float = 0.02, lookback: int = 60):
        super().__init__('利差交易', {
            'rate_threshold': rate_threshold,
            'lookback': lookback
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        threshold = self.params['rate_threshold']
        lookback = self.params['lookback']
        
        # 簡化：使用價格動量模擬利率差
        # 實際應用需要利率數據
        returns = data['close'].pct_change()
        momentum = returns.rolling(window=lookback).mean()
        
        signals = pd.Series(0, index=data.index)
        
        # 動量強（模擬高利率）→ 買入
        signals[momentum > threshold] = 1
        
        # 動量弱（模擬低利率）→ 賣出
        signals[momentum < -threshold] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 2. 跨品種價差
# ============================================================================

class CrossCommoditySpread(BaseStrategy):
    """
    跨品種價差交易策略
    
    交易相關商品之間的價差，
    如金銀比、油金比等。
    """
    
    def __init__(self, lookback: int = 60, z_threshold: float = 2.0):
        super().__init__('跨品種價差', {
            'lookback': lookback,
            'z_threshold': z_threshold
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        z_thresh = self.params['z_threshold']
        
        # 簡化：使用自身價格序列模擬價差
        spread = data['close'] - data['close'].rolling(window=lookback).mean()
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
# 3. 動態避險比率
# ============================================================================

class DynamicHedgeRatio(BaseStrategy):
    """
    動態避險比率策略
    
    根據市場波動率動態調整避險比率。
    """
    
    def __init__(self, base_hedge: float = 0.5, vol_lookback: int = 30):
        super().__init__('動態避險比率', {
            'base_hedge': base_hedge,
            'vol_lookback': vol_lookback
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        base_hedge = self.params['base_hedge']
        vol_lb = self.params['vol_lookback']
        
        # 計算波動率
        returns = data['close'].pct_change()
        volatility = returns.rolling(window=vol_lb).std()
        
        # 動態避險比率：波動率高時增加避險
        hedge_ratio = base_hedge * (volatility / volatility.median())
        
        signals = pd.Series(0, index=data.index)
        
        # 避險比率高 → 減少曝險（賣出）
        signals[hedge_ratio > 0.8] = -1
        
        # 避險比率低 → 增加曝險（買入）
        signals[hedge_ratio < 0.3] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 4. 商品超級週期
# ============================================================================

class CommoditySuperCycle(BaseStrategy):
    """
    商品超級週期策略
    
    識別商品市場的長期週期（10-20 年），
    在週期底部買入，頂部賣出。
    """
    
    def __init__(self, short_ma: int = 120, long_ma: int = 480):
        super().__init__('商品超級週期', {
            'short_ma': short_ma,
            'long_ma': long_ma
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        short_ma = self.params['short_ma']
        long_ma = self.params['long_ma']
        
        # 計算長期移動平均
        sma_short = data['close'].rolling(window=short_ma).mean()
        sma_long = data['close'].rolling(window=long_ma).mean()
        
        signals = pd.Series(0, index=data.index)
        
        # 短期均線上穿長期均線 → 買入（新週期開始）
        cross_above = (sma_short > sma_long) & (sma_short.shift(1) < sma_long.shift(1))
        signals[cross_above] = 1
        
        # 短期均線下穿長期均線 → 賣出（週期結束）
        cross_below = (sma_short < sma_long) & (sma_short.shift(1) > sma_long.shift(1))
        signals[cross_below] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 5. 信用利差交易
# ============================================================================

class CreditSpread(BaseStrategy):
    """
    信用利差交易策略
    
    交易投資級與高收益債券的信用利差。
    """
    
    def __init__(self, lookback: int = 60, z_threshold: float = 1.5):
        super().__init__('信用利差交易', {
            'lookback': lookback,
            'z_threshold': z_threshold
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        z_thresh = self.params['z_threshold']
        
        # 簡化：使用波動率模擬信用利差
        volatility = data['close'].pct_change().rolling(window=lookback).std()
        
        # 標準化
        vol_zscore = (volatility - volatility.rolling(window=lookback).mean()) / \
                     (volatility.rolling(window=lookback).std() + 1e-10)
        
        signals = pd.Series(0, index=data.index)
        
        # 信用利差擴大（波動率高）→ 賣出
        signals[vol_zscore > z_thresh] = -1
        
        # 信用利差收窄（波動率低）→ 買入
        signals[vol_zscore < -z_thresh] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.015 / (2.5 * volatility * price + 1e-10))

# ============================================================================
# 6. 黃金/實際利率
# ============================================================================

class GoldRealRate(BaseStrategy):
    """
    黃金/實際利率套利策略
    
    黃金價格與實際利率負相關，
    實際利率下降時買入黃金。
    """
    
    def __init__(self, lookback: int = 60):
        super().__init__('黃金/實際利率', {
            'lookback': lookback
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        
        # 簡化：使用價格動量模擬實際利率變化
        # 實際利率 = 名義利率 - 通脹預期
        momentum = data['close'].pct_change(periods=lookback)
        
        signals = pd.Series(0, index=data.index)
        
        # 動量為正（模擬實際利率下降）→ 買入黃金
        signals[momentum > 0] = 1
        
        # 動量為負（模擬實際利率上升）→ 賣出黃金
        signals[momentum < 0] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 7. 跨資產風險平價
# ============================================================================

class CrossAssetRiskParity(BaseStrategy):
    """
    跨資產風險平價策略
    
    根據各資產風險貢獻分配權重，
    實現風險分散。
    """
    
    def __init__(self, lookback: int = 252, target_vol: float = 0.10):
        super().__init__('跨資產風險平價', {
            'lookback': lookback,
            'target_vol': target_vol
        }, category='macro')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        target_vol = self.params['target_vol']
        
        # 計算波動率
        returns = data['close'].pct_change()
        volatility = returns.rolling(window=lookback).std() * np.sqrt(252)
        
        # 風險平價權重（波動率倒數）
        risk_parity_weight = 1 / (volatility + 1e-10)
        risk_parity_weight = risk_parity_weight / risk_parity_weight.rolling(window=lookback).sum()
        
        signals = pd.Series(0, index=data.index)
        
        # 風險權重高 → 買入
        signals[risk_parity_weight > risk_parity_weight.rolling(window=lookback).mean() * 1.2] = 1
        
        # 風險權重低 → 賣出
        signals[risk_parity_weight < risk_parity_weight.rolling(window=lookback).mean() * 0.8] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))

# ============================================================================
# 策略註冊表
# ============================================================================

MACRO_COMPLETE_STRATEGIES = {
    'carry_trade': CarryTrade,
    'cross_commodity': CrossCommoditySpread,
    'dynamic_hedge': DynamicHedgeRatio,
    'super_cycle': CommoditySuperCycle,
    'credit_spread': CreditSpread,
    'gold_real_rate': GoldRealRate,
    'cross_asset_parity': CrossAssetRiskParity,
}

# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("宏觀策略補全測試")
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
    
    for name, cls in MACRO_COMPLETE_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")
    
    print("\n" + "=" * 60)
    print("測試完成！宏觀策略 12/12 完成！✅")
    print("=" * 60)
