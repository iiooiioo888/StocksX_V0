# API Routers - 回測相關
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core import security, logger
from ..models import BacktestHistory, get_db
from ..schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestResult,
    BacktestStatus,
    BacktestHistoryResponse,
    OptimizeRequest,
    OptimizeResponse,
)

router = APIRouter(prefix="/backtest", tags=["回測"])
security_scheme = HTTPBearer()
log = logger.get_logger("stocksx.api.backtest")


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> int:
    """取得當前用戶 ID"""
    token = credentials.credentials
    payload = security.verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效或已過期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return int(payload.get("sub", 0))


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> Any:
    """
    執行回測（非同步）
    
    返回 task_id，可使用 /backtest/status/{task_id} 查詢進度
    """
    import uuid
    from datetime import datetime
    
    task_id = str(uuid.uuid4())
    
    log.info(
        f"回測任務已提交：task_id={task_id}, user_id={user_id}, "
        f"symbol={request.symbol}, strategy={request.strategy}"
    )
    
    # 儲存回測請求到資料庫（待完成）
    # 這裡應該建立 Celery 任務並儲存 task_id
    
    # 模擬：實際實作應使用 Celery
    # from ..workers.tasks import run_backtest_task
    # task = run_backtest_task.delay(request.dict(), user_id)
    # task_id = task.id
    
    # 暫時儲存請求記錄
    backtest_record = BacktestHistory(
        user_id=user_id,
        symbol=request.symbol,
        exchange=request.exchange,
        timeframe=request.timeframe,
        strategy=request.strategy,
        params=str(request.params),
        metrics="{}",
        notes="",
        created_at=datetime.utcnow()
    )
    db.add(backtest_record)
    db.commit()
    
    return BacktestResponse(
        task_id=task_id,
        status="pending",
        message="回測任務已提交，處理中..."
    )


@router.get("/status/{task_id}", response_model=BacktestStatus)
async def get_backtest_status(
    task_id: str,
    user_id: int = Depends(get_current_user_id)
) -> Any:
    """
    查詢回測任務狀態
    """
    # 實際實作應從 Celery 查詢任務狀態
    # from celery.result import AsyncResult
    # task = AsyncResult(task_id, app=celery_app)
    # status = task.state
    
    # 模擬狀態
    return BacktestStatus(
        task_id=task_id,
        status="completed",  # pending, running, completed, failed
        progress=100,
        result=BacktestResult(
            task_id=task_id,
            status="completed",
            metrics={
                "total_return_pct": 15.5,
                "sharpe": 1.2,
                "max_drawdown_pct": -8.3,
                "win_rate": 0.55
            },
            trades=[
                {"date": "2024-01-01", "action": "BUY", "price": 42000, "pnl_pct": 5.2},
                {"date": "2024-01-15", "action": "SELL", "price": 44000, "pnl_pct": 4.8}
            ],
            equity_curve=[
                {"date": "2024-01-01", "equity": 10000},
                {"date": "2024-01-31", "equity": 11550}
            ],
            duration_ms=2345.67
        )
    )


@router.get("/result/{task_id}", response_model=BacktestResult)
async def get_backtest_result(
    task_id: str,
    user_id: int = Depends(get_current_user_id)
) -> Any:
    """
    取得回測結果
    """
    # 實際實作應從資料庫或快取取得結果
    
    return BacktestResult(
        task_id=task_id,
        status="completed",
        metrics={
            "total_return_pct": 15.5,
            "annual_return_pct": 62.0,
            "sharpe": 1.2,
            "sortino": 1.8,
            "calmar": 7.44,
            "max_drawdown_pct": -8.3,
            "win_rate": 0.55,
            "profit_factor": 1.85,
            "total_trades": 42,
            "avg_win": 520.5,
            "avg_loss": -280.3
        },
        trades=[
            {
                "date": "2024-01-01",
                "action": "BUY",
                "price": 42000,
                "amount": 10000,
                "pnl_pct": 5.2,
                "pnl_amount": 520
            },
            {
                "date": "2024-01-15",
                "action": "SELL",
                "price": 44000,
                "amount": 10520,
                "pnl_pct": 4.8,
                "pnl_amount": 504.96
            }
        ],
        equity_curve=[
            {"timestamp": 1704067200000, "equity": 10000},
            {"timestamp": 1704153600000, "equity": 10520},
            {"timestamp": 1705363200000, "equity": 11550}
        ],
        duration_ms=2345.67,
        config={
            "symbol": "BTC/USDT:USDT",
            "exchange": "binance",
            "timeframe": "1h",
            "strategy": "sma_cross",
            "params": {"fast_period": 5, "slow_period": 20}
        }
    )


@router.get("/history", response_model=BacktestHistoryResponse)
async def get_backtest_history(
    page: int = 1,
    page_size: int = 20,
    strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> Any:
    """
    取得回測歷史
    
    - **page**: 頁碼
    - **page_size**: 每頁數量
    - **strategy**: 篩選策略（可選）
    - **symbol**: 篩選交易對（可選）
    """
    query = db.query(BacktestHistory).filter(BacktestHistory.user_id == user_id)
    
    if strategy:
        query = query.filter(BacktestHistory.strategy == strategy)
    if symbol:
        query = query.filter(BacktestHistory.symbol == symbol)
    
    total = query.count()
    items = query.order_by(
        BacktestHistory.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return BacktestHistoryResponse(
        items=[
            {
                "id": item.id,
                "symbol": item.symbol,
                "exchange": item.exchange,
                "timeframe": item.timeframe,
                "strategy": item.strategy,
                "params": eval(item.params) if item.params else {},
                "metrics": eval(item.metrics) if item.metrics else {},
                "created_at": item.created_at.timestamp(),
                "notes": item.notes,
                "is_favorite": item.is_favorite
            }
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/history/{record_id}")
async def delete_backtest_history(
    record_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> Any:
    """
    刪除回測記錄
    """
    record = db.query(BacktestHistory).filter(
        BacktestHistory.id == record_id,
        BacktestHistory.user_id == user_id
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回測記錄不存在"
        )
    
    db.delete(record)
    db.commit()
    
    return {"message": "已刪除"}


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_params(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id)
) -> Any:
    """
    參數優化（非同步）
    
    使用網格搜索尋找最佳參數組合
    """
    import uuid
    
    task_id = str(uuid.uuid4())
    
    log.info(
        f"參數優化任務已提交：task_id={task_id}, user_id={user_id}, "
        f"strategy={request.strategy}, param_grid={request.param_grid}"
    )
    
    # 實際實作應使用 Celery
    # from ..workers.tasks import optimize_params_task
    # task = optimize_params_task.delay(request.dict(), user_id)
    
    return OptimizeResponse(
        task_id=task_id,
        status="pending",
        message="參數優化任務已提交，處理中..."
    )
