"""
AetherVerse Server — Auth API 路由
/api/v1/auth/*
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user_id
from app.core.security import decode_token
from app.services import auth_service

router = APIRouter()


# ---- Request/Response Schemas ----

class SmsSendRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    purpose: str = Field(default="login", pattern=r"^(register|login|reset_password)$")


class RegisterRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=6, max_length=6)
    password: str = Field(..., min_length=8, max_length=20)
    nickname: str = Field(..., min_length=2, max_length=16)


class PasswordLoginRequest(BaseModel):
    phone: str
    password: str


class SmsLoginRequest(BaseModel):
    phone: str
    code: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    phone: str
    code: str
    new_password: str = Field(..., min_length=8, max_length=20)


# ---- Endpoints ----

@router.post("/sms/send")
async def send_sms(body: SmsSendRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """发送短信验证码"""
    ip = request.client.host if request.client else "127.0.0.1"
    result = await auth_service.send_sms_code(db, body.phone, body.purpose, ip)
    return {"code": 0, "message": "success", "data": result}


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """手机号注册"""
    result = await auth_service.register(db, body.phone, body.code, body.password, body.nickname)
    return {"code": 0, "message": "success", "data": result}


@router.post("/login/password")
async def login_password(body: PasswordLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """密码登录"""
    ip = request.client.host if request.client else "127.0.0.1"
    result = await auth_service.login_password(db, body.phone, body.password, ip)
    return {"code": 0, "message": "success", "data": result}


@router.post("/login/sms")
async def login_sms(body: SmsLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """验证码登录"""
    ip = request.client.host if request.client else "127.0.0.1"
    result = await auth_service.login_sms(db, body.phone, body.code, ip)
    return {"code": 0, "message": "success", "data": result}


@router.post("/token/refresh")
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """刷新 Token"""
    result = await auth_service.refresh_token(db, body.refresh_token)
    return {"code": 0, "message": "success", "data": result}


@router.post("/password/reset")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """重置密码"""
    result = await auth_service.reset_password(db, body.phone, body.code, body.new_password)
    return {"code": 0, "message": "success", "data": result}


@router.post("/logout")
async def logout(
    request: Request,
    user_id=Depends(get_current_user_id),
):
    """退出登录"""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
    try:
        payload = decode_token(token)
        jti = payload.get("jti", "")
        exp = payload.get("exp", 0)
        result = await auth_service.logout(jti, exp)
    except Exception:
        result = {"message": "已退出"}
    return {"code": 0, "message": "success", "data": result}
