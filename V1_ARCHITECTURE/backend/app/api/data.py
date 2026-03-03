# API Routers - 數據相關
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core import security, logger
from ..schemas.data import (
    KlineRequest,
    KlineResponse,
    SymbolInfo,
    SymbolListResponse,
    FearGreedResponse,
    StrategyInfo,
    StrategyListResponse,
)

router = APIRouter(prefix="/data", tags=["數據"])
security_scheme = HTTPBearer()
log = logger.get_logger("stocksx.api.data")


# 模擬數據（實際應從資料庫或外部 API 取得）
CRYPTO_SYMBOLS = [
    {"symbol": "BTC/USDT", "name": "Bitcoin", "category": "主流現貨"},
    {"symbol": "ETH/USDT", "name": "Ethereum", "category": "主流現貨"},
    {"symbol": "BTC/USDT:USDT", "name": "Bitcoin 永續", "category": "主流永續"},
    {"symbol": "ETH/USDT:USDT", "name": "Ethereum 永續", "category": "主流永續"},
    {"symbol": "SOL/USDT", "name": "Solana", "category": "主流現貨"},
    {"symbol": "BNB/USDT", "name": "BNB", "category": "主流現貨"},
]

TRADITIONAL_SYMBOLS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "category": "美股"},
    {"symbol": "MSFT", "name": "Microsoft", "category": "美股"},
    {"symbol": "GOOGL", "name": "Alphabet", "category": "美股"},
    {"symbol": "NVDA", "name": "NVIDIA", "category": "美股"},
    {"symbol": "TSLA", "name": "Tesla", "category": "美股"},
    {"symbol": "^GSPC", "name": "S&P 500", "category": "指數"},
]

STRATEGIES = [
    {
        "name": "sma_cross",
        "label": "雙均線交叉",
        "description": "當快線向上穿越慢線時買入，向下穿越時賣出",
        "params": {
            "fast_period": {"type": "int", "default": 5, "min": 2, "max": 50},
            "slow_period": {"type": "int", "default": 20, "min": 10, "max": 200}
        },
        "category": "趨勢"
    },
    {
        "name": "rsi_signal",
        "label": "RSI 指標",
        "description": "RSI 低於超賣區間買入，高於超買區間賣出",
        "params": {
            "period": {"type": "int", "default": 14, "min": 5, "max": 30},
            "oversold": {"type": "float", "default": 30, "min": 10, "max": 40},
            "overbought": {"type": "float", "default": 70, "min": 60, "max": 90}
        },
        "category": "擺盪"
    },
    {
        "name": "macd_cross",
        "label": "MACD 交叉",
        "description": "MACD 線向上穿越信號線時買入，向下穿越時賣出",
        "params": {
            "fast_period": {"type": "int", "default": 12, "min": 5, "max": 20},
            "slow_period": {"type": "int", "default": 26, "min": 20, "max": 50},
            "signal_period": {"type": "int", "default": 9, "min": 5, "max": 15}
        },
        "category": "趨勢"
    },
    {
        "name": "bollinger_signal",
        "label": "布林帶",
        "description": "價格觸及下軌時買入，觸及上軌時賣出",
        "params": {
            "period": {"type": "int", "default": 20, "min": 10, "max": 50},
            "std_dev": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0}
        },
        "category": "擺盪"
    },
    {
        "name": "supertrend",
        "label": "超級趨勢",
        "description": "基於 ATR 的趨勢跟隨策略",
        "params": {
            "period": {"type": "int", "default": 10, "min": 5, "max": 20},
            "multiplier": {"type": "float", "default": 3.0, "min": 1.0, "max": 5.0}
        },
        "category": "趨勢"
    },
]


