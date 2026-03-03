# API Routers - 認證相關
from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core import security, logger
from ..core.config import settings
from ..models import User, get_db
from ..schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    PasswordChange,
)

router = APIRouter(prefix="/auth", tags=["認證"])
security_scheme = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    用戶註冊
    
    - **username**: 帳號（至少 3 個字元）
    - **password**: 密碼（至少 6 個字元）
    - **display_name**: 顯示名稱（可選）
    - **email**: 電子郵件（可選）
    """
    log = logger.get_logger("stocksx.api.auth")
    
    # 檢查用戶是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="帳號已存在"
        )
    
    # 創建新用戶
    hashed_password = security.hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        display_name=user_data.display_name or user_data.username,
        email=user_data.email,
        role="user",
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log.info(f"用戶註冊成功：{new_user.username}")
    
    return new_user


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)) -> Any:
    """
    用戶登入
    
    返回 JWT Access Token 和 Refresh Token
    """
    log = logger.get_logger("stocksx.api.auth")
    
    # 查詢用戶
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not user.is_active:
        log.warning(f"登入失敗：用戶不存在或未啟用 - {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 驗證密碼
    if not security.verify_password(login_data.password, user.password_hash):
        log.warning(f"登入失敗：密碼錯誤 - {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新最後登入時間
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 建立令牌
    access_token = security.create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        }
    )
    refresh_token = security.create_refresh_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        }
    )
    
    log.info(f"用戶登入成功：{user.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Any:
    """
    刷新令牌
    
    使用 Refresh Token 換取新的 Access Token
    """
    log = logger.get_logger("stocksx.api.auth")
    
    token = credentials.credentials
    payload = security.verify_token(token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效或已過期的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查詢用戶
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶不存在或未啟用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 建立新令牌
    new_access_token = security.create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        }
    )
    new_refresh_token = security.create_refresh_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        }
    )
    
    log.info(f"令牌刷新成功：{user.username}")
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Any:
    """
    取得當前用戶資訊
    """
    token = credentials.credentials
    payload = security.verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效或已過期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    return user


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Any:
    """
    修改密碼
    """
    log = logger.get_logger("stocksx.api.auth")
    
    token = credentials.credentials
    payload = security.verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效或已過期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    # 驗證舊密碼
    if not security.verify_password(password_data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="舊密碼錯誤"
        )
    
    # 更新密碼
    user.password_hash = security.hash_password(password_data.new_password)
    db.commit()
    
    log.info(f"用戶密碼已修改：{user.username}")
    
    return {"message": "密碼已修改"}
