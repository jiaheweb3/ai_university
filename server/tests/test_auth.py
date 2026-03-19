"""
AetherVerse Server — Auth API 集成测试
"""

import pytest
from httpx import AsyncClient


# ============================================================
# SMS 发送
# ============================================================

@pytest.mark.asyncio
async def test_send_sms_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/sms/send", json={
        "phone": "13800138000",
        "purpose": "login",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_send_sms_invalid_phone(client: AsyncClient):
    resp = await client.post("/api/v1/auth/sms/send", json={
        "phone": "12345",
        "purpose": "login",
    })
    assert resp.status_code == 422  # pydantic validation


# ============================================================
# 注册
# ============================================================

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    # 先发验证码
    await client.post("/api/v1/auth/sms/send", json={"phone": "13800000001", "purpose": "register"})

    resp = await client.post("/api/v1/auth/register", json={
        "phone": "13800000001",
        "code": "123456",
        "password": "MyPass123",
        "nickname": "新用户",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == 0
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["nickname"] == "新用户"


@pytest.mark.asyncio
async def test_register_duplicate_phone(client: AsyncClient):
    """重复注册同一手机号应报错"""
    phone = "13800000002"
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "register"})
    await client.post("/api/v1/auth/register", json={
        "phone": phone, "code": "123456", "password": "MyPass123", "nickname": "用户A",
    })

    # 第二次注册
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "register"})
    resp = await client.post("/api/v1/auth/register", json={
        "phone": phone, "code": "123456", "password": "MyPass123", "nickname": "用户B",
    })
    assert resp.status_code == 409
    assert resp.json()["code"] == 40901  # PHONE_REGISTERED


@pytest.mark.asyncio
async def test_register_wrong_code(client: AsyncClient):
    await client.post("/api/v1/auth/sms/send", json={"phone": "13800000003", "purpose": "register"})
    resp = await client.post("/api/v1/auth/register", json={
        "phone": "13800000003", "code": "999999", "password": "MyPass123", "nickname": "用户C",
    })
    assert resp.status_code == 400
    assert resp.json()["code"] == 40104  # SMS_CODE_INVALID


# ============================================================
# 密码登录
# ============================================================

@pytest.mark.asyncio
async def test_login_password_success(client: AsyncClient):
    phone = "13800000010"
    # 注册
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "register"})
    await client.post("/api/v1/auth/register", json={
        "phone": phone, "code": "123456", "password": "Login1234", "nickname": "登录测试",
    })

    # 登录
    resp = await client.post("/api/v1/auth/login/password", json={
        "phone": phone, "password": "Login1234",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_login_password_wrong(client: AsyncClient):
    phone = "13800000011"
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "register"})
    await client.post("/api/v1/auth/register", json={
        "phone": phone, "code": "123456", "password": "Correct1", "nickname": "错误密码",
    })

    resp = await client.post("/api/v1/auth/login/password", json={
        "phone": phone, "password": "WrongPass",
    })
    assert resp.status_code == 401


# ============================================================
# 验证码登录
# ============================================================

@pytest.mark.asyncio
async def test_login_sms_success(client: AsyncClient):
    phone = "13800000020"
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "register"})
    await client.post("/api/v1/auth/register", json={
        "phone": phone, "code": "123456", "password": "SmsPwd12", "nickname": "短信登录",
    })

    # SMS 登录
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "login"})
    resp = await client.post("/api/v1/auth/login/sms", json={
        "phone": phone, "code": "123456",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"]


# ============================================================
# Token 刷新
# ============================================================

@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    phone = "13800000030"
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "register"})
    reg_resp = await client.post("/api/v1/auth/register", json={
        "phone": phone, "code": "123456", "password": "Refresh1", "nickname": "刷新测试",
    })
    refresh_token = reg_resp.json()["data"]["refresh_token"]

    resp = await client.post("/api/v1/auth/token/refresh", json={
        "refresh_token": refresh_token,
    })
    assert resp.status_code == 200
    new_data = resp.json()["data"]
    assert new_data["access_token"] != reg_resp.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client: AsyncClient):
    resp = await client.post("/api/v1/auth/token/refresh", json={
        "refresh_token": "invalid.token.here",
    })
    assert resp.status_code == 401


# ============================================================
# 密码重置
# ============================================================

@pytest.mark.asyncio
async def test_password_reset(client: AsyncClient):
    phone = "13800000040"
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "register"})
    await client.post("/api/v1/auth/register", json={
        "phone": phone, "code": "123456", "password": "OldPass12", "nickname": "重置密码",
    })

    # 重置
    await client.post("/api/v1/auth/sms/send", json={"phone": phone, "purpose": "reset_password"})
    resp = await client.post("/api/v1/auth/password/reset", json={
        "phone": phone, "code": "123456", "new_password": "NewPass12",
    })
    assert resp.status_code == 200

    # 用新密码登录
    resp = await client.post("/api/v1/auth/login/password", json={
        "phone": phone, "password": "NewPass12",
    })
    assert resp.status_code == 200


# ============================================================
# 退出登录
# ============================================================

@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_logout_without_token(client: AsyncClient):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 422  # missing Authorization header
