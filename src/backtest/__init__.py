# 回測引擎
from .engine import BacktestResult, _compute_metrics, run_backtest
from .optimizer import find_optimal, find_optimal_global
from .np_utils import OHLCVArrays, sma, ema, rolling_max, rolling_min, rolling_std, true_range, atr
from . import strategies

# Alias: public API uses compute_metrics (no underscore)
compute_metrics = _compute_metrics

__all__ = [
    "BacktestResult",
    "OHLCVArrays",
    "compute_metrics",
    "find_optimal",
    "find_optimal_global",
    "run_backtest",
    "strategies",
    # np_utils 高性能原語
    "sma",
    "ema",
    "rolling_max",
    "rolling_min",
    "rolling_std",
    "true_range",
    "atr",
]
