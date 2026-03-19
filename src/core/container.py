"""
DI Container — 輕量依賴注入

取代散落的全局單例和 import 時副作用。
所有組件通過 Container 註冊和獲取，支持替換（測試、開發）。

用法：
    container = get_container()
    settings = container.get(Settings)        # → Settings 實例
    provider = container.get(MarketProvider)   # → CompositeProvider 實例
    cache = container.get(CacheBackend)        # → RedisCache / DictCache

替換（測試）：
    container.register(MarketProvider, MockProvider())
"""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Container:
    """
    輕量 DI 容器。

    支持：
    - 直接實例註冊：container.register(Settings, Settings())
    - 工廠註冊：container.register_factory(Settings, lambda: Settings())
    - 單例（預設）或多例
    """

    def __init__(self) -> None:
        self._instances: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}

    def register(self, cls: type[T], instance: T) -> None:
        """註冊具體實例."""
        self._instances[cls] = instance
        logger.debug("DI registered instance: %s", cls.__name__)

    def register_factory(self, cls: type[T], factory: Callable[[], T]) -> None:
        """註冊工廠函數（延遲建立）."""
        self._factories[cls] = factory
        logger.debug("DI registered factory: %s", cls.__name__)

    def get(self, cls: type[T]) -> T:
        """取得實例."""
        # 已有實例
        if cls in self._instances:
            return self._instances[cls]  # type: ignore[return-value]

        # 工廠建立
        if cls in self._factories:
            instance = self._factories[cls]()
            self._instances[cls] = instance  # 快取為單例
            return instance  # type: ignore[return-value]

        raise KeyError(f"No registration for {cls.__name__}. Register it first.")

    def has(self, cls: type) -> bool:
        return cls in self._instances or cls in self._factories

    def remove(self, cls: type) -> None:
        self._instances.pop(cls, None)
        self._factories.pop(cls, None)


# ─── 全域容器（延遲初始化所有組件） ───

_container: Container | None = None


def get_container() -> Container:
    """取得全域 DI 容器，自動註冊核心組件."""
    global _container
    if _container is not None:
        return _container

    _container = Container()

    # ── Settings（總是可用）──
    from .config import Settings

    _container.register_factory(Settings, Settings)

    # ── CacheBackend ──
    from .provider import CacheBackend, make_cache
    from .config import get_settings

    def _make_cache() -> CacheBackend:
        return make_cache(get_settings().cache.redis_url)

    _container.register_factory(CacheBackend, _make_cache)

    # ── CacheManager ──
    from .cache_manager import CacheManager

    def _make_cm() -> CacheManager:
        return CacheManager(redis_url=get_settings().cache.redis_url)

    _container.register_factory(CacheManager, _make_cm)

    # ── CompositeProvider ──
    from .adapters import CompositeProvider

    def _make_provider() -> CompositeProvider:
        composite = CompositeProvider()
        cache = _container.get(CacheBackend)
        try:
            from .adapters import CCXTProvider

            for ex in ["binance", "okx", "bybit", "bitget", "gate"]:
                try:
                    composite.add(CCXTProvider(ex, cache=cache))
                except Exception:
                    pass
        except Exception:
            pass
        try:
            from .adapters import YahooProvider

            composite.add(YahooProvider(cache=cache))
        except Exception:
            pass
        return composite

    from .provider import MarketProvider

    _container.register_factory(MarketProvider, _make_provider)

    # ── SignalBus ──
    from .signals import SignalBus, get_signal_bus

    _container.register_factory(SignalBus, get_signal_bus)

    # ── AlertManager ──
    from .alerts import AlertManager, get_alert_manager

    _container.register_factory(AlertManager, get_alert_manager)

    # ── TaskQueue ──
    from .tasks import ThreadTaskQueue, get_task_queue

    _container.register_factory(ThreadTaskQueue, get_task_queue)

    # ── BacktestRepository ──
    from .repository import BacktestRepository, get_backtest_repository

    _container.register_factory(BacktestRepository, get_backtest_repository)

    logger.info("DI Container initialized with %d registrations", len(_container._factories))
    return _container
