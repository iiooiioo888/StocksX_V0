# Pydantic Schemas - 回測相關
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    """回測請求"""
    symbol: str = Field(..., description="交易對（如 BTC/USDT:USDT 或 AAPL）")
    exchange: str = Field("binance", description="交易所")
    timeframe: str = Field("1h", description="時間框架")
    strategy: str = Field(..., description="策略名稱")
    params: Dict[str, Any] = Field(default_factory=dict, description="策略參數")
    start_date: str = Field(..., description="開始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="結束日期 YYYY-MM-DD")
    initial_equity: float = Field(10000.0, description="初始資金")
    leverage: float = Field(1.0, description="槓桿")
    fee_rate: float = Field(0.001, description="手續費率")


class BacktestResponse(BaseModel):
    """回測響應"""
    task_id: str
    status: str = "pending"
    message: str = "回測任務已提交"


class BacktestResult(BaseModel):
    """回測結果"""
    task_id: str
    status: str  # pending, completed, failed
    metrics: Optional[Dict[str, Any]] = None
    trades: Optional[List[Dict[str, Any]]] = None
    equity_curve: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    config: Optional[Dict[str, Any]] = None


class BacktestStatus(BaseModel):
    """回測狀態"""
    task_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[BacktestResult] = None


class BacktestHistoryItem(BaseModel):
    """回測歷史項目"""
    id: int
    symbol: str
    exchange: str
    timeframe: str
    strategy: str
    params: Dict[str, Any]
    metrics: Dict[str, Any]
    created_at: float
    notes: Optional[str] = None
    is_favorite: bool = False


class BacktestHistoryResponse(BaseModel):
    """回測歷史響應"""
    items: List[BacktestHistoryItem]
    total: int
    page: int
    page_size: int


class OptimizeRequest(BaseModel):
    """參數優化請求"""
    symbol: str
    exchange: str
    timeframe: str
    strategy: str
    param_grid: Dict[str, List[Any]] = Field(
        ...,
        description="參數網格，如 {'fast_period': [5, 10, 20]}"
    )
    start_date: str
    end_date: str
    initial_equity: float = 10000.0
    leverage: float = 1.0
    fee_rate: float = 0.001
    metric: str = Field("total_return_pct", description="優化指標")
    n_best: int = Field(10, description="回傳前 N 個最佳結果")


class OptimizeResponse(BaseModel):
    """參數優化響應"""
    task_id: str
    status: str = "pending"
    message: str = "優化任務已提交"


class OptimizeResult(BaseModel):
    """參數優化結果"""
    task_id: str
    status: str
    results: Optional[List[Dict[str, Any]]] = None
    best_params: Optional[Dict[str, Any]] = None
    total_runs: Optional[int] = None
    duration_ms: Optional[float] = None
