"""
配对交易策略 - 统计套利

基于协整检验找出配对的标的，进行均值回归交易
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, List
from datetime import datetime
from scipy import stats


class PairsTrading:
    """配对交易策略"""
    
    def __init__(
        self,
        lookback: int = 60,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.5,
        stoploss_zscore: float = 3.0
    ):
        """
        初始化配对交易策略
        
        Args:
            lookback: 回溯天数
            entry_zscore: 开仓 Z 值阈值
            exit_zscore: 平仓 Z 值阈值
            stoploss_zscore: 止损 Z 值阈值
        """
        self.lookback = lookback
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.stoploss_zscore = stoploss_zscore
        self.hedge_ratio: Optional[float] = None
        self.mean_spread: Optional[float] = None
        self.std_spread: Optional[float] = None
    
    def check_cointegration(
        self,
        price_a: pd.Series,
        price_b: pd.Series,
        confidence: float = 0.05
    ) -> Tuple[bool, float]:
        """
        检验两个价格序列是否协整
        
        Returns:
            is_cointegrated: 是否协整
            p_value: 检验 p 值
        """
        # Engle-Granger 协整检验
        model = np.polyfit(price_a, price_b, 1)
        spread = price_b - model[0] * price_a
        
        # ADF 检验
        from statsmodels.tsa.stattools import adfuller
        adf_result = adfuller(spread.dropna())
        
        p_value = adf_result[1]
        is_cointegrated = p_value < confidence
        
        return is_cointegrated, p_value
    
    def calculate_hedge_ratio(self, price_a: pd.Series, price_b: pd.Series) -> float:
        """计算对冲比率"""
        # 使用 OLS 回归
        model = np.polyfit(price_a, price_b, 1)
        return model[0]
    
    def calculate_spread(
        self,
        price_a: pd.Series,
        price_b: pd.Series,
        hedge_ratio: Optional[float] = None
    ) -> pd.Series:
        """计算价差"""
        if hedge_ratio is None:
            hedge_ratio = self.hedge_ratio
        
        if hedge_ratio is None:
            raise ValueError("需要指定对冲比率")
        
        return price_b - hedge_ratio * price_a
    
    def calculate_zscore(self, spread: pd.Series) -> pd.Series:
        """计算 Z 值"""
        self.mean_spread = spread.rolling(window=self.lookback).mean()
        self.std_spread = spread.rolling(window=self.lookback).std()
        
        zscore = (spread - self.mean_spread) / self.std_spread
        return zscore
    
    def generate_signal(
        self,
        price_a: pd.Series,
        price_b: pd.Series
    ) -> Dict:
        """
        生成交易信号
        
        Returns:
            信号字典
        """
        if len(price_a) < self.lookback or len(price_b) < self.lookback:
            return {
                "strategy": "pairs_trading",
                "signal": 0,
                "action": "WAIT",
                "reason": "数据不足"
            }
        
        # 计算对冲比率
        self.hedge_ratio = self.calculate_hedge_ratio(
            price_a.iloc[-self.lookback:],
            price_b.iloc[-self.lookback:]
        )
        
        # 计算价差
        spread = self.calculate_spread(price_a, price_b, self.hedge_ratio)
        
        # 计算 Z 值
        zscore = self.calculate_zscore(spread)
        current_zscore = zscore.iloc[-1]
        
        # 生成信号
        signal = 0
        action = "HOLD"
        
        if current_zscore > self.entry_zscore:
            # 价差过高：卖出 B，买入 A
            signal = -1
            action = "SELL_B_BUY_A"
        elif current_zscore < -self.entry_zscore:
            # 价差过低：买入 B，卖出 A
            signal = 1
            action = "BUY_B_SELL_A"
        elif abs(current_zscore) < self.exit_zscore:
            # 价差回归：平仓
            signal = 0
            action = "CLOSE"
        
        # 止损检查
        if abs(current_zscore) > self.stoploss_zscore:
            action = "STOP_LOSS"
        
        return {
            "strategy": "pairs_trading",
            "signal": signal,
            "action": action,
            "zscore": float(current_zscore),
            "hedge_ratio": float(self.hedge_ratio),
            "spread": float(spread.iloc[-1]),
            "mean_spread": float(self.mean_spread.iloc[-1]) if not np.isnan(self.mean_spread.iloc[-1]) else None,
            "std_spread": float(self.std_spread.iloc[-1]) if not np.isnan(self.std_spread.iloc[-1]) else None,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
    
    def backtest(
        self,
        price_a: pd.Series,
        price_b: pd.Series,
        initial_capital: float = 100000
    ) -> pd.DataFrame:
        """
        回测配对交易策略
        
        Returns:
            回测结果 DataFrame
        """
        signals = []
        
        for i in range(self.lookback, len(price_a)):
            signal = self.generate_signal(
                price_a.iloc[:i],
                price_b.iloc[:i]
            )
            signals.append(signal)
        
        results = pd.DataFrame(signals)
        
        # 计算累积收益
        results['cumulative_return'] = (results['zscore'].shift(1) - results['zscore']).cumsum()
        
        return results


# ════════════════════════════════════════════════════════════
# 使用示例
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 创建示例数据
    np.random.seed(42)
    n = 500
    
    # 生成两个相关的价格序列
    base = np.random.randn(n).cumsum() + 100
    price_a = pd.Series(base + np.random.randn(n) * 0.5)
    price_b = pd.Series(base * 1.2 + np.random.randn(n) * 0.3)
    
    # 创建策略
    strategy = PairsTrading(lookback=60, entry_zscore=2.0)
    
    # 协整检验
    is_coint, p_value = strategy.check_cointegration(price_a, price_b)
    print(f"协整检验：{'通过' if is_coint else '不通过'} (p={p_value:.4f})")
    
    # 生成信号
    signal = strategy.generate_signal(price_a, price_b)
    print(f"\n交易信号：{signal}")
