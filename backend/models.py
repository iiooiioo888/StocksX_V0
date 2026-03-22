#!/usr/bin/env python3
"""
StocksX 數據模型
SQLAlchemy ORM Models

作者：StocksX Team
創建日期：2026-03-22
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Strategy(Base):
    """策略表"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=False)  # trend, oscillator, breakout, etc.
    description = Column(Text)
    params = Column(Text)  # JSON 字符串存儲參數
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關係
    signals = relationship("Signal", back_populates="strategy")
    scores = relationship("Score", back_populates="strategy")
    
    def __repr__(self):
        return f"<Strategy(name='{self.name}', category='{self.category}')>"


class Signal(Base):
    """信號表"""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(Text)  # JSON 字符串存儲額外信息
    
    # 關係
    strategy = relationship("Strategy", back_populates="signals")
    
    def __repr__(self):
        return f"<Signal(strategy_id={self.strategy_id}, type='{self.signal_type}')>"


class Portfolio(Base):
    """投資組合表"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    initial_capital = Column(Float, default=1000000.0)
    current_value = Column(Float, default=1000000.0)
    weights = Column(Text)  # JSON 字符串存儲策略權重
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Portfolio(name='{self.name}', value={self.current_value})>"


class Score(Base):
    """策略評分表"""
    __tablename__ = "scores"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    score = Column(Float, nullable=False)  # 0-100
    grade = Column(String(5), nullable=False)  # A+, A, B+, etc.
    sharpe_ratio = Column(Float)
    total_return = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    
    # 關係
    strategy = relationship("Strategy", back_populates="scores")
    
    def __repr__(self):
        return f"<Score(strategy_id={self.strategy_id}, score={self.score})>"


class BacktestResult(Base):
    """回測結果表"""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_value = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    total_trades = Column(Integer)
    win_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BacktestResult(return={self.total_return}, sharpe={self.sharpe_ratio})>"
