"""趋势策略模块"""

from .trend_strategies import TREND_STRATEGIES
from .hull_ma_strategy import ADVANCED_TREND_STRATEGIES as HULL_TEMA
from .advanced_trend_strategies import ADVANCED_TREND_STRATEGIES as ADVANCED7

# 合并所有趋势策略
ALL_TREND_STRATEGIES = {**TREND_STRATEGIES, **HULL_TEMA, **ADVANCED7}

__all__ = ['ALL_TREND_STRATEGIES', 'TREND_STRATEGIES', 'HULL_TEMA', 'ADVANCED7']
