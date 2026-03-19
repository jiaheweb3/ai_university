"""
AetherVerse Server — Users API 集成测试
"""

import pytest
from httpx import AsyncClient


# ============================================================
# GET /users/me
# ============================================================

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["nickname"] == "测试用户"
    assert "id" in data
    assert "points_balance" in data


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 422


# ============================================================
# PATCH /users/me
# ============================================================

@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, auth_headers: dict):
    resp = await client.patch("/api/v1/users/me", headers=auth_headers, json={
        "nickname": "改名了",
        "bio": "这是我的简介",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["nickname"] == "改名了"
    assert data["bio"] == "这是我的简介"


@pytest.mark.asyncio
async def test_update_profile_nickname_too_short(client: AsyncClient, auth_headers: dict):
    resp = await client.patch("/api/v1/users/me", headers=auth_headers, json={
        "nickname": "a",  # min 2 chars
    })
    assert resp.status_code == 422


# ============================================================
# PUT /users/me/password
# ============================================================

@pytest.mark.asyncio
async def test_change_password(client: AsyncClient):
    """独立注册用户测试密码修改"""
    phone = "13800000050"
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "register"})
    reg_resp = await client.post("/api/v1/auth/register", json={
        "phone": phone, "code": "123456", "password": "OldPwd12", "nickname": "改密码",
    })
    token = reg_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.put("/api/v1/users/me/password", headers=headers, json={
        "old_password": "OldPwd12",
        "new_password": "NewPwd12",
    })
    assert resp.status_code == 200

    # 用新密码登录
    login_resp = await client.post("/api/v1/auth/login/password", json={
        "phone": phone, "password": "NewPwd12",
    })
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old(client: AsyncClient, auth_headers: dict):
    resp = await client.put("/api/v1/users/me/password", headers=auth_headers, json={
        "old_password": "WrongOld",
        "new_password": "NewOne12",
    })
    assert resp.status_code == 400
    assert resp.json()["code"] == 40109  # PASSWORD_WRONG


# ============================================================
# GET/PATCH /users/me/settings
# ============================================================

@pytest.mark.asyncio
async def test_get_settings(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/users/me/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["notification_enabled"] is True
    assert data["privacy_show_agents"] is True


@pytest.mark.asyncio
async def test_update_settings(client: AsyncClient, auth_headers: dict):
    resp = await client.patch("/api/v1/users/me/settings", headers=auth_headers, json={
        "notification_enabled": False,
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["notification_enabled"] is False


# ============================================================
# GET /users/{user_id}
# ============================================================

@pytest.mark.asyncio
async def test_get_other_user(client: AsyncClient, auth_headers: dict):
    # 获取当前用户 ID
    me_resp = await client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/users/{user_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == user_id


@pytest.mark.asyncio
async def test_get_nonexistent_user(client: AsyncClient, auth_headers: dict):
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/api/v1/users/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


# ============================================================
# POST/DELETE /users/{user_id}/block
# ============================================================

@pytest.mark.asyncio
async def test_block_and_unblock_user(client: AsyncClient, auth_headers: dict, second_auth_headers: dict):
    # 获取第二个用户的 ID
    me2_resp = await client.get("/api/v1/users/me", headers=second_auth_headers)
    target_id = me2_resp.json()["data"]["id"]

    # 屏蔽
    resp = await client.post(f"/api/v1/users/{target_id}/block", headers=auth_headers)
    assert resp.status_code == 200

    # 重复屏蔽 → 仍成功 (幂等)
    resp = await client.post(f"/api/v1/users/{target_id}/block", headers=auth_headers)
    assert resp.status_code == 200

    # 取消屏蔽
    resp = await client.delete(f"/api/v1/users/{target_id}/block", headers=auth_headers)
    assert resp.status_code == 200


# ============================================================
# DELETE /users/me (注销)
# ============================================================

@pytest.mark.asyncio
async def test_delete_account(client: AsyncClient):
    """注册后注销"""
    phone = "13800000060"
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "register"})
    reg_resp = await client.post("/api/v1/auth/register", json={
        "phone": phone, "code": "123456", "password": "Delete12", "nickname": "即将注销",
    })
    token = reg_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.request("DELETE", "/api/v1/users/me", headers=headers, json={
        "code": "123456", "reason": "测试注销",
    })
    assert resp.status_code == 200

    # 注销后无法登录
    login_resp = await client.post("/api/v1/auth/login/password", json={
        "phone": phone, "password": "Delete12",
    })
    assert login_resp.status_code == 401
