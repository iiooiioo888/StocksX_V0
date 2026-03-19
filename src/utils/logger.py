"""
StocksX 統一日誌配置
取代散落各處的 print()，提供結構化日誌輸出。
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys


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
    # 從環境變數讀取，fallback 到參數，最後 fallback 到 INFO
    env_level = os.getenv("LOG_LEVEL", "")
    if env_level:
        level = env_level.upper()
    elif level is None:
        level = "INFO"

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return root_logger  # 已初始化過

    root_logger.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console Handler ──
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root_logger.addHandler(console)

    # ── File Handler（輪轉，保留 7 天）──
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{app_name}.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", backupCount=7, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root_logger.addHandler(file_handler)

    # 降低第三方庫的噪音
    for noisy in ("urllib3", "ccxt", "httpx", "httpcore", "plotly"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root_logger.info("📝 日誌系統初始化完成 — 級別=%s", level)
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """取得指定名稱的日誌器（快捷方式）。"""
    return logging.getLogger(name)
