"""
StocksX Core — 現代化架構核心

Provider → Pipeline → Signal → Backtest

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
from .backtest import BacktestEngine, BacktestConfig, BacktestReport
from .registry import StrategyRegistry, registry, register_strategy
from .adapters import CCXTProvider, YahooProvider, CompositeProvider
from .orchestrator import Orchestrator, get_orchestrator

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
    # Registry
    "StrategyRegistry",
    "registry",
    "register_strategy",
    # Orchestrator
    "Orchestrator",
    "get_orchestrator",
]
