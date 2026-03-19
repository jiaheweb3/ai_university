"""
AetherVerse Server — 认证服务
注册/登录/Token/密码/注销
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import get_redis_pool
from app.core.security import (
    create_token_pair,
    decode_token,
    hash_password,
    hash_phone,
    encrypt_phone,
    verify_password,
)
from app.models.auxiliary import SmsCode
from app.models.user import LoginAttempt, User, UserDID, UserSetting
from shared.constants import UserStatus
from shared.exceptions import (
    AppException,
    ErrorCode,
    NotFoundError,
    UnauthorizedError,
)


async def send_sms_code(
    db: AsyncSession,
    phone: str,
    purpose: str = "login",
    ip_address: str = "127.0.0.1",
) -> dict:
    """发送短信验证码 (Phase 1: mock 固定码)"""
    settings = get_settings()
    phone_h = hash_phone(phone)

    # Redis 限频: 60 秒内同一手机号不重发
    redis = get_redis_pool()
    rate_key = f"sms:rate:{phone_h}:{purpose}"
    if await redis.exists(rate_key):
        raise AppException(
            code=ErrorCode.SMS_RATE_LIMITED,
            message="验证码发送过于频繁，请 60 秒后重试",
            status_code=429,
        )

    # 生成验证码 (Phase 1 mock)
    code = settings.SMS_MOCK_CODE if settings.SMS_MOCK else str(uuid4().int)[:6]

    # 写入 DB
    sms = SmsCode(
        phone_hash=phone_h,
        code=code,
        purpose=purpose,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    db.add(sms)
    await db.commit()

    # 设置限频 60 秒
    await redis.setex(rate_key, 60, "1")

    return {"message": "验证码已发送"}


async def verify_sms_code(
    db: AsyncSession,
    phone: str,
    code: str,
    purpose: str = "login",
) -> bool:
    """校验短信验证码"""
    phone_h = hash_phone(phone)
    now = datetime.now(UTC)

    result = await db.execute(
        select(SmsCode)
        .where(
            SmsCode.phone_hash == phone_h,
            SmsCode.purpose == purpose,
            SmsCode.is_used == False,  # noqa: E712
            SmsCode.expires_at > now,
        )
        .order_by(SmsCode.created_at.desc())
        .limit(1)
    )
    sms = result.scalar_one_or_none()
    if sms is None or sms.code != code:
        raise AppException(
            code=ErrorCode.SMS_CODE_INVALID,
            message="验证码错误或已过期",
            status_code=400,
        )

    sms.is_used = True
    await db.commit()
    return True


async def register(
    db: AsyncSession,
    phone: str,
    code: str,
    password: str,
    nickname: str,
) -> dict:
    """用户注册"""
    # 1. 校验验证码
    await verify_sms_code(db, phone, code, purpose="register")

    # 2. 检查手机号是否已注册
    phone_h = hash_phone(phone)
    result = await db.execute(
        select(User).where(User.phone_hash == phone_h, User.deleted_at.is_(None))
    )
    if result.scalar_one_or_none():
        raise AppException(
            code=ErrorCode.PHONE_REGISTERED, message="该手机号已注册", status_code=409
        )

    # 3. 创建用户
    user = User(
        phone_hash=phone_h,
        phone_encrypted=encrypt_phone(phone),
        password_hash=hash_password(password),
        nickname=nickname,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.flush()

    # 4. 创建 DID
    did = UserDID(
        user_id=user.id,
        did_value=f"did:aetherverse:{user.id}",
        is_verified=True,
    )
    db.add(did)

    # 5. 创建默认设置
    settings = UserSetting(user_id=user.id)
    db.add(settings)

    await db.commit()
    await db.refresh(user)

    # 6. 签发 Token
    tokens = create_token_pair(str(user.id))
    return {
        **tokens,
        "user": _user_to_dict(user),
    }


async def login_password(
    db: AsyncSession,
    phone: str,
    password: str,
    ip_address: str = "127.0.0.1",
    device_info: str | None = None,
) -> dict:
    """密码登录"""
    phone_h = hash_phone(phone)
    result = await db.execute(
        select(User).where(User.phone_hash == phone_h, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    # 记录登录尝试
    success = False
    failure_reason = None

    if user is None:
        failure_reason = "user_not_found"
    elif not verify_password(password, user.password_hash):
        failure_reason = "wrong_password"
    elif user.status == UserStatus.BANNED_TEMP or user.status == UserStatus.BANNED_PERM:
        failure_reason = "account_banned"
    else:
        success = True

    attempt = LoginAttempt(
        phone_hash=phone_h,
        ip_address=ip_address,
        device_info=device_info,
        success=success,
        failure_reason=failure_reason,
    )
    db.add(attempt)
    await db.commit()

    if not success:
        if failure_reason == "account_banned":
            raise AppException(code=ErrorCode.ACCOUNT_BANNED, message="账号已被封禁", status_code=403)
        raise AppException(code=ErrorCode.LOGIN_FAILED, message="手机号或密码错误", status_code=401)

    # 更新活跃时间
    user.last_active_at = datetime.now(UTC)
    await db.commit()

    tokens = create_token_pair(str(user.id))
    return {**tokens, "user": _user_to_dict(user)}


async def login_sms(
    db: AsyncSession,
    phone: str,
    code: str,
    ip_address: str = "127.0.0.1",
) -> dict:
    """验证码登录"""
    await verify_sms_code(db, phone, code, purpose="login")

    phone_h = hash_phone(phone)
    result = await db.execute(
        select(User).where(User.phone_hash == phone_h, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(code=ErrorCode.USER_NOT_FOUND, message="用户不存在，请先注册")
    if user.status in (UserStatus.BANNED_TEMP, UserStatus.BANNED_PERM):
        raise AppException(code=ErrorCode.ACCOUNT_BANNED, message="账号已被封禁", status_code=403)

    user.last_active_at = datetime.now(UTC)
    await db.commit()

    tokens = create_token_pair(str(user.id))
    return {**tokens, "user": _user_to_dict(user)}


async def refresh_token(db: AsyncSession, refresh_token_str: str) -> dict:
    """刷新 Token"""
    try:
        payload = decode_token(refresh_token_str)
    except Exception:
        raise UnauthorizedError(message="Refresh Token 无效或已过期")

    if payload.get("type") != "refresh":
        raise UnauthorizedError(message="请使用 refresh_token")

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError(message="用户不存在")

    return create_token_pair(str(user.id))


async def reset_password(
    db: AsyncSession,
    phone: str,
    code: str,
    new_password: str,
) -> dict:
    """重置密码"""
    await verify_sms_code(db, phone, code, purpose="reset_password")

    phone_h = hash_phone(phone)
    result = await db.execute(
        select(User).where(User.phone_hash == phone_h, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(code=ErrorCode.USER_NOT_FOUND, message="用户不存在")

    user.password_hash = hash_password(new_password)
    await db.commit()
    return {"message": "密码已重置"}


async def logout(token_jti: str, token_exp: int) -> dict:
    """退出登录 (JWT 加入黑名单)"""
    redis = get_redis_pool()
    ttl = max(token_exp - int(datetime.now(UTC).timestamp()), 0)
    if ttl > 0:
        await redis.setex(f"jwt:blacklist:{token_jti}", ttl, "1")
    return {"message": "已退出登录"}


def _user_to_dict(user: User) -> dict:
    """User ORM → 响应 dict"""
    return {
        "id": str(user.id),
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "points_balance": user.points_balance,
        "agent_count": user.agent_count,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
