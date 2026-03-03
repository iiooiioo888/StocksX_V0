# Celery 應用配置
from __future__ import annotations

import os
from celery import Celery
from celery.schedules import crontab

# Redis 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery 配置
app = Celery(
    'stocksx',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.tasks.backtest_tasks']
)

# Celery 優化配置
app.conf.update(
    # 任務序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 時區
    timezone='Asia/Taipei',
    enable_utc=True,
    
    # 任務結果過期時間（秒）
    result_expires=3600,
    
    # 任務確認
    task_acks_late=True,
    task_reject_on_worker_or_miss=True,
    
    # 預取限制（防止單一 worker 佔用過多任務）
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # 重試配置
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # 任務時間限制
    task_time_limit=300,  # 5 分鐘
    task_soft_time_limit=240,  # 4 分鐘
    
    # Redis 特定配置
    broker_transport_options={
        'visibility_timeout': 3600,  # 1 小時
        'confirm_publish': True,
    },
    
    # 任務路由
    task_routes={
        'src.tasks.backtest_tasks.run_backtest': {'queue': 'backtest'},
        'src.tasks.backtest_tasks.run_param_optimizer': {'queue': 'optimizer'},
        'src.tasks.backtest_tasks.run_walk_forward_analysis': {'queue': 'backtest'},
    },
    
    # 定時任務
    beat_schedule={
        'cleanup-old-results': {
            'task': 'src.tasks.cleanup.cleanup_old_results',
            'schedule': crontab(hour=3, minute=0),  # 每天凌晨 3 點
        },
        'refresh-cache': {
            'task': 'src.tasks.cache_tasks.refresh_market_cache',
            'schedule': crontab(minute='*/15'),  # 每 15 分鐘
        },
    },
)


# 任務信號處理器
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    task_success,
    worker_process_init,
)

import logging
import time

logger = logging.getLogger('stocksx.celery')


@task_prerun.connect
def on_task_prerun(task_id, task, *args, **kwargs):
    """任務開始前記錄"""
    task.start_time = time.time()
    logger.info(
        f"Task started: {task.name}[{task_id}]",
        extra={
            'task_id': task_id,
            'task_name': task.name,
        }
    )


@task_postrun.connect
def on_task_postrun(task_id, task, *args, **kwargs, retval=None):
    """任務完成後記錄"""
    duration = time.time() - getattr(task, 'start_time', time.time())
    logger.info(
        f"Task completed: {task.name}[{task_id}] in {duration:.2f}s",
        extra={
            'task_id': task_id,
            'task_name': task.name,
            'duration': duration,
            'retval': str(retval)[:100] if retval else None,
        }
    )


@task_failure.connect
def on_task_failure(task_id, task, *args, exception=None, **kwargs):
    """任務失敗記錄"""
    logger.error(
        f"Task failed: {task.name}[{task_id}]",
        extra={
            'task_id': task_id,
            'task_name': task.name,
            'exception': str(exception),
        },
        exc_info=True
    )


@worker_process_init.connect
def on_worker_init(*args, **kwargs):
    """Worker 啟動時初始化"""
    from src.utils.logger import setup_logger
    setup_logger(
        name='stocksx.celery',
        level=logging.INFO,
        log_dir=os.getenv('LOG_DIR', 'logs')
    )
    logger.info("Worker process initialized")
