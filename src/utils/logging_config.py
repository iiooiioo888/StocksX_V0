"""
結構化日誌配置 — JSON 輸出、等級控制、檔案輪替

用法：
    from src.utils.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("操作完成", extra={"symbol": "BTC/USDT", "duration_ms": 123})
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON 格式化器 — 輸出結構化日誌，方便 ELK/Loki 解析."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 附加 extra 欄位
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "message", "timestamp",
            ):
                log_entry[key] = value

        # 異常資訊
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """彩色控制台輸出 — 開發環境使用."""

    COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "INFO": "\033[32m",      # green
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[35m",  # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = f"{color}{ts} {record.levelname:8s}{self.RESET}"
        msg = f"{prefix} [{record.name}] {record.getMessage()}"
        if record.exc_info and record.exc_info[0] is not None:
            msg += f"\n{self.COLORS['ERROR']}{self.formatException(record.exc_info)}{self.RESET}"
        return msg


def setup_logging(
    level: str | None = None,
    log_file: str | None = None,
    json_mode: bool | None = None,
) -> None:
    """
    初始化全域日誌配置.

    Args:
        level: 日誌等級（DEBUG/INFO/WARNING/ERROR），預設從 LOG_LEVEL 環境變數讀取
        log_file: 日誌檔案路徑，預設 logs/app.log
        json_mode: 是否使用 JSON 格式，預設從 APP_ENV 判斷（production=True）
    """
    level = level or os.getenv("LOG_LEVEL", "INFO")
    log_file = log_file or os.getenv("LOG_FILE", "logs/app.log")

    if json_mode is None:
        json_mode = os.getenv("APP_ENV", "production") == "production"

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 清除既有 handlers
    root_logger.handlers.clear()

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_mode:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())
    root_logger.addHandler(console_handler)

    # 檔案 handler（輪替，最大 10MB，保留 5 個）
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    except OSError:
        pass  # 檔案不可寫時忽略

    # 降低 noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("ccxt").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """取得命名 logger."""
    return logging.getLogger(name)
