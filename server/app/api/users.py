"""
AetherVerse Server — Users API 路由
/api/v1/users/*
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.services import user_service

router = APIRouter()


# ---- Request Schemas ----

class UpdateProfileRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=2, max_length=16)
    avatar_url: str | None = None
    bio: str | None = Field(default=None, max_length=200)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=20)


class UpdateSettingsRequest(BaseModel):
    notification_enabled: bool | None = None
    privacy_show_agents: bool | None = None


class DeleteAccountRequest(BaseModel):
    code: str  # 短信验证码确认
    reason: str | None = Field(default=None, max_length=200)


class BlockRequest(BaseModel):
    blocked_type: str = Field(default="user", pattern=r"^(user|agent)$")


# ---- Endpoints ----

@router.get("/me")
async def get_me(user=Depends(get_current_active_user)):
    """获取当前用户信息"""
    data = user_service._user_public_dict(user)
    return {"code": 0, "message": "success", "data": data}


@router.patch("/me")
async def update_me(
    body: UpdateProfileRequest,
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新个人资料"""
    data = await user_service.update_profile(
        db, user,
        nickname=body.nickname,
        avatar_url=body.avatar_url,
        bio=body.bio,
    )
    return {"code": 0, "message": "success", "data": data}


@router.delete("/me")
async def delete_me(
    body: DeleteAccountRequest,
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """注销账号"""
    # Phase 1: 暂不校验验证码, 直接注销
    data = await user_service.delete_account(db, user)
    return {"code": 0, "message": "success", "data": data}


@router.put("/me/password")
async def change_password(
    body: ChangePasswordRequest,
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    data = await user_service.change_password(db, user, body.old_password, body.new_password)
    return {"code": 0, "message": "success", "data": data}


@router.get("/me/settings")
async def get_settings(
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户设置"""
    data = await user_service.get_settings(db, user.id)
    return {"code": 0, "message": "success", "data": data}


@router.patch("/me/settings")
async def update_settings(
    body: UpdateSettingsRequest,
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户设置"""
    data = await user_service.update_settings(
        db, user.id,
        notification_enabled=body.notification_enabled,
        privacy_show_agents=body.privacy_show_agents,
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """查看用户主页"""
    data = await user_service.get_profile(db, user_id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{user_id}/block")
async def block_user(
    user_id: UUID,
    body: BlockRequest = BlockRequest(),
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """屏蔽用户/智能体"""
    data = await user_service.block_user(db, user.id, user_id, body.blocked_type)
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{user_id}/block")
async def unblock_user(
    user_id: UUID,
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """取消屏蔽"""
    data = await user_service.unblock_user(db, user.id, user_id)
    return {"code": 0, "message": "success", "data": data}
