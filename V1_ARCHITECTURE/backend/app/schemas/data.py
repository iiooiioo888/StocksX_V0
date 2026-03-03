# Pydantic Schemas - 數據相關
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KlineRequest(BaseModel):
    """K 線數據請求"""
    symbol: str = Field(..., description="交易對")
    exchange: str = Field("binance", description="交易所")
    timeframe: str = Field("1h", description="時間框架")
    start_date: str = Field(..., description="開始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="結束日期 YYYY-MM-DD")
    limit: Optional[int] = Field(None, description="最大返回筆數")


class KlineResponse(BaseModel):
    """K 線數據響應"""
    symbol: str
    exchange: str
    timeframe: str
    data: List[Dict[str, Any]]
    count: int


class OHLCV(BaseModel):
    """OHLCV 數據點"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class SymbolInfo(BaseModel):
    """交易對資訊"""
    symbol: str
    exchange: str
    name: Optional[str] = None
    market_type: str = "crypto"
    category: Optional[str] = None
    is_active: bool = True


class SymbolListResponse(BaseModel):
    """交易對列表響應"""
    symbols: List[SymbolInfo]
    total: int


class MarketDataRequest(BaseModel):
    """市場數據請求"""
    symbols: List[str] = Field(..., description="交易對列表")
    fields: List[str] = Field(
        ["price", "change", "volume"],
        description="需要的欄位"
    )


class MarketDataResponse(BaseModel):
    """市場數據響應"""
    data: Dict[str, Dict[str, Any]]
    timestamp: float


class FearGreedResponse(BaseModel):
    """恐懼貪婪指數響應"""
    value: int
    classification: str
    timestamp: str


class StrategyInfo(BaseModel):
    """策略資訊"""
    name: str
    label: str
    description: str
    params: Dict[str, Any]
    category: str


class StrategyListResponse(BaseModel):
    """策略列表響應"""
    strategies: List[StrategyInfo]
    total: int
