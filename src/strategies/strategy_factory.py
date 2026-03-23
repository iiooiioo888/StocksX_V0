"""
StocksX 策略工廠
統一管理所有 130+ 策略的創建和註冊
"""

from typing import Dict, Type, Optional
from .base_strategy import BaseStrategy


class StrategyFactory:
    """策略工廠類"""
    
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    
    @classmethod
    def register(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        """註冊策略"""
        cls._strategies[name.lower()] = strategy_class
    
    @classmethod
    def create(cls, name: str, params: Optional[Dict] = None) -> BaseStrategy:
        """創建策略實例"""
        strategy_class = cls._strategies.get(name.lower())
        if not strategy_class:
            raise ValueError(f"未知策略：{name}")
        return strategy_class(params=params)
    
    @classmethod
    def list_strategies(cls) -> Dict[str, Type[BaseStrategy]]:
        """列出所有已註冊策略"""
        return cls._strategies.copy()
    
    @classmethod
    def get_strategy_info(cls, name: str) -> Optional[Dict]:
        """獲取策略信息"""
        strategy_class = cls._strategies.get(name.lower())
        if not strategy_class:
            return None
        
        # 創建臨時實例獲取信息
        try:
            instance = strategy_class()
            return {
                'name': instance.name,
                'category': instance.category,
                'params': instance.get_params(),
                'class': strategy_class.__name__
            }
        except Exception:
            return {
                'name': name,
                'category': 'unknown',
                'params': {},
                'class': strategy_class.__name__
            }


# 導入所有策略模塊
def load_all_strategies():
    """加載所有策略"""
    from .trend import ALL_TREND_STRATEGIES
    from .oscillator import ALL_OSCILLATOR_STRATEGIES
    from .breakout import ALL_BREAKOUT_STRATEGIES
    from .ai_ml import ALL_AI_ML_STRATEGIES
    from .risk_management import ALL_RISK_STRATEGIES
    from .microstructure import ALL_MICRO_STRATEGIES
    from .macro import ALL_MACRO_STRATEGIES
    from .statistical import ALL_STAT_STRATEGIES
    from .pattern import ALL_PATTERN_STRATEGIES
    from .execution import ALL_EXECUTION_STRATEGIES
    
    # 註冊所有策略
    all_strategies = {**ALL_TREND_STRATEGIES, **ALL_OSCILLATOR_STRATEGIES, 
                      **ALL_BREAKOUT_STRATEGIES, **ALL_AI_ML_STRATEGIES,
                      **ALL_RISK_STRATEGIES, **ALL_MICRO_STRATEGIES,
                      **ALL_MACRO_STRATEGIES, **ALL_STAT_STRATEGIES,
                      **ALL_PATTERN_STRATEGIES, **ALL_EXECUTION_STRATEGIES}
    
    for name, cls in all_strategies.items():
        StrategyFactory.register(name, cls)


# 自動加載策略
load_all_strategies()


def get_strategy(name: str, params: Optional[Dict] = None) -> BaseStrategy:
    """便捷函數：創建策略"""
    return StrategyFactory.create(name, params)


def list_all_strategies() -> Dict:
    """便捷函數：列出所有策略"""
    strategies = StrategyFactory.list_strategies()
    result = {}
    for name, cls in strategies.items():
        info = StrategyFactory.get_strategy_info(name)
        if info:
            result[name] = info
    return result
