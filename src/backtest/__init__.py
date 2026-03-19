# 回測引擎
from .engine import BacktestResult, _compute_metrics, run_backtest
from .optimizer import find_optimal, find_optimal_global
from . import strategies

# Alias: public API uses compute_metrics (no underscore)
compute_metrics = _compute_metrics

__all__ = [
    "BacktestResult",
    "compute_metrics",
    "find_optimal",
    "find_optimal_global",
    "run_backtest",
    "strategies",
]
