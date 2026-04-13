#!/usr/bin/env python3
"""
StocksX 數據庫配置
SQLite + SQLAlchemy

作者：StocksX Team
創建日期：2026-03-22
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# 數據庫路徑
DB_PATH = Path(__file__).parent.parent / "data" / "stocksx.db"
DB_PATH.parent.mkdir(exist_ok=True)

# SQLite 連接字符串
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 創建引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要
)

# 會話工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基類
Base = declarative_base()


# 依賴注入
def get_db():
    """獲取數據庫會話"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 初始化數據庫
def init_db():
    """創建所有表"""

    Base.metadata.create_all(bind=engine)
    print(f"✅ 數據庫已創建：{DB_PATH}")


if __name__ == "__main__":
    init_db()
