# 安全認證模組（JWT、密碼加密）
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from passlib.context import CryptContext

from .config import settings


# 密碼加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """密碼哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """建立存取令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """建立刷新令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """解碼令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[dict[str, Any]]:
    """驗證令牌"""
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if payload.get("type") != token_type:
        return None
    
    return payload


def get_current_user_from_token(token: str) -> Optional[dict[str, Any]]:
    """從令牌取得當前用戶資訊"""
    payload = verify_token(token, token_type="access")
    
    if payload is None:
        return None
    
    return {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "role": payload.get("role", "user")
    }
