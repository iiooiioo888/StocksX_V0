# FastAPI 應用配置
from __future__ import annotations

import os
from typing import List, Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """應用配置"""
    
    # 應用配置
    APP_NAME: str = "StocksX API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api"
    
    # 伺服器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 資料庫配置
    DATABASE_URL: str = "sqlite:///./stocksx.db"
    # PostgreSQL: postgresql://user:password@localhost:5432/stocksx
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS 配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_CAPACITY: int = 10
    RATE_LIMIT_DEFAULT_REFILL_RATE: float = 1.0
    
    # 日誌配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
    # 外部 API 金鑰
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    FRED_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全域配置實例
settings = Settings()
