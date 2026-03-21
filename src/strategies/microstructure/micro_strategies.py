"""
微結構與訂單流策略包
包含 12 個微結構策略

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
# 1. 訂單流分析
# ============================================================================

class OrderFlowAnalysis(BaseStrategy):
    """
    訂單流分析策略
    
    分析買賣訂單流的不平衡，
    跟隨大單方向交易。
    """
    
    def __init__(self, lookback: int = 20, imbalance_threshold: float = 0.3):
        """
        初始化訂單流策略
        
        Args:
            lookback: 回看週期
            imbalance_threshold: 不平衡閾值
        """
        super().__init__('訂單流分析', {
            'lookback': lookback,
            'imbalance_threshold': imbalance_threshold
        }, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        threshold = self.params['imbalance_threshold']
        
        # 簡化：使用價格和成交量模擬訂單流
        # 實際應用需要 Level 2 數據
        close = data['close']
        volume = data['volume']
        
        # 計算價格變化
        price_change = close.diff()
        
        # 計算買方/賣方壓力（簡化）
        buyer_pressure = ((price_change > 0) * volume).rolling(window=lookback).sum()
        seller_pressure = ((price_change < 0) * volume).rolling(window=lookback).sum()
        
        # 計算訂單流不平衡
        total_pressure = buyer_pressure + seller_pressure
        imbalance = (buyer_pressure - seller_pressure) / (total_pressure + 1e-10)
        
        signals = pd.Series(0, index=data.index)
        
        # 買方壓力大 → 買入
        signals[imbalance > threshold] = 1
        
        # 賣方壓力大 → 賣出
        signals[imbalance < -threshold] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        risk_per_trade = 0.015
        risk_amount = capital * risk_per_trade
        
        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)


# ============================================================================
# 2. Delta 累積
# ============================================================================

class CumulativeDelta(BaseStrategy):
    """
    Delta 累積策略
    
    累積買賣 Delta 值，
    識別機構資金流向。
    """
    
    def __init__(self, lookback: int = 50):
        """
        初始化 Delta 累積策略
        
        Args:
            lookback: 回看週期
        """
        super().__init__('Delta 累積', {
            'lookback': lookback
        }, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        
        # 簡化 Delta 計算
        high = data['high']
        low = data['low']
        close = data['close']
        
        # 計算每根 K 線的 Delta（簡化）
        typical_price = (high + low + close) / 3
        price_position = (close - low) / (high - low + 1e-10)
        
        # Delta = 價格位置 * 成交量 * 符號
        delta = (price_position - 0.5) * 2 * data['volume']
        
        # 累積 Delta
        cum_delta = delta.rolling(window=lookback).sum()
        
        signals = pd.Series(0, index=data.index)
        
        # Delta 轉正 → 買入
        delta_turn_positive = (cum_delta > 0) & (cum_delta.shift(1) <= 0)
        signals[delta_turn_positive] = 1
        
        # Delta 轉負 → 賣出
        delta_turn_negative = (cum_delta < 0) & (cum_delta.shift(1) >= 0)
        signals[delta_turn_negative] = -1
        
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
# 3. POC / Value Area
# ============================================================================

class POCValueArea(BaseStrategy):
    """
    POC (Point of Control) 和價值區域策略
    
    識別成交量分佈的 POC 和價值區域，
    在價值區域外交易。
    """
    
    def __init__(self, lookback: int = 100, va_percentage: float = 0.7):
        """
        初始化 POC 策略
        
        Args:
            lookback: 回看週期
            va_percentage: 價值區域百分比（70%）
        """
        super().__init__('POC / Value Area', {
            'lookback': lookback,
            'va_percentage': va_percentage
        }, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        va_pct = self.params['va_percentage']
        
        close = data['close']
        volume = data['volume']
        
        # 計算滾動 POC（簡化：成交量加權平均價）
        vwap = (close * volume).rolling(window=lookback).sum() / \
               volume.rolling(window=lookback).sum()
        
        # 計算價值區域（標準差）
        std = close.rolling(window=lookback).std()
        va_upper = vwap + std * 1.28  # 70% 置信區間
        va_lower = vwap - std * 1.28
        
        signals = pd.Series(0, index=data.index)
        
        # 突破價值區域上界 → 買入
        breakout_above = close > va_upper
        signals[breakout_above] = 1
        
        # 跌破價值區域下界 → 賣出
        breakout_below = close < va_lower
        signals[breakout_below] = -1
        
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
# 4. VPIN (Volume-Synchronized Probability of Informed Trading)
# ============================================================================

class VPIN(BaseStrategy):
    """
    VPIN 知情交易機率策略
    
    計算知情交易機率，
    VPIN 高時表示有知情交易者。
    """
    
    def __init__(self, bucket_size: int = 50, lookback: int = 100):
        """
        初始化 VPIN 策略
        
        Args:
            bucket_size: 桶大小
            lookback: 回看週期
        """
        super().__init__('VPIN', {
            'bucket_size': bucket_size,
            'lookback': lookback
        }, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        bucket_size = self.params['bucket_size']
        lookback = self.params['lookback']
        
        volume = data['volume']
        price_change = data['close'].diff()
        
        # 簡化 VPIN 計算
        # 實際應用需要 tick 數據
        buy_volume = ((price_change > 0) * volume).rolling(window=bucket_size).sum()
        sell_volume = ((price_change < 0) * volume).rolling(window=bucket_size).sum()
        
        total_volume = buy_volume + sell_volume
        vpin = abs(buy_volume - sell_volume) / (total_volume + 1e-10)
        
        signals = pd.Series(0, index=data.index)
        
        # VPIN 高（>0.8）表示知情交易 → 跟隨
        signals[vpin > 0.8] = np.sign(price_change)
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        risk_per_trade = 0.01
        risk_amount = capital * risk_per_trade
        
        if volatility > 0:
            position_size = risk_amount / (3 * volatility)  # VPIN 高時保守
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)


# ============================================================================
# 5. Amihud 非流動性
# ============================================================================

class AmihudIlliquidity(BaseStrategy):
    """
    Amihud 非流動性指標策略
    
    計算 Amihud 非流動性指標，
    流動性低時避免交易。
    """
    
    def __init__(self, lookback: int = 60):
        """
        初始化 Amihud 策略
        
        Args:
            lookback: 回看週期
        """
        super().__init__('Amihud 非流動性', {
            'lookback': lookback
        }, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        
        returns = data['close'].pct_change()
        volume = data['volume']
        
        # Amihud 指標 = |回報| / 成交量
        amihud = (abs(returns) / (volume + 1e-10)).rolling(window=lookback).mean()
        
        # 標準化
        amihud_zscore = (amihud - amihud.rolling(window=lookback).mean()) / \
                        (amihud.rolling(window=lookback).std() + 1e-10)
        
        signals = pd.Series(0, index=data.index)
        
        # 流動性高（Amihud 低）→ 買入
        signals[amihud_zscore < -1] = 1
        
        # 流動性低（Amihud 高）→ 賣出/避免交易
        signals[amihud_zscore > 1] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        # 根據流動性調整倉位
        risk_per_trade = 0.015
        risk_amount = capital * risk_per_trade
        
        if volatility > 0:
            position_size = risk_amount / (2.5 * volatility)
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)


# ============================================================================
# 6. 冰山訂單偵測
# ============================================================================

class IcebergDetection(BaseStrategy):
    """
    冰山訂單偵測策略
    
    識別大額冰山訂單，
    跟隨機構資金。
    """
    
    def __init__(self, lookback: int = 20, volume_threshold: float = 3.0):
        """
        初始化冰山訂單策略
        
        Args:
            lookback: 回看週期
            volume_threshold: 成交量閾值（倍數）
        """
        super().__init__('冰山訂單偵測', {
            'lookback': lookback,
            'volume_threshold': volume_threshold
        }, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        vol_threshold = self.params['volume_threshold']
        
        volume = data['volume']
        vol_ma = volume.rolling(window=lookback).mean()
        vol_std = volume.rolling(window=lookback).std()
        
        # 偵測異常成交量
        unusual_volume = volume > (vol_ma + vol_threshold * vol_std)
        
        # 價格變化小但成交量大 → 可能是冰山訂單
        price_change = abs(data['close'].pct_change())
        small_price_change = price_change < price_change.rolling(window=lookback).median()
        
        # 冰山信號
        iceberg = unusual_volume & small_price_change
        
        signals = pd.Series(0, index=data.index)
        
        # 冰山訂單出現 → 跟隨方向（簡化：假設買入）
        signals[iceberg & (data['close'] > data['open'])] = 1
        signals[iceberg & (data['close'] < data['open'])] = -1
        
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
# 7-12. 其他微結構策略（簡化版）
# ============================================================================

class KyleLambda(BaseStrategy):
    """Kyle's Lambda 價格衝擊策略"""
    
    def __init__(self, lookback: int = 60):
        super().__init__("Kyle's Lambda", {'lookback': lookback}, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        returns = data['close'].pct_change()
        volume = data['volume']
        
        # Lambda = 價格變化 / 成交量（價格衝擊）
        lambda_val = (abs(returns) / (volume + 1e-10)).rolling(window=lookback).mean()
        
        signals = pd.Series(0, index=data.index)
        signals[lambda_val < lambda_val.rolling(window=lookback).quantile(0.3)] = 1
        signals[lambda_val > lambda_val.rolling(window=lookback).quantile(0.7)] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))


