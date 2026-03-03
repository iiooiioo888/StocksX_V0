# 日誌配置
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

from .config import settings


def setup_logger(name: str = "stocksx") -> logging.Logger:
    """設定日誌"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    if logger.handlers:
        return logger
    
    # 建立日誌目錄
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    # 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 檔案 Handler（按日輪轉）
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(settings.LOG_DIR, f"{name}.log"),
        when='D',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # JSON 格式 Handler（便於分析）
    json_handler = RotatingFileHandler(
        filename=os.path.join(settings.LOG_DIR, f"{name}.json.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=7,
        encoding='utf-8'
    )
    json_handler.setLevel(logging.INFO)
    logger.addHandler(json_handler)
    
    return logger


# 全域 logger
logger = setup_logger("stocksx")


def get_logger(name: str = "stocksx") -> logging.Logger:
    """取得 logger"""
    return logging.getLogger(name)
