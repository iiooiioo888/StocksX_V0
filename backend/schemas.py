#!/usr/bin/env python3
"""
StocksX Pydantic Schemas
API 請求/響應模型

作者：StocksX Team
創建日期：2026-03-22
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ============ 策略相關 ============


class StrategyBase(BaseModel):
    """策略基礎模式"""

    name: str
    category: str
    description: Optional[str] = None
    params: Optional[dict[str, Any]] = None


class StrategyCreate(StrategyBase):
    """創建策略"""

    pass


class StrategyUpdate(BaseModel):
    """更新策略"""

    description: Optional[str] = None
    params: Optional[dict[str, Any]] = None


class StrategyResponse(StrategyBase):
    """策略響應"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 信號相關 ============


class SignalBase(BaseModel):
    """信號基礎模式"""

    strategy_id: int
    signal_type: str = Field(..., pattern="^(BUY|SELL|HOLD)$")
    price: float
    metadata: Optional[dict[str, Any]] = None


class SignalCreate(SignalBase):
    """創建信號"""

    pass


class SignalResponse(BaseModel):
    """信號響應"""

    id: int
    strategy_id: int
    signal_type: str
    price: float
    timestamp: datetime
    metadata: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class SignalBatchResponse(BaseModel):
    """批量信號響應"""

    signals: list[SignalResponse]
    count: int
    timestamp: datetime


# ============ 評分相關 ============


class ScoreBase(BaseModel):
    """評分基礎模式"""

    strategy_id: int
    score: float = Field(..., ge=0, le=100)
    grade: str
    sharpe_ratio: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None


class ScoreCreate(ScoreBase):
    """創建評分"""

    pass


class ScoreResponse(ScoreBase):
    """評分響應"""

    id: int
    evaluated_at: datetime
    strategy_name: Optional[str] = None

    class Config:
        from_attributes = True


class ScoreRanking(BaseModel):
    """評分排名"""

    rank: int
    strategy_id: int
    strategy_name: str
    score: float
    grade: str
    sharpe_ratio: Optional[float] = None


# ============ 組合相關 ============


class PortfolioBase(BaseModel):
    """組合基礎模式"""

    name: str
    initial_capital: float = 1000000.0
    weights: Optional[dict[str, float]] = None


class PortfolioCreate(PortfolioBase):
    """創建組合"""

    pass


class PortfolioUpdate(BaseModel):
    """更新組合"""

    weights: Optional[dict[str, float]] = None
    current_value: Optional[float] = None


class PortfolioResponse(PortfolioBase):
    """組合響應"""

    id: int
    current_value: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioBacktestRequest(BaseModel):
    """組合回測請求"""

    strategies: list[str]
    weights: Optional[dict[str, float]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = 1000000.0


class PortfolioBacktestResponse(BaseModel):
    """組合回測響應"""

    portfolio_id: int
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    final_value: float
    strategy_results: list[dict[str, Any]]


# ============ 回測結果相關 ============


class BacktestResultBase(BaseModel):
    """回測結果基礎模式"""

    strategy_id: Optional[int] = None
    portfolio_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_value: float
    total_return: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_trades: Optional[int] = None
    win_rate: Optional[float] = None


class BacktestResultResponse(BacktestResultBase):
    """回測結果響應"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 通用響應 ============


class HealthResponse(BaseModel):
    """健康檢查響應"""

    status: str
    timestamp: datetime
    version: str
    strategies: int


class ErrorResponse(BaseModel):
    """錯誤響應"""

    error: str
    detail: Optional[str] = None
    code: Optional[int] = None


class MessageResponse(BaseModel):
    """消息響應"""

    message: str
    success: bool = True
