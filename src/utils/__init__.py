"""
Utils — 工具模組

日誌、限流、健康檢查、結構化日誌
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
]
