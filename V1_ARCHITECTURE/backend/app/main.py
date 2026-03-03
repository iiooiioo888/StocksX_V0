# FastAPI 主應用程式
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core import settings, logger, init_db
from .api import auth_router, backtest_router, data_router, monitor_router


log = logger.get_logger("stocksx.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """應用程式生命週期管理"""
    # 啟動時
    log.info("StocksX API 啟動中...")
    
    # 初始化資料庫
    init_db()
    log.info("資料庫初始化完成")
    
    yield
    
    # 關閉時
    log.info("StocksX API 關閉中...")


# 建立 FastAPI 應用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="StocksX 通用回測平台 API - 支援加密貨幣和傳統市場",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康檢查端點
@app.get("/health", tags=["健康檢查"])
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


# 註冊 API routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(backtest_router, prefix=settings.API_PREFIX)
app.include_router(data_router, prefix=settings.API_PREFIX)
app.include_router(monitor_router, prefix=settings.API_PREFIX)


# 根端點
@app.get("/", tags=["根"])
async def root():
    """根端點"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
