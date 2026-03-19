"""
StocksX 統一日誌配置
取代散落各處的 print()，提供結構化日誌輸出。
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import time
from contextlib import contextmanager
from typing import Any


def setup_logging(
    level: str | int | None = None,
    log_dir: str = "logs",
    app_name: str = "stocksx",
) -> logging.Logger:
    """
    初始化應用日誌系統。

    Args:
        level: 日誌級別（環境變數 LOG_LEVEL 優先）
        log_dir: 日誌目錄
        app_name: 應用名稱（用於日誌檔名）

    Returns:
        根日誌器
    """
    env_level = os.getenv("LOG_LEVEL", "")
    if env_level:
        level = env_level.upper()
    elif level is None:
        level = "INFO"

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return root_logger

    root_logger.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root_logger.addHandler(console)

    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{app_name}.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file, when="midnight", backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root_logger.addHandler(file_handler)

    for noisy in ("urllib3", "ccxt", "httpx", "httpcore", "plotly"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root_logger.info("📝 日誌系統初始化完成 — 級別=%s", level)
    return root_logger


# ── Aliases ──
setup_logger = setup_logging
init_default_logger = setup_logging


def get_logger(name: str) -> logging.Logger:
    """取得指定名稱的日誌器（快捷方式）。"""
    return logging.getLogger(name)


# ── 結構化日誌輔助 ──


def log_api_call(
    logger: logging.Logger,
    provider: str,
    endpoint: str,
    status: int | str = "ok",
    duration_ms: float | None = None,
    **extra: Any,
) -> None:
    """記錄一次 API 呼叫。"""
    parts = [f"provider={provider}", f"endpoint={endpoint}", f"status={status}"]
    if duration_ms is not None:
        parts.append(f"duration={duration_ms:.1f}ms")
    for k, v in extra.items():
        parts.append(f"{k}={v}")
    logger.info("API call: %s", " | ".join(parts))


def log_backtest(
    logger: logging.Logger,
    symbol: str,
    strategy: str,
    status: str = "started",
    **extra: Any,
) -> None:
    """記錄回測事件。"""
    parts = [f"symbol={symbol}", f"strategy={strategy}", f"status={status}"]
    for k, v in extra.items():
        parts.append(f"{k}={v}")
    logger.info("Backtest: %s", " | ".join(parts))


def log_user_action(
    logger: logging.Logger,
    user_id: Any,
    action: str,
    **extra: Any,
) -> None:
    """記錄用戶操作。"""
    parts = [f"user={user_id}", f"action={action}"]
    for k, v in extra.items():
        parts.append(f"{k}={v}")
    logger.info("User action: %s", " | ".join(parts))


@contextmanager
def LogContext(logger: logging.Logger, operation: str, **extra: Any):
    """日誌上下文管理器 — 自動記錄操作的開始、結束與耗時。"""
    start = time.monotonic()
    parts = [f"op={operation}"]
    for k, v in extra.items():
        parts.append(f"{k}={v}")
    logger.info("▶ Start: %s", " | ".join(parts))
    try:
        yield
    except Exception:
        elapsed = (time.monotonic() - start) * 1000
        logger.exception("✖ Failed: %s (%.1fms)", operation, elapsed)
        raise
    else:
        elapsed = (time.monotonic() - start) * 1000
        logger.info("✔ Done: %s (%.1fms)", operation, elapsed)