"""
StocksX 策略工廠
統一管理所有 130+ 策略的創建和註冊

優化：使用延遲加載（Lazy Loading），避免 import 時載入全部策略模組。
"""

from typing import Dict, Type, Optional
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
    """策略工廠類（支持延遲加載）"""

    _strategies: Dict[str, Type[BaseStrategy]] = {}
    _loaded_categories: set[str] = set()

    @classmethod
    def _ensure_category_loaded(cls, category: str) -> None:
        """確保某分類的策略已加載。"""
        if category in cls._loaded_categories:
            return
        mod_path = _CATEGORY_MODULES.get(category)
        if not mod_path:
            return
        try:
            import importlib
            mod = importlib.import_module(mod_path, package="src.strategies")
            all_cls_name = f"ALL_{category.upper()}_STRATEGIES"
            all_strategies = getattr(mod, all_cls_name, None)
            if all_strategies:
                for name, strategy_cls in all_strategies.items():
                    cls._strategies[name.lower()] = strategy_cls
                    _name_to_category[name.lower()] = category
            cls._loaded_categories.add(category)
        except Exception:
            pass

    @classmethod
    def _ensure_all_loaded(cls) -> None:
        """確保所有策略已加載。"""
        for cat in _CATEGORY_MODULES:
            cls._ensure_category_loaded(cat)

    @classmethod
    def register(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        """註冊策略"""
        cls._strategies[name.lower()] = strategy_class

    @classmethod
    def create(cls, name: str, params: Optional[Dict] = None) -> BaseStrategy:
        """創建策略實例（自動加載所需分類）"""
        name_lower = name.lower()
        # 若尚未加載，嘗試按分類加載
        if name_lower not in cls._strategies:
            for cat in _CATEGORY_MODULES:
                cls._ensure_category_loaded(cat)
                if name_lower in cls._strategies:
                    break
        strategy_class = cls._strategies.get(name_lower)
        if not strategy_class:
            raise ValueError(f"未知策略：{name}")
        return strategy_class(params=params)

    @classmethod
    def list_strategies(cls) -> Dict[str, Type[BaseStrategy]]:
        """列出所有已註冊策略（確保全量加載）"""
        cls._ensure_all_loaded()
        return cls._strategies.copy()

    @classmethod
    def get_strategy_info(cls, name: str) -> Optional[Dict]:
        """獲取策略信息"""
        name_lower = name.lower()
        if name_lower not in cls._strategies:
            cls._ensure_all_loaded()
        strategy_class = cls._strategies.get(name_lower)
        if not strategy_class:
            return None

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


def load_all_strategies():
    """加載所有策略（向後兼容）"""
    StrategyFactory._ensure_all_loaded()


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