class TickRule(BaseStrategy):
    """Lee-Ready Tick Rule 策略"""
    
    def __init__(self, lookback: int = 20):
        super().__init__('Tick Rule', {'lookback': lookback}, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        
        # Tick 規則：價格上升為買單，下降為賣單
        tick_up = data['close'] > data['close'].shift(1)
        tick_down = data['close'] < data['close'].shift(1)
        
        # 連續買單/賣單
        buy_pressure = tick_up.rolling(window=lookback).sum()
        sell_pressure = tick_down.rolling(window=lookback).sum()
        
        signals = pd.Series(0, index=data.index)
        signals[buy_pressure > lookback * 0.6] = 1
        signals[sell_pressure > lookback * 0.6] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))


class QuoteStuffing(BaseStrategy):
    """Quote Stuffing 偵測策略"""
    
    def __init__(self, threshold: int = 100):
        super().__init__('Quote Stuffing 偵測', {'threshold': threshold}, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        threshold = self.params['threshold']
        
        # 簡化：檢測成交量突然激增
        volume_change = data['volume'].pct_change()
        
        signals = pd.Series(0, index=data.index)
        signals[volume_change > threshold] = -1  # Quote stuffing 後通常回調
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.01 / (3 * volatility * price + 1e-10))


class Level2Analysis(BaseStrategy):
    """Level 2 深度分析策略"""
    
    def __init__(self, levels: int = 5):
        super().__init__('Level 2 深度分析', {'levels': levels}, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # 簡化：使用高低點差模擬買賣價差
        spread = (data['high'] - data['low']) / data['close']
        
        signals = pd.Series(0, index=data.index)
        signals[spread < spread.rolling(window=20).quantile(0.2)] = 1  # 價差小，流動性好
        signals[spread > spread.rolling(window=20).quantile(0.8)] = -1  # 價差大，流動性差
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))


