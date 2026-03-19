"""
AetherVerse Server — 房间服务
列表/详情/加入/离开/成员
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis_pool
from app.models.room import Room, RoomMember
from app.models.user import User
from app.models.agent import Agent
from shared.constants import RoomStatus
from shared.exceptions import AppException, ErrorCode, NotFoundError


async def list_rooms(
    db: AsyncSession,
    user_id: UUID | None = None,
    category: str | None = None,
    search: str | None = None,
    sort: str = "hot",
    after: str | None = None,
    limit: int = 20,
) -> dict:
    """房间列表 (cursor 分页)"""
    query = select(Room).where(Room.status == RoomStatus.ACTIVE)

    if category:
        query = query.where(Room.category == category)

    if search:
        query = query.where(Room.name.ilike(f"%{search}%"))

    if sort == "hot":
        query = query.order_by(Room.online_count.desc(), Room.created_at.desc())
    elif sort == "new":
        query = query.order_by(Room.created_at.desc())
    elif sort == "joined" and user_id:
        # 只显示用户加入的房间
        query = query.join(
            RoomMember,
            (RoomMember.room_id == Room.id)
            & (RoomMember.member_id == user_id)
            & (RoomMember.member_type == "user")
            & (RoomMember.left_at.is_(None)),
        )
        query = query.order_by(Room.created_at.desc())
    else:
        query = query.order_by(Room.created_at.desc())

    # cursor 分页
    if after:
        try:
            cursor_id = UUID(after)
            result = await db.execute(select(Room.created_at).where(Room.id == cursor_id))
            cursor_time = result.scalar_one_or_none()
            if cursor_time:
                query = query.where(Room.created_at < cursor_time)
        except ValueError:
            pass

    query = query.limit(limit + 1)
    result = await db.execute(query)
    rooms = result.scalars().all()

    has_more = len(rooms) > limit
    items = rooms[:limit]

    return {
        "items": [_room_to_dict(r) for r in items],
        "next_cursor": str(items[-1].id) if has_more and items else None,
        "has_more": has_more,
    }


async def get_room_detail(db: AsyncSession, room_id: UUID) -> dict:
    """房间详情 (含成员列表)"""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()
    if room is None:
        raise NotFoundError(code=ErrorCode.ROOM_NOT_FOUND, message="房间不存在")

    # 获取在线人数 (优先 Redis, 回退 DB)
    redis = get_redis_pool()
    online_count = await redis.get(f"room:online:{room_id}")
    if online_count is not None:
        room_dict = _room_to_dict(room)
        room_dict["online_count"] = int(online_count)
    else:
        room_dict = _room_to_dict(room)

    # 获取成员列表
    members = await get_members(db, room_id)
    room_dict["members"] = members["items"]

    return room_dict


async def join_room(
    db: AsyncSession,
    room_id: UUID,
    user_id: UUID,
) -> dict:
    """加入房间"""
    # 检查房间是否存在
    result = await db.execute(
        select(Room).where(Room.id == room_id, Room.status == RoomStatus.ACTIVE)
    )
    room = result.scalar_one_or_none()
    if room is None:
        raise NotFoundError(code=ErrorCode.ROOM_NOT_FOUND, message="房间不存在")

    # 检查是否已加入
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.member_id == user_id,
            RoomMember.member_type == "user",
            RoomMember.left_at.is_(None),
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise AppException(code=ErrorCode.ALREADY_JOINED, message="已在房间中", status_code=409)

    # 检查房间人数上限
    member_count_result = await db.execute(
        select(func.count()).select_from(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.left_at.is_(None),
        )
    )
    count = member_count_result.scalar()
    if count >= room.max_members:
        raise AppException(code=ErrorCode.ROOM_FULL, message="房间已满", status_code=409)

    # 加入
    member = RoomMember(
        room_id=room_id,
        member_id=user_id,
        member_type="user",
        is_online=True,
    )
    db.add(member)
    await db.commit()

    # Redis 在线计数 +1
    redis = get_redis_pool()
    await redis.incr(f"room:online:{room_id}")

    return {"message": "已加入房间"}


async def leave_room(
    db: AsyncSession,
    room_id: UUID,
    user_id: UUID,
) -> dict:
    """离开房间"""
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.member_id == user_id,
            RoomMember.member_type == "user",
            RoomMember.left_at.is_(None),
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise NotFoundError(code=ErrorCode.ROOM_NOT_FOUND, message="未加入该房间")

    member.left_at = datetime.now(UTC)
    member.is_online = False
    await db.commit()

    # Redis 在线计数 -1
    redis = get_redis_pool()
    await redis.decr(f"room:online:{room_id}")

    return {"message": "已离开房间"}


async def get_members(
    db: AsyncSession,
    room_id: UUID,
) -> dict:
    """房间成员列表 (含智能体)"""
    result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.left_at.is_(None),
        )
        .order_by(RoomMember.joined_at)
    )
    members = result.scalars().all()

    items = []
    for m in members:
        if m.member_type == "user":
            user_result = await db.execute(select(User).where(User.id == m.member_id))
            user = user_result.scalar_one_or_none()
            if user:
                items.append({
                    "id": str(m.member_id),
                    "member_type": "user",
                    "nickname": user.nickname,
                    "avatar_url": user.avatar_url,
                    "is_online": m.is_online,
                    "is_ai": False,
                })
        elif m.member_type == "agent":
            agent_result = await db.execute(select(Agent).where(Agent.id == m.member_id))
            agent = agent_result.scalar_one_or_none()
            if agent:
                # 获取 owner 昵称
                owner_nickname = None
                if agent.owner_id:
                    owner_result = await db.execute(
                        select(User.nickname).where(User.id == agent.owner_id)
                    )
                    owner_nickname = owner_result.scalar_one_or_none()
                items.append({
                    "id": str(m.member_id),
                    "member_type": "agent",
                    "nickname": agent.name,
                    "avatar_url": agent.avatar_url,
                    "is_online": m.is_online,
                    "is_ai": True,
                    "owner_nickname": owner_nickname,
                })

    return {"items": items}


def _room_to_dict(room: Room) -> dict:
    return {
        "id": str(room.id),
        "name": room.name,
        "description": room.description,
        "category": room.category,
        "tags": room.tags or [],
        "cover_url": room.cover_url,
        "status": room.status,
        "online_count": room.online_count,
        "message_count": room.message_count,
        "max_members": room.max_members,
        "created_at": room.created_at.isoformat() if room.created_at else None,
    }
