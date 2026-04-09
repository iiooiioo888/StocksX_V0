"""
風險管理策略包
包含 7 個風險管理策略

作者：StocksX Team
創建日期：2026-03-21
狀態：🔄 批量實作中
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from src.strategies.base_strategy import RiskManagementStrategy

# ============================================================================
# 1. 凱利公式倉位
# ============================================================================

class KellyCriterion(RiskManagementStrategy):
    """
    凱利公式倉位策略
    
    使用凱利公式計算最優倉位比例：
    f = W - (1-W)/R
    
    W = 勝率
    R = 盈虧比
    """
    
    def __init__(self, max_kelly: float = 0.25, lookback: int = 60):
        """
        初始化凱利公式策略
        
        Args:
            max_kelly: 最大凱利比例（默认 25%）
            lookback: 回看週期
        """
        super().__init__('凱利公式倉位', {
            'max_kelly': max_kelly,
            'lookback': lookback
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        max_kelly = self.params['max_kelly']
        
        # 計算歷史收益
        returns = data['close'].pct_change()
        
        # 計算勝率
        winning_trades = (returns > 0).rolling(window=lookback).sum()
        total_trades = returns.rolling(window=lookback).count()
        win_rate = winning_trades / (total_trades + 1)
        
        # 計算盈虧比
        avg_win = returns.rolling(window=lookback).apply(
            lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0
        )
        avg_loss = returns.rolling(window=lookback).apply(
            lambda x: abs(x[x < 0].mean()) if len(x[x < 0]) > 0 else 0
        )
        
        win_loss_ratio = avg_win / (avg_loss + 1e-10)
        
        # 凱利公式
        kelly = win_rate - (1 - win_rate) / (win_loss_ratio + 1e-10)
        kelly = kelly.clip(0, max_kelly)
        
        signals = pd.Series(0, index=data.index)
        
        # 凱利值高時買入
        signals[kelly > 0.1] = 1
        signals[kelly < 0.05] = 0
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小（使用凱利公式）"""
        if signal == 0:
            return 0
        
        # 凱利公式已經計算了最優比例
        kelly_pct = self.params['max_kelly']
        position_value = capital * kelly_pct
        
        shares = int(position_value / price)
        return max(0, shares)

# ============================================================================
# 2. 固定分數法
# ============================================================================

