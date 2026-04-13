"""風險管理策略模塊 - 12/12 完成（100%）"""

from .risk_strategies import RISK_STRATEGIES
from .advanced_risk_strategies import ADVANCED_RISK_STRATEGIES

# 合併所有風險管理策略（12 個）
ALL_RISK_STRATEGIES = {**RISK_STRATEGIES, **ADVANCED_RISK_STRATEGIES}

__all__ = ["ALL_RISK_STRATEGIES", "RISK_STRATEGIES", "ADVANCED_RISK_STRATEGIES"]
