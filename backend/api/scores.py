#!/usr/bin/env python3
"""
StocksX 評分 API 路由

作者：StocksX Team
創建日期：2026-03-22
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Score, Strategy
from schemas import ScoreResponse, ScoreRanking, MessageResponse

router = APIRouter()


@router.get("", response_model=List[ScoreResponse])
def get_all_scores(
    grade: Optional[str] = Query(None, description="等級篩選 (A+, A, B+, etc.)"),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """獲取所有策略評分"""
    query = db.query(Score).join(Strategy)
    
    if grade:
        query = query.filter(Score.grade == grade)
    
    if min_score is not None:
        query = query.filter(Score.score >= min_score)
    
    scores = query.order_by(Score.score.desc()).limit(limit).all()
    
    # 添加策略名稱
    results = []
    for score in scores:
        result = ScoreResponse.from_orm(score)
        result.strategy_name = score.strategy.name
        results.append(result)
    
    return results


@router.get("/ranking", response_model=List[ScoreRanking])
def get_score_ranking(
    top_n: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """獲取評分排名"""
    scores = db.query(Score).join(Strategy).order_by(
        Score.score.desc()
    ).limit(top_n).all()
    
    rankings = []
    for rank, score in enumerate(scores, 1):
        rankings.append(ScoreRanking(
            rank=rank,
            strategy_id=score.strategy_id,
            strategy_name=score.strategy.name,
            score=score.score,
            grade=score.grade,
            sharpe_ratio=score.sharpe_ratio
        ))
    
    return rankings


@router.get("/{strategy_name}", response_model=ScoreResponse)
def get_strategy_score(strategy_name: str, db: Session = Depends(get_db)):
    """獲取策略評分"""
    strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    score = db.query(Score).filter(Score.strategy_id == strategy.id).first()
    
    if not score:
        raise HTTPException(status_code=404, detail="評分不存在")
    
    result = ScoreResponse.from_orm(score)
    result.strategy_name = strategy.name
    return result


@router.post("/{strategy_name}", response_model=ScoreResponse)
def create_or_update_score(
    strategy_name: str,
    score_data: ScoreResponse,
    db: Session = Depends(get_db)
):
    """創建或更新策略評分"""
    strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    # 檢查是否已存在評分
    existing_score = db.query(Score).filter(Score.strategy_id == strategy.id).first()
    
    if existing_score:
        # 更新
        existing_score.score = score_data.score
        existing_score.grade = score_data.grade
        existing_score.sharpe_ratio = score_data.sharpe_ratio
        existing_score.total_return = score_data.total_return
        existing_score.max_drawdown = score_data.max_drawdown
        existing_score.win_rate = score_data.win_rate
        existing_score.profit_factor = score_data.profit_factor
        existing_score.evaluated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_score)
        result = existing_score
    else:
        # 創建
        new_score = Score(
            strategy_id=strategy.id,
            score=score_data.score,
            grade=score_data.grade,
            sharpe_ratio=score_data.sharpe_ratio,
            total_return=score_data.total_return,
            max_drawdown=score_data.max_drawdown,
            win_rate=score_data.win_rate,
            profit_factor=score_data.profit_factor
        )
        db.add(new_score)
        db.commit()
        db.refresh(new_score)
        result = new_score
    
    response = ScoreResponse.from_orm(result)
    response.strategy_name = strategy_name
    return response


@router.delete("/{strategy_name}", response_model=MessageResponse)
def delete_score(strategy_name: str, db: Session = Depends(get_db)):
    """刪除策略評分"""
    strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    score = db.query(Score).filter(Score.strategy_id == strategy.id).first()
    
    if not score:
        raise HTTPException(status_code=404, detail="評分不存在")
    
    db.delete(score)
    db.commit()
    
    return MessageResponse(message=f"策略 {strategy_name} 的評分已刪除", success=True)


@router.get("/statistics/grade-distribution")
def get_grade_distribution(db: Session = Depends(get_db)):
    """獲取等級分佈統計"""
    from sqlalchemy import func
    
    distribution = db.query(
        Score.grade,
        func.count(Score.id).label('count')
    ).group_by(Score.grade).order_by(Score.grade).all()
    
    return {
        "distribution": {grade: count for grade, count in distribution},
        "total": sum(count for _, count in distribution)
    }
