"""趋势策略模块 - 18/18 完成（100%）"""

from .hull_ma_strategy import ADVANCED_TREND_STRATEGIES as HULL_TEMA
from .advanced_trend_strategies import ADVANCED_TREND_STRATEGIES

# 合并所有趋势策略（18 个）
ALL_TREND_STRATEGIES = {**HULL_TEMA, **ADVANCED_TREND_STRATEGIES}

__all__ = ['ALL_TREND_STRATEGIES', 'HULL_TEMA', 'ADVANCED_TREND_STRATEGIES']
