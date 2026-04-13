"""
StocksX 策略庫
130+ 專業交易策略
"""

from .base_strategy import BaseStrategy, TrendFollowingStrategy, OscillatorStrategy, BreakoutStrategy
from .strategy_factory import StrategyFactory, get_strategy, list_all_strategies

__version__ = "1.0.0"
__all__ = [
    "BaseStrategy",
    "TrendFollowingStrategy",
    "OscillatorStrategy",
    "BreakoutStrategy",
    "StrategyFactory",
    "get_strategy",
    "list_all_strategies",
]
