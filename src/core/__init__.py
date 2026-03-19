"""
StocksX Core — 現代化架構核心

Provider → Pipeline → Signal → Backtest
+ Middleware + CacheManager + Repository + TaskQueue + Alerts + DI Container
+ WalkForwardAnalyzer

所有組件通過 Protocol 定義介面，支持依賴注入與替換。
"""

from .config import Settings, get_settings
from .provider import (
    MarketProvider,
    OHLCV,
    Ticker,
    OrderBook,
    CacheBackend,
)
from .signals import Signal, SignalBus, Direction
from .pipeline import Pipeline, PipelineStep
from .backtest import BacktestEngine, BacktestConfig, BacktestReport, TradeRecord
from .registry import StrategyRegistry, registry, register_strategy
from .adapters import CCXTProvider, YahooProvider, CompositeProvider
from .orchestrator import Orchestrator, get_orchestrator
from .middleware import (
    Middleware,
    MiddlewarePipeline,
    LoggingMiddleware,
    RetryMiddleware,
    RateLimitMiddleware,
    TimingMiddleware,
    with_middleware,
)
from .cache_manager import CacheManager, CacheNamespace, CacheStats, get_cache_manager
from .repository import (
    BacktestRepository,
    BacktestRecord,
    SqliteBacktestRepository,
    get_backtest_repository,
)
from .tasks import ThreadTaskQueue, TaskInfo, TaskStatus, get_task_queue
from .alerts import (
    AlertManager,
    AlertRule,
    Alert,
    AlertSeverity,
    LogChannel,
    BarkChannel,
    WebhookChannel,
    get_alert_manager,
)
from .container import Container, get_container

# Walk-Forward Analysis
try:
    from .walk_forward import WalkForwardAnalyzer, WFResult, WFSplit
except ImportError:
    pass

# 確保策略橋接被加載（註冊舊策略到新 Registry）
try:
    from . import strategies_bridge  # noqa: F401
except Exception:
    pass

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Provider
    "MarketProvider",
    "OHLCV",
    "Ticker",
    "OrderBook",
    "CacheBackend",
    "CCXTProvider",
    "YahooProvider",
    "CompositeProvider",
    # Signals
    "Signal",
    "SignalBus",
    "Direction",
    # Pipeline
    "Pipeline",
    "PipelineStep",
    # Backtest
    "BacktestEngine",
    "BacktestConfig",
    "BacktestReport",
    "TradeRecord",
    # Registry
    "StrategyRegistry",
    "registry",
    "register_strategy",
    # Orchestrator
    "Orchestrator",
    "get_orchestrator",
    # Middleware
    "Middleware",
    "MiddlewarePipeline",
    "LoggingMiddleware",
    "RetryMiddleware",
    "RateLimitMiddleware",
    "TimingMiddleware",
    "with_middleware",
    # Cache
    "CacheManager",
    "CacheNamespace",
    "CacheStats",
    "get_cache_manager",
    # Repository
    "BacktestRepository",
    "BacktestRecord",
    "SqliteBacktestRepository",
    "get_backtest_repository",
    # Tasks
    "ThreadTaskQueue",
    "TaskInfo",
    "TaskStatus",
    "get_task_queue",
    # Alerts
    "AlertManager",
    "AlertRule",
    "Alert",
    "AlertSeverity",
    "LogChannel",
    "BarkChannel",
    "WebhookChannel",
    "get_alert_manager",
    # DI Container
    "Container",
    "get_container",
    # Walk-Forward
    "WalkForwardAnalyzer",
    "WFResult",
    "WFSplit",
]