@router.get("/symbols", response_model=SymbolListResponse)
async def get_symbols(
    market_type: str = Query("crypto", description="市場類型：crypto 或 traditional"),
    category: Optional[str] = Query(None, description="分類"),
    exchange: Optional[str] = Query("binance", description="交易所")
) -> Any:
    """
    取得交易對列表
    
    - **market_type**: 市場類型（crypto / traditional）
    - **category**: 分類篩選（可選）
    - **exchange**: 交易所（可選）
    """
    symbols = CRYPTO_SYMBOLS if market_type == "crypto" else TRADITIONAL_SYMBOLS
    
    if category:
        symbols = [s for s in symbols if s.get("category") == category]
    
    return SymbolListResponse(
        symbols=[
            SymbolInfo(
                symbol=s["symbol"],
                name=s["name"],
                market_type=market_type,
                category=s.get("category"),
                exchange=exchange or "binance"
            )
            for s in symbols
        ],
        total=len(symbols)
    )


@router.get("/symbols/categories")
async def get_categories(
    market_type: str = Query("crypto", description="市場類型")
) -> Any:
    """
    取得分類列表
    """
    symbols = CRYPTO_SYMBOLS if market_type == "crypto" else TRADITIONAL_SYMBOLS
    categories = list(set(s.get("category") for s in symbols if s.get("category")))
    return {"categories": categories}


@router.get("/kline", response_model=KlineResponse)
async def get_kline(
    symbol: str = Query(..., description="交易對"),
    exchange: str = Query("binance", description="交易所"),
    timeframe: str = Query("1h", description="時間框架"),
    start_date: str = Query(..., description="開始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="結束日期 YYYY-MM-DD"),
    limit: Optional[int] = Query(None, description="最大返回筆數")
) -> Any:
    """
    取得 K 線數據
    
    實際實作應呼叫外部 API（CCXT / yfinance）
    """
    from datetime import datetime
    import random
    
    # 解析日期
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # 模擬 K 線數據（實際應從 API 取得）
    data = []
    current = start
    base_price = random.uniform(40000, 50000) if "BTC" in symbol else random.uniform(100, 500)
    
    while current <= end:
        change = random.uniform(-0.05, 0.05)
        open_price = base_price
        close_price = base_price * (1 + change)
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, close_price) * random.uniform(0.98, 1.0)
        volume = random.uniform(100, 10000)
        
        data.append({
            "timestamp": int(current.timestamp() * 1000),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": round(volume, 2)
        })
        
        base_price = close_price
        current = datetime(current.year, current.month, current.day)
        # 簡單起見，每天增加
        from datetime import timedelta
        current += timedelta(days=1)
        
        if limit and len(data) >= limit:
            break
    
    return KlineResponse(
        symbol=symbol,
        exchange=exchange,
        timeframe=timeframe,
        data=data,
        count=len(data)
    )


@router.get("/fear-greed", response_model=FearGreedResponse)
async def get_fear_greed() -> Any:
    """
    取得恐懼貪婪指數
    
    實際實作應呼叫 Alternative.me API
    """
    import random
    
    value = random.randint(20, 80)
    
    if value < 25:
        classification = "Extreme Fear"
    elif value < 45:
        classification = "Fear"
    elif value < 55:
        classification = "Neutral"
    elif value < 75:
        classification = "Greed"
    else:
        classification = "Extreme Greed"
    
    from datetime import datetime
    return FearGreedResponse(
        value=value,
       classification=classification,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/strategies", response_model=StrategyListResponse)
async def get_strategies(
    category: Optional[str] = Query(None, description="策略分類")
) -> Any:
    """
    取得可用策略列表
    
    - **category**: 策略分類篩選（可選）
    """
    strategies = STRATEGIES
    
    if category:
        strategies = [s for s in strategies if s.get("category") == category]
    
    return StrategyListResponse(
        strategies=[
            StrategyInfo(
                name=s["name"],
                label=s["label"],
                description=s["description"],
                params=s["params"],
                category=s["category"]
            )
            for s in strategies
        ],
        total=len(strategies)
    )


@router.get("/strategies/{strategy_name}")
async def get_strategy_info(
    strategy_name: str
) -> Any:
    """
    取得單一策略詳細資訊
    """
    strategy = next((s for s in STRATEGIES if s["name"] == strategy_name), None)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略 {strategy_name} 不存在"
        )
    
    return strategy
