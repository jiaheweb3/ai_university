"""
AetherVerse Server — Rooms API 路由
/api/v1/rooms/*
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.services import room_service

router = APIRouter()


@router.get("")
async def list_rooms(
    category: str | None = None,
    sort: str = Query(default="hot", pattern=r"^(hot|new|joined)$"),
    search: str | None = None,
    after: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """房间列表"""
    data = await room_service.list_rooms(
        db, user_id=user.id,
        category=category, search=search,
        sort=sort, after=after, limit=limit,
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{room_id}")
async def get_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """房间详情"""
    data = await room_service.get_room_detail(db, room_id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{room_id}/join")
async def join_room(
    room_id: UUID,
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """加入房间"""
    data = await room_service.join_room(db, room_id, user.id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{room_id}/leave")
async def leave_room(
    room_id: UUID,
    user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """离开房间"""
    data = await room_service.leave_room(db, room_id, user.id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{room_id}/members")
async def get_members(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """房间成员列表"""
    data = await room_service.get_members(db, room_id)
    return {"code": 0, "message": "success", "data": data}