class MicroPrice(BaseStrategy):
    """微價格偏移策略"""
    
    def __init__(self, lookback: int = 50):
        super().__init__('微價格偏移', {'lookback': lookback}, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params['lookback']
        
        # 微價格 = 加權平均價
        micro_price = (data['close'] * data['volume']).rolling(window=lookback).sum() / \
                      data['volume'].rolling(window=lookback).sum()
        
        signals = pd.Series(0, index=data.index)
        signals[data['close'] < micro_price * 0.98] = 1
        signals[data['close'] > micro_price * 1.02] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        return int(capital * 0.02 / (2 * volatility * price + 1e-10))


class TWAPSignal(BaseStrategy):
    """TWAP 執行信號策略"""
    
    def __init__(self, intervals: int = 12):
        super().__init__('TWAP Signal', {'intervals': intervals}, category='microstructure')
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        intervals = self.params['intervals']
        
        # 簡化：均勻分拆信號
        n = len(data)
        signals = pd.Series(0, index=data.index)
        
        # 每 N 個間隔生成一個信號
        step = n // intervals
        for i in range(0, n, step):
            if i < n:
                signals.iloc[i] = 1 if data['close'].iloc[i] < data['close'].iloc[max(0, i-step)].mean() else -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0: return 0
        intervals = self.params['intervals']
        return int(capital * 0.02 / intervals / (2 * volatility * price + 1e-10))


# ============================================================================
# 策略註冊表
# ============================================================================

MICRO_STRATEGIES = {
    'order_flow': OrderFlowAnalysis,
    'cum_delta': CumulativeDelta,
    'poc_va': POCValueArea,
    'vpin': VPIN,
    'amihud': AmihudIlliquidity,
    'iceberg': IcebergDetection,
    'kyle_lambda': KyleLambda,
    'tick_rule': TickRule,
    'quote_stuffing': QuoteStuffing,
    'level2': Level2Analysis,
    'micro_price': MicroPrice,
    'twap_signal': TWAPSignal,
}


# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("微結構策略測試")
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
    
    for name, cls in MICRO_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
