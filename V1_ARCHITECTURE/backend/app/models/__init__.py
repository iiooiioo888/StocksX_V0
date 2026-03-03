# SQLAlchemy 資料庫模型
from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from ..core.config import settings

Base = declarative_base()


class User(Base):
    """用戶模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), default="")
    email = Column(String(255), nullable=True)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # 關聯
    backtests = relationship("BacktestHistory", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"


class BacktestHistory(Base):
    """回測歷史模型"""
    __tablename__ = "backtest_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(50), default="")
    timeframe = Column(String(20), default="")
    strategy = Column(String(50), default="")
    params = Column(Text, default="{}")  # JSON
    metrics = Column(Text, default="{}")  # JSON
    notes = Column(Text, default="")
    tags = Column(String(200), default="")
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    user = relationship("User", back_populates="backtests")
    
    def __repr__(self) -> str:
        return f"<BacktestHistory(id={self.id}, symbol='{self.symbol}', strategy='{self.strategy}')>"


class Product(Base):
    """交易對產品模型"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False)
    name = Column(String(100), default="")
    exchange = Column(String(50), default="")
    market_type = Column(String(20), default="crypto")
    category = Column(String(50), default="")
    is_system = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, symbol='{self.symbol}')>"


class UserSettings(Base):
    """用戶設定模型"""
    __tablename__ = "user_settings"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    settings = Column(Text, default="{}")  # JSON


class StrategyPreset(Base):
    """策略預設模型"""
    __tablename__ = "strategy_presets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    config = Column(Text, nullable=False)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)


class Watchlist(Base):
    """監控清單模型"""
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(50), default="binance")
    timeframe = Column(String(20), default="1h")
    strategy = Column(String(50), nullable=False)
    strategy_params = Column(Text, default="{}")  # JSON
    initial_equity = Column(Float, default=10000.0)
    leverage = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_check = Column(DateTime, nullable=True)
    last_signal = Column(Integer, default=0)  # 0: none, 1: buy, -1: sell
    last_price = Column(Float, default=0.0)
    entry_price = Column(Float, default=0.0)
    position = Column(Integer, default=0)  # 0: none, 1: long, -1: short
    pnl_pct = Column(Float, default=0.0)


class Alert(Base):
    """提醒模型"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    condition_type = Column(String(50), nullable=False)
    threshold = Column(Float, nullable=False)
    message = Column(Text, default="")
    is_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class LoginLog(Base):
    """登入日誌模型"""
    __tablename__ = "login_log"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, index=True)
    ip = Column(String(50), default="")
    success = Column(Boolean, nullable=False)
    reason = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# 資料庫引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """取得資料庫 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化資料庫"""
    Base.metadata.create_all(bind=engine)
