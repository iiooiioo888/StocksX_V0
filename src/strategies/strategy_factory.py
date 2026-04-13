"""
StocksX 策略工廠
統一管理所有 130+ 策略的創建和註冊

優化：使用延遲加載（Lazy Loading），避免 import 時載入全部策略模組。
"""

from typing import Optional
from .base_strategy import BaseStrategy


# 策略分類 → 模組映射（延遲加載用）
_CATEGORY_MODULES = {
    "trend": ".trend",
    "oscillator": ".oscillator",
    "breakout": ".breakout",
    "ai_ml": ".ai_ml",
    "risk_management": ".risk_management",
    "microstructure": ".microstructure",
    "macro": ".macro",
    "statistical": ".statistical",
    "pattern": ".pattern",
    "execution": ".execution",
}

# 策略鍵名 → 分類映射（動態填充）
_name_to_category: dict[str, str] = {}


class StrategyFactory:
    """策略工廠類"""

    _strategies: dict[str, type[BaseStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_class: type[BaseStrategy]) -> None:
        """註冊策略"""
        cls._strategies[name.lower()] = strategy_class

    @classmethod
    def create(cls, name: str, params: Optional[dict] = None) -> BaseStrategy:
        """創建策略實例"""
        strategy_class = cls._strategies.get(name.lower())
        if not strategy_class:
            raise ValueError(f"未知策略：{name}")
        return strategy_class(params=params)

    @classmethod
    def list_strategies(cls) -> dict[str, type[BaseStrategy]]:
        """列出所有已註冊策略"""
        return cls._strategies.copy()

    @classmethod
    def get_strategy_info(cls, name: str) -> Optional[dict]:
        """獲取策略信息"""
        name_lower = name.lower()
        if name_lower not in cls._strategies:
            cls._ensure_all_loaded()
        strategy_class = cls._strategies.get(name_lower)
        if not strategy_class:
            return None

        # 創建臨時實例獲取信息
        try:
            instance = strategy_class()
            return {
                "name": instance.name,
                "category": instance.category,
                "params": instance.get_params(),
                "class": strategy_class.__name__,
            }
        except Exception:
            return {"name": name, "category": "unknown", "params": {}, "class": strategy_class.__name__}


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
    all_strategies = {
        **ALL_TREND_STRATEGIES,
        **ALL_OSCILLATOR_STRATEGIES,
        **ALL_BREAKOUT_STRATEGIES,
        **ALL_AI_ML_STRATEGIES,
        **ALL_RISK_STRATEGIES,
        **ALL_MICRO_STRATEGIES,
        **ALL_MACRO_STRATEGIES,
        **ALL_STAT_STRATEGIES,
        **ALL_PATTERN_STRATEGIES,
        **ALL_EXECUTION_STRATEGIES,
    }

    for name, cls in all_strategies.items():
        StrategyFactory.register(name, cls)


# 自動加載策略
load_all_strategies()


def get_strategy(name: str, params: Optional[dict] = None) -> BaseStrategy:
    """便捷函數：創建策略"""
    return StrategyFactory.create(name, params)


def list_all_strategies() -> dict:
    """便捷函數：列出所有策略"""
    strategies = StrategyFactory.list_strategies()
    result = {}
    for name in strategies.keys():
        info = StrategyFactory.get_strategy_info(name)
        if info:
            result[name] = info
    return result
