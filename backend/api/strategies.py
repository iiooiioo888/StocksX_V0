#!/usr/bin/env python3
"""
StocksX 策略 API 路由

作者：StocksX Team
創建日期：2026-03-22
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import get_db
from models import Strategy, Signal
from schemas import StrategyResponse, StrategyCreate, StrategyUpdate, SignalResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=list[StrategyResponse])
def get_all_strategies(
    category: Optional[str] = Query(None, description="策略類別篩選"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """獲取所有策略"""
    query = db.query(Strategy)

    if category:
        query = query.filter(Strategy.category == category)

    strategies = query.offset(skip).limit(limit).all()
    return strategies


@router.get("/{name}", response_model=StrategyResponse)
def get_strategy(name: str, db: Session = Depends(get_db)):
    """獲取策略詳情"""
    strategy = db.query(Strategy).filter(Strategy.name == name).first()

    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    return strategy


@router.post("", response_model=StrategyResponse)
def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    """創建新策略"""
    # 檢查是否已存在
    existing = db.query(Strategy).filter(Strategy.name == strategy.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="策略名稱已存在")

    db_strategy = Strategy(**strategy.dict())
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)

    return db_strategy


@router.put("/{name}", response_model=StrategyResponse)
def update_strategy(name: str, strategy_update: StrategyUpdate, db: Session = Depends(get_db)):
    """更新策略"""
    db_strategy = db.query(Strategy).filter(Strategy.name == name).first()

    if not db_strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    update_data = strategy_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_strategy, key, value)

    db_strategy.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_strategy)

    return db_strategy


@router.delete("/{name}", response_model=MessageResponse)
def delete_strategy(name: str, db: Session = Depends(get_db)):
    """刪除策略"""
    db_strategy = db.query(Strategy).filter(Strategy.name == name).first()

    if not db_strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    db.delete(db_strategy)
    db.commit()

    return MessageResponse(message=f"策略 {name} 已刪除", success=True)


@router.get("/{name}/signals", response_model=list[SignalResponse])
def get_strategy_signals(name: str, limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    """獲取策略歷史信號"""
    strategy = db.query(Strategy).filter(Strategy.name == name).first()

    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    signals = (
        db.query(Signal).filter(Signal.strategy_id == strategy.id).order_by(Signal.timestamp.desc()).limit(limit).all()
    )

    return signals


@router.post("/{name}/signals", response_model=SignalResponse)
def create_signal(name: str, signal: SignalResponse, db: Session = Depends(get_db)):
    """創建新信號"""
    strategy = db.query(Strategy).filter(Strategy.name == name).first()

    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    db_signal = Signal(
        strategy_id=strategy.id, signal_type=signal.signal_type, price=signal.price, metadata=signal.metadata
    )

    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)

    return db_signal
