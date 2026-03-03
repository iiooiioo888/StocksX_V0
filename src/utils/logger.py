# 結構化日誌系統（JSON 格式）
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON 格式化的日誌輸出"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
        self._skip_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'message', 'taskName'
        }
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加異常資訊
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加自定義欄位
        if self.include_extra:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in self._skip_fields:
                    try:
                        json.dumps(value)  # 確保可序列化
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)
            
            if extra_fields:
                log_data['extra'] = extra_fields
        
        # 添加用戶/請求資訊（如果有）
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        
        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """控制台輸出格式（帶顏色）"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 綠色
        'WARNING': '\033[33m',   # 黃色
        'ERROR': '\033[31m',     # 紅色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        level_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = 'stocksx',
    level: int = logging.INFO,
    log_dir: str = 'logs',
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 7,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json_file: bool = True,
) -> logging.Logger:
    """
    設定日誌系統
    
    Args:
        name: 日誌名稱
        level: 日誌層級
        log_dir: 日誌目錄
        max_bytes: 單一檔案最大大小
        backup_count: 保留備份數量
        enable_console: 啟用控制台輸出
        enable_file: 啟用檔案輸出（文字格式）
        enable_json_file: 啟用 JSON 格式檔案
    
    Returns:
        設定好的 Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重複添加 handler
    if logger.handlers:
        return logger
    
    # 建立日誌目錄
    if log_dir and enable_file:
        os.makedirs(log_dir, exist_ok=True)
    
    # 控制台 Handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(ConsoleFormatter())
        logger.addHandler(console_handler)
    
    # 文字格式檔案 Handler（按時間輪轉）
    if enable_file and log_dir:
        text_log_path = os.path.join(log_dir, f'{name}.log')
        file_handler = TimedRotatingFileHandler(
            text_log_path,
            when='D',
            interval=1,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(file_handler)
    
    # JSON 格式檔案 Handler（按大小輪轉，便於日誌分析）
    if enable_json_file and log_dir:
        json_log_path = os.path.join(log_dir, f'{name}.json.log')
        json_handler = RotatingFileHandler(
            json_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)  # JSON 只記錄 INFO 以上
        json_handler.setFormatter(JSONFormatter(include_extra=True))
        logger.addHandler(json_handler)
    
    # 添加異常處理 Hook
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            return
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={'source': 'global_exception_handler'}
        )
    
    sys.excepthook = handle_exception
    
    return logger


def get_logger(name: str = 'stocksx') -> logging.Logger:
    """取得已設定的 Logger"""
    return logging.getLogger(name)


class LogContext:
    """日誌上下文管理器（用於添加追蹤資訊）"""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.context = kwargs
        self._old_factory = None
    
    def __enter__(self):
        self._add_context()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._remove_context()
        if exc_type:
            self.logger.error(
                f"Exception in context: {self.context}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
    
    def _add_context(self):
        """添加上下文資訊到 Logger"""
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        self._old_factory = old_factory
    
    def _remove_context(self):
        """移除上下文資訊"""
        if self._old_factory:
            logging.setLogRecordFactory(self._old_factory)


# 快捷函數
def log_api_call(
    logger: logging.Logger,
    api_name: str,
    endpoint: str,
    params: Optional[Dict] = None,
    response_time_ms: Optional[float] = None,
    status: str = 'success',
    **extra
):
    """記錄 API 呼叫日誌"""
    extra.update({
        'api_name': api_name,
        'endpoint': endpoint,
        'params': params,
        'response_time_ms': response_time_ms,
        'call_status': status
    })
    
    if status == 'success':
        logger.info(f"API call: {api_name}.{endpoint}", extra=extra)
    elif status == 'rate_limited':
        logger.warning(f"API rate limited: {api_name}.{endpoint}", extra=extra)
    else:
        logger.error(f"API call failed: {api_name}.{endpoint}", extra=extra)


def log_backtest(
    logger: logging.Logger,
    symbol: str,
    strategy: str,
    timeframe: str,
    metrics: Optional[Dict] = None,
    duration_ms: Optional[float] = None,
    user_id: Optional[int] = None,
    status: str = 'completed',
    **extra
):
    """記錄回測執行日誌"""
    extra.update({
        'symbol': symbol,
        'strategy': strategy,
        'timeframe': timeframe,
        'metrics': metrics,
        'duration_ms': duration_ms,
        'backtest_status': status
    })
    
    if user_id:
        extra['user_id'] = user_id
    
    if status == 'started':
        logger.info(f"Backtest started: {symbol} / {strategy}", extra=extra)
    elif status == 'completed':
        logger.info(f"Backtest completed: {symbol} / {strategy}", extra=extra)
    elif status == 'failed':
        logger.error(f"Backtest failed: {symbol} / {strategy}", extra=extra)
    elif status == 'queued':
        logger.info(f"Backtest queued: {symbol} / {strategy}", extra=extra)


def log_user_action(
    logger: logging.Logger,
    user_id: int,
    action: str,
    resource: str,
    details: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    **extra
):
    """記錄用戶操作日誌"""
    extra.update({
        'user_id': user_id,
        'action': action,
        'resource': resource,
        'details': details,
        'ip_address': ip_address
    })
    logger.info(f"User action: {action} on {resource}", extra=extra)


# 初始化預設 Logger
_default_logger: Optional[logging.Logger] = None


def init_default_logger(
    level: int = logging.INFO,
    log_dir: str = 'logs'
) -> logging.Logger:
    """初始化預設 Logger"""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger(
            name='stocksx',
            level=level,
            log_dir=log_dir,
            enable_console=True,
            enable_file=True,
            enable_json_file=True
        )
    return _default_logger