class FixedFractional(RiskManagementStrategy):
    """
    固定分數法倉位管理
    
    每筆交易固定風險資本的固定比例（如 2%）。
    """
    
    def __init__(self, risk_per_trade: float = 0.02, stop_loss_distance: float = 0.05):
        """
        初始化固定分數法
        
        Args:
            risk_per_trade: 每筆交易風險比例
            stop_loss_distance: 止損距離
        """
        super().__init__('固定分數法', {
            'risk_per_trade': risk_per_trade,
            'stop_loss_distance': stop_loss_distance
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（簡化：均線交叉）"""
        sma_20 = data['close'].rolling(window=20).mean()
        sma_50 = data['close'].rolling(window=50).mean()
        
        signals = pd.Series(0, index=data.index)
        
        # 黃金交叉
        cross_above = (sma_20 > sma_50) & (sma_20.shift(1) < sma_50.shift(1))
        signals[cross_above] = 1
        
        # 死亡交叉
        cross_below = (sma_20 < sma_50) & (sma_20.shift(1) > sma_50.shift(1))
        signals[cross_below] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        risk_per_trade = self.params['risk_per_trade']
        stop_loss_distance = self.params['stop_loss_distance']
        
        # 風險金額
        risk_amount = capital * risk_per_trade
        
        # 倉位大小
        if stop_loss_distance > 0:
            position_size = risk_amount / stop_loss_distance
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 3. 固定比率法
# ============================================================================

class FixedRatio(RiskManagementStrategy):
    """
    固定比率法倉位管理
    
    根據帳戶規模動態調整倉位，
    帳戶越大，每單位風險越小。
    """
    
    def __init__(self, base_capital: float = 100000, delta: float = 0.5):
        """
        初始化固定比率法
        
        Args:
            base_capital: 基準資本
            delta: 調整係數
        """
        super().__init__('固定比率法', {
            'base_capital': base_capital,
            'delta': delta
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        # 簡化：RSI 超賣超買
        rsi = self._calculate_rsi(data['close'], 14)
        
        signals = pd.Series(0, index=data.index)
        
        # 超賣買入
        signals[rsi < 30] = 1
        
        # 超買賣出
        signals[rsi > 70] = -1
        
        return signals
    
    def _calculate_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        """計算 RSI"""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        base_capital = self.params['base_capital']
        delta = self.params['delta']
        
        # 根據資本規模調整
        if capital > base_capital:
            risk_pct = 0.02 * (base_capital / capital) ** delta
        else:
            risk_pct = 0.02
        
        risk_amount = capital * risk_pct
        
        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 4. Anti-Martingale（反馬丁格爾）
# ============================================================================

class AntiMartingale(RiskManagementStrategy):
    """
    Anti-Martingale 倉位管理
    
    盈利時增加倉位，虧損時減少倉位，
    與馬丁格爾相反。
    """
    
    def __init__(self, base_risk: float = 0.01, step_multiplier: float = 0.5):
        """
        初始化反馬丁格爾
        
        Args:
            base_risk: 基準風險
            step_multiplier: 調整步長
        """
        super().__init__('Anti-Martingale', {
            'base_risk': base_risk,
            'step_multiplier': step_multiplier
        })
        
        self.consecutive_wins = 0
        self.consecutive_losses = 0
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        # 簡化：趨勢跟隨
        ema_12 = data['close'].ewm(span=12, adjust=False).mean()
        ema_26 = data['close'].ewm(span=26, adjust=False).mean()
        
        signals = pd.Series(0, index=data.index)
        
        # EMA 金叉
        cross_above = (ema_12 > ema_26) & (ema_12.shift(1) < ema_26.shift(1))
        signals[cross_above] = 1
        
        # EMA 死叉
        cross_below = (ema_12 < ema_26) & (ema_12.shift(1) > ema_26.shift(1))
        signals[cross_below] = -1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小（根據連勝調整）"""
        if signal == 0:
            return 0
        
        base_risk = self.params['base_risk']
        step = self.params['step_multiplier']
        
        # 連勝時增加風險（簡化：假設連勝）
        adjusted_risk = base_risk * (1 + self.consecutive_wins * step)
        adjusted_risk = min(adjusted_risk, 0.05)  # 最大 5%
        
        risk_amount = capital * adjusted_risk
        
        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 5. CVaR/ES 倉位控制
# ============================================================================

class CVaRPosition(RiskManagementStrategy):
    """
    CVaR（條件風險價值）倉位控制
    
    基於預期虧損（Expected Shortfall）計算倉位，
    比 VaR 更保守。
    """
    
    def __init__(self, confidence_level: float = 0.95, lookback: int = 252):
        """
        初始化 CVaR 策略
        
        Args:
            confidence_level: 置信水平
            lookback: 回看天數
        """
        super().__init__('CVaR 倉位控制', {
            'confidence_level': confidence_level,
            'lookback': lookback
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        
        # 計算波動率
        volatility = data['close'].pct_change().rolling(window=lookback).std()
        
        signals = pd.Series(0, index=data.index)
        
        # 波動率低時買入
        vol_low = volatility < volatility.rolling(window=lookback).quantile(0.3)
        signals[vol_low] = 1
        
        # 波動率高時賣出
        vol_high = volatility > volatility.rolling(window=lookback).quantile(0.7)
        signals[vol_high] = -1
        
        return signals
    
    def calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """計算 CVaR"""
        if len(returns) == 0:
            return 0
        
        var = returns.quantile(1 - confidence)
        cvar = returns[returns <= var].mean()
        
        return abs(cvar) if not pd.isna(cvar) else 0
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        confidence = self.params['confidence_level']
        max_cvar_pct = 0.05  # 最大 CVaR 比例
        
        # 簡化 CVaR 計算
        cvar_estimate = volatility * 2.33  # 99% 置信水平的近似
        
        if cvar_estimate > 0:
            position_pct = min(max_cvar_pct / cvar_estimate, 0.2)
        else:
            position_pct = 0.1
        
        position_value = capital * position_pct
        shares = int(position_value / price)
        
        return max(0, shares)

# ============================================================================
# 6. 最優停損
# ============================================================================

class OptimalStop(RiskManagementStrategy):
    """
    最優停損策略
    
    使用 ATR 和波動率動態計算最優止損位。
    """
    
    def __init__(self, atr_period: int = 14, atr_multiplier: float = 2.0):
        """
        初始化最優停損
        
        Args:
            atr_period: ATR 週期
            atr_multiplier: ATR 倍數
        """
        super().__init__('最優停損', {
            'atr_period': atr_period,
            'atr_multiplier': atr_multiplier
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        atr_period = self.params['atr_period']
        atr_mult = self.params['atr_multiplier']
        
        # 計算 ATR
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift(1))
        low_close = abs(data['low'] - data['close'].shift(1))
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_period).mean()
        
        # 計算止損位
        stop_loss = data['close'] - atr_mult * atr
        
        signals = pd.Series(0, index=data.index)
        
        # 價格接近止損位時賣出
        near_stop = (data['close'] - stop_loss) / atr < 0.5
        signals[near_stop] = -1
        
        # 價格遠離止損位時買入
        far_from_stop = (data['close'] - stop_loss) / atr > 2
        signals[far_from_stop] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade
        
        atr_mult = self.params['atr_multiplier']
        
        if volatility > 0:
            position_size = risk_amount / (atr_mult * volatility)
        else:
            position_size = 0
        
        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 7. 尾部風險對沖
# ============================================================================

class TailRiskHedge(RiskManagementStrategy):
    """
    尾部風險對沖策略
    
    在市場極端波動時自動對沖，
    保護組合免受黑天鵝事件影響。
    """
    
    def __init__(self, lookback: int = 252, tail_threshold: float = 0.05):
        """
        初始化尾部風險對沖
        
        Args:
            lookback: 回看天數
            tail_threshold: 尾部閾值
        """
        super().__init__('尾部風險對沖', {
            'lookback': lookback,
            'tail_threshold': tail_threshold
        })
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params['lookback']
        threshold = self.params['tail_threshold']
        
        # 計算歷史波動率
        returns = data['close'].pct_change()
        volatility = returns.rolling(window=lookback).std()
        
        # 計算波動率分位數
        vol_percentile = volatility.rolling(window=lookback).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1]
        )
        
        signals = pd.Series(0, index=data.index)
        
        # 波動率極高時（>95% 分位）對沖/賣出
        signals[vol_percentile > 0.95] = -1
        
        # 波動率正常時買入
        signals[(vol_percentile > 0.3) & (vol_percentile < 0.7)] = 1
        
        return signals
    
    def calculate_position_size(self, signal: int, capital: float, 
                                 price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0
        
        # 尾部風險時減少倉位
        if signal == -1:
            position_pct = 0.05  # 對沖時只留 5%
        else:
            position_pct = 0.15  # 正常時 15%
        
        position_value = capital * position_pct
        shares = int(position_value / price)
        
        return max(0, shares)

# ============================================================================
# 策略註冊表
# ============================================================================

RISK_STRATEGIES = {
    'kelly': KellyCriterion,
    'fixed_fractional': FixedFractional,
    'fixed_ratio': FixedRatio,
    'anti_martingale': AntiMartingale,
    'cvar': CVaRPosition,
    'optimal_stop': OptimalStop,
    'tail_hedge': TailRiskHedge,
}

# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("風險管理策略測試")
    print("=" * 60)
    
    # 創建測試數據
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
    
    # 測試各策略
    for name, cls in RISK_STRATEGIES.items():
        strategy = cls()
        signals = strategy.generate_signals(data)
        print(f"{name}: {signals.sum():+d} 信號")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
