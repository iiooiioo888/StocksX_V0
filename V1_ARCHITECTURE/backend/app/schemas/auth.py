# Pydantic Schemas - 認證相關
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """用戶基礎 Schema"""
    username: str = Field(..., min_length=3, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """用戶創建請求"""
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """用戶登入請求"""
    username: str
    password: str


class UserResponse(UserBase):
    """用戶響應"""
    id: int
    role: str = "user"
    is_active: bool = True
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """令牌響應"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """令牌負載"""
    sub: Optional[str] = None  # user_id
    username: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    type: Optional[str] = None


class PasswordChange(BaseModel):
    """密碼修改請求"""
    old_password: str
    new_password: str = Field(..., min_length=6)
