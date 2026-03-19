"""
AetherVerse Server — Rooms API 集成测试
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ---- Helper: 创建测试房间 ----

async def create_test_room(db: AsyncSession, name: str = "测试房间", category: str = "general") -> str:
    """直接插入测试房间, 返回 room_id"""
    room_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO rooms (id, name, description, category, status, max_members)
        VALUES (:id, :name, '房间描述', :category, 'active', 200)
    """), {"id": room_id, "name": name, "category": category})
    await db.commit()
    return room_id


# ============================================================
# GET /rooms
# ============================================================

@pytest.mark.asyncio
async def test_list_rooms_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/rooms", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "has_more" in data


@pytest.mark.asyncio
async def test_list_rooms_with_data(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    await create_test_room(db, "聊天室A")
    await create_test_room(db, "聊天室B")

    resp = await client.get("/api/v1/rooms", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) >= 2


@pytest.mark.asyncio
async def test_list_rooms_with_category(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    await create_test_room(db, "兴趣房间", category="interest")

    resp = await client.get("/api/v1/rooms?category=interest", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    for item in items:
        assert item["category"] == "interest"


@pytest.mark.asyncio
async def test_list_rooms_with_search(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    await create_test_room(db, "独特名称XYZ")

    resp = await client.get("/api/v1/rooms?search=XYZ", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert any("XYZ" in item["name"] for item in items)


@pytest.mark.asyncio
async def test_list_rooms_pagination(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    for i in range(5):
        await create_test_room(db, f"分页房间{i}")

    resp = await client.get("/api/v1/rooms?limit=2", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    # items may be 2 or more depending on ordering
    assert len(data["items"]) <= 2


# ============================================================
# GET /rooms/{room_id}
# ============================================================

@pytest.mark.asyncio
async def test_get_room_detail(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    room_id = await create_test_room(db, "详情房间")

    resp = await client.get(f"/api/v1/rooms/{room_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "详情房间"
    assert data["id"] == room_id


@pytest.mark.asyncio
async def test_get_room_not_found(client: AsyncClient, auth_headers: dict):
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/api/v1/rooms/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


# ============================================================
# POST /rooms/{room_id}/join
# ============================================================

@pytest.mark.asyncio
async def test_join_room(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    room_id = await create_test_room(db, "加入房间")

    resp = await client.post(f"/api/v1/rooms/{room_id}/join", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_join_room_twice(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    """重复加入同一房间应报冲突"""
    room_id = await create_test_room(db, "重复加入")

    await client.post(f"/api/v1/rooms/{room_id}/join", headers=auth_headers)
    resp = await client.post(f"/api/v1/rooms/{room_id}/join", headers=auth_headers)
    assert resp.status_code == 409
    assert resp.json()["code"] == 40905  # ALREADY_JOINED


# ============================================================
# POST /rooms/{room_id}/leave
# ============================================================

@pytest.mark.asyncio
async def test_leave_room(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    room_id = await create_test_room(db, "离开房间")

    # 先加入再离开
    await client.post(f"/api/v1/rooms/{room_id}/join", headers=auth_headers)
    resp = await client.post(f"/api/v1/rooms/{room_id}/leave", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_leave_room_not_joined(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    room_id = await create_test_room(db, "未加入")

    resp = await client.post(f"/api/v1/rooms/{room_id}/leave", headers=auth_headers)
    assert resp.status_code == 404


# ============================================================
# GET /rooms/{room_id}/members
# ============================================================

@pytest.mark.asyncio
async def test_get_members(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    room_id = await create_test_room(db, "成员列表")

    # 加入
    await client.post(f"/api/v1/rooms/{room_id}/join", headers=auth_headers)

    resp = await client.get(f"/api/v1/rooms/{room_id}/members", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) >= 1
    assert items[0]["member_type"] == "user"
    assert items[0]["is_ai"] is False


@pytest.mark.asyncio
async def test_get_members_empty_room(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    room_id = await create_test_room(db, "空房间")

    resp = await client.get(f"/api/v1/rooms/{room_id}/members", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["items"] == []
