"""
AetherVerse Server — 用户服务
个人资料/设置/屏蔽/注销
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserBlock, UserSetting
from shared.constants import UserStatus
from shared.exceptions import AppException, ErrorCode, ForbiddenError, NotFoundError


async def get_profile(db: AsyncSession, user_id: UUID) -> dict:
    """获取用户公开资料"""
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(code=ErrorCode.USER_NOT_FOUND, message="用户不存在")
    return _user_public_dict(user)


async def update_profile(
    db: AsyncSession,
    user: User,
    nickname: str | None = None,
    avatar_url: str | None = None,
    bio: str | None = None,
) -> dict:
    """更新个人资料"""
    if nickname is not None:
        user.nickname = nickname
    if avatar_url is not None:
        user.avatar_url = avatar_url
    if bio is not None:
        user.bio = bio
    user.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)
    return _user_public_dict(user)


async def change_password(
    db: AsyncSession,
    user: User,
    old_password: str,
    new_password: str,
) -> dict:
    """修改密码"""
    if not verify_password(old_password, user.password_hash):
        raise AppException(code=ErrorCode.PASSWORD_WRONG, message="原密码错误", status_code=400)
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(UTC)
    await db.commit()
    return {"message": "密码已修改"}


async def get_settings(db: AsyncSession, user_id: UUID) -> dict:
    """获取用户设置"""
    result = await db.execute(
        select(UserSetting).where(UserSetting.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        # 自动创建默认设置
        settings = UserSetting(user_id=user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return {
        "notification_enabled": settings.notification_enabled,
        "privacy_show_agents": settings.privacy_show_agents,
    }


async def update_settings(
    db: AsyncSession,
    user_id: UUID,
    notification_enabled: bool | None = None,
    privacy_show_agents: bool | None = None,
) -> dict:
    """更新用户设置"""
    result = await db.execute(
        select(UserSetting).where(UserSetting.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = UserSetting(user_id=user_id)
        db.add(settings)

    if notification_enabled is not None:
        settings.notification_enabled = notification_enabled
    if privacy_show_agents is not None:
        settings.privacy_show_agents = privacy_show_agents
    settings.updated_at = datetime.now(UTC)
    await db.commit()
    return {
        "notification_enabled": settings.notification_enabled,
        "privacy_show_agents": settings.privacy_show_agents,
    }


async def delete_account(db: AsyncSession, user: User) -> dict:
    """注销账号 (软删除)"""
    user.status = UserStatus.DELETED
    user.deleted_at = datetime.now(UTC)
    user.nickname = f"已注销用户_{str(user.id)[:8]}"
    user.bio = None
    user.avatar_url = None
    await db.commit()
    return {"message": "账号已注销，30 天内可联系客服恢复"}


async def block_user(
    db: AsyncSession,
    blocker_id: UUID,
    blocked_id: UUID,
    blocked_type: str = "user",
) -> dict:
    """屏蔽用户/智能体"""
    # 检查是否已屏蔽
    result = await db.execute(
        select(UserBlock).where(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id,
        )
    )
    if result.scalar_one_or_none():
        return {"message": "已屏蔽"}

    block = UserBlock(
        blocker_id=blocker_id,
        blocked_id=blocked_id,
        blocked_type=blocked_type,
    )
    db.add(block)
    await db.commit()
    return {"message": "已屏蔽"}


async def unblock_user(
    db: AsyncSession,
    blocker_id: UUID,
    blocked_id: UUID,
) -> dict:
    """取消屏蔽"""
    await db.execute(
        delete(UserBlock).where(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id,
        )
    )
    await db.commit()
    return {"message": "已取消屏蔽"}


def _user_public_dict(user: User) -> dict:
    """User ORM → 公开响应 dict"""
    return {
        "id": str(user.id),
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "points_balance": user.points_balance,
        "agent_count": user.agent_count,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
