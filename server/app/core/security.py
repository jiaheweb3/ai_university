"""
AetherVerse Server — 安全工具
JWT 签发/验证、密码哈希、手机号加密
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# ---- 密码 ----
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ---- JWT ----

def create_access_token(user_id: str, extra: dict | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "jti": uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "jti": uuid4().hex,
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码 JWT, 失败抛 JWTError"""
    settings = get_settings()
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def create_token_pair(user_id: str) -> dict:
    """创建 access + refresh token 对"""
    settings = get_settings()
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# ---- 手机号 ----

def hash_phone(phone: str) -> str:
    """SHA-256 哈希手机号 (用于查重/索引)"""
    return hashlib.sha256(phone.encode()).hexdigest()


def encrypt_phone(phone: str) -> bytes:
    """AES 加密手机号存储 (Phase 1 简化: XOR 混淆, 生产环境换 AES-256-GCM)"""
    settings = get_settings()
    key = settings.PHONE_AES_KEY.encode()[:16]
    phone_bytes = phone.encode()
    # 简化加密: 使用 XOR + random nonce (Phase 1 开发阶段)
    # 生产环境切换为 cryptography.fernet 或 AES-GCM
    nonce = secrets.token_bytes(16)
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(phone_bytes))
    return nonce + encrypted


def decrypt_phone(encrypted: bytes) -> str:
    """解密手机号"""
    settings = get_settings()
    key = settings.PHONE_AES_KEY.encode()[:16]
    # 跳过 16 字节 nonce
    data = encrypted[16:]
    decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return decrypted.decode()


# Re-export for convenience
__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "hash_phone",
    "encrypt_phone",
    "decrypt_phone",
    "JWTError",
]
