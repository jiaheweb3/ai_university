"""
AetherVerse Server — FastAPI 依赖注入
"""

from uuid import UUID

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis_pool
from app.core.security import decode_token
from shared.constants import UserStatus
from shared.exceptions import UnauthorizedError


async def get_current_user_id(authorization: str = Header(..., alias="Authorization")) -> UUID:
    """从 Authorization: Bearer <token> 解析出 user_id"""
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError(message="请提供有效的 Bearer Token")
    token = authorization[7:]

    try:
        payload = decode_token(token)
    except JWTError:
        raise UnauthorizedError(message="Token 无效或已过期")

    if payload.get("type") != "access":
        raise UnauthorizedError(message="请使用 access_token")

    # 检查 Redis 黑名单
    redis = get_redis_pool()
    jti = payload.get("jti", "")
    if await redis.exists(f"jwt:blacklist:{jti}"):
        raise UnauthorizedError(message="Token 已被注销")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError(message="Token 数据异常")

    return UUID(user_id)


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户 ORM 对象"""
    from app.models.user import User  # 延迟导入避免循环

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError(message="用户不存在")
    return user


async def get_current_active_user(
    user=Depends(get_current_user),
):
    """获取当前活跃用户 (未被封禁/删除)"""
    from shared.exceptions import AppException, ErrorCode

    if user.status == UserStatus.DELETED:
        raise AppException(code=ErrorCode.ACCOUNT_DELETED, message="账号已注销", status_code=401)
    if user.status in (UserStatus.BANNED_TEMP, UserStatus.BANNED_PERM):
        raise AppException(code=ErrorCode.ACCOUNT_BANNED, message="账号已被封禁", status_code=403)

    return user
