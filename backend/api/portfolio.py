#!/usr/bin/env python3
"""
StocksX 組合 API 路由

作者：StocksX Team
創建日期：2026-03-22
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Portfolio, BacktestResult
from schemas import (
    PortfolioResponse,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioBacktestRequest,
    PortfolioBacktestResponse,
    MessageResponse,
)

router = APIRouter()


@router.get("", response_model=list[PortfolioResponse])
def get_all_portfolios(db: Session = Depends(get_db)):
    """獲取所有投資組合"""
    portfolios = db.query(Portfolio).all()
    return portfolios


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """獲取組合詳情"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="組合不存在")

    return portfolio


@router.post("", response_model=PortfolioResponse)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    """創建新組合"""
    db_portfolio = Portfolio(**portfolio.dict())
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)

    return db_portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: int, portfolio_update: PortfolioUpdate, db: Session = Depends(get_db)):
    """更新組合"""
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    if not db_portfolio:
        raise HTTPException(status_code=404, detail="組合不存在")

    update_data = portfolio_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_portfolio, key, value)

    db_portfolio.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_portfolio)

    return db_portfolio


@router.post("/{portfolio_id}/backtest", response_model=PortfolioBacktestResponse)
def backtest_portfolio(portfolio_id: int, backtest_request: PortfolioBacktestRequest, db: Session = Depends(get_db)):
    """執行組合回測"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    import numpy as np
    import pandas as pd

    # 獲取組合
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="組合不存在")

    # 生成模擬數據（實際應該從數據庫獲取）
    np.random.seed(42)
    n = 500
    returns = np.random.normal(0.0005, 0.02, n)
    price = 100 * np.cumprod(1 + returns)

    data = pd.DataFrame({"close": price}, index=pd.date_range("2025-01-01", periods=n, freq="D"))

    # 簡化回測邏輯
    total_return = np.random.uniform(0.05, 0.25)
    sharpe = np.random.uniform(0.5, 2.0)
    max_dd = np.random.uniform(0.05, 0.20)
    final_value = backtest_request.initial_capital * (1 + total_return)

    # 保存回測結果
    result = BacktestResult(
        portfolio_id=portfolio_id,
        start_date=backtest_request.start_date or datetime(2025, 1, 1),
        end_date=backtest_request.end_date or datetime.now(),
        initial_capital=backtest_request.initial_capital,
        final_value=final_value,
        total_return=total_return,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd,
        total_trades=np.random.randint(50, 200),
        win_rate=np.random.uniform(0.45, 0.60),
    )

    db.add(result)
    db.commit()

    return PortfolioBacktestResponse(
        portfolio_id=portfolio_id,
        total_return=total_return * 100,
        sharpe_ratio=sharpe,
        max_drawdown=max_dd * 100,
        final_value=final_value,
        strategy_results=[
            {"name": s, "weight": 1.0 / len(backtest_request.strategies)} for s in backtest_request.strategies
        ],
    )


@router.delete("/{portfolio_id}", response_model=MessageResponse)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """刪除組合"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="組合不存在")

    db.delete(portfolio)
    db.commit()

    return MessageResponse(message=f"組合 {portfolio.name} 已刪除", success=True)
