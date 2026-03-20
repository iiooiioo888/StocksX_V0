"""
Utils — 工具模組

日誌、限流、健康檢查、裝飾器、風險分析、配置驗證、投資組合、報告匯出
"""

from .cache import LRUCache, TTLCache
from .health_check import (
    HealthStatus,
    SystemHealth,
    check_database,
    check_redis,
    check_disk_usage,
    check_memory,
    get_system_health,
)
from .rate_limiter import TokenBucket

try:
    from .logging_config import get_logger, setup_logging, JSONFormatter
except ImportError:
    pass

try:
    from .decorators import retry, timed, cached, rate_limit, suppress_errors
except ImportError:
    pass

try:
    from .risk import RiskAnalyzer, RiskMetrics, MonteCarloResult, compute_correlation
except ImportError:
    pass

try:
    from .config_validator import validate_config, ConfigReport, ConfigIssue
except ImportError:
    pass

try:
    from .portfolio import PortfolioAnalyzer, PortfolioWeights, PortfolioMetrics
except ImportError:
    pass

try:
    from .report import BacktestReportGenerator, StrategyComparisonGenerator
except ImportError:
    pass

__all__ = [
    "LRUCache",
    "TTLCache",
    "TokenBucket",
    "HealthStatus",
    "SystemHealth",
    "check_database",
    "check_redis",
    "check_disk_usage",
    "check_memory",
    "get_system_health",
    # Logging
    "get_logger",
    "setup_logging",
    "JSONFormatter",
    # Decorators
    "retry",
    "timed",
    "cached",
    "rate_limit",
    "suppress_errors",
    # Risk
    "RiskAnalyzer",
    "RiskMetrics",
    "MonteCarloResult",
    "compute_correlation",
    # Config validation
    "validate_config",
    "ConfigReport",
    "ConfigIssue",
    # Portfolio
    "PortfolioAnalyzer",
    "PortfolioWeights",
    "PortfolioMetrics",
    # Report
    "BacktestReportGenerator",
    "StrategyComparisonGenerator",
]
