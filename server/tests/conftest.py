"""
AetherVerse Server — 测试公共 Fixture
使用 testcontainers 启动真实 PostgreSQL 容器
"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.core.config import Settings


# ---- PostgreSQL 容器 (session 级) ----

@pytest.fixture(scope="session")
def event_loop():
    """创建 session 级事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def pg_container():
    """启动 PostgreSQL 容器, 整个测试 session 共享"""
    with PostgresContainer(
        image="postgres:16-alpine",
        username="test",
        password="test",
        dbname="testdb",
    ) as pg:
        yield pg


@pytest.fixture(scope="session")
def database_url(pg_container) -> str:
    """构建 asyncpg 连接串"""
    host = pg_container.get_container_host_ip()
    port = pg_container.get_exposed_port(5432)
    return f"postgresql+asyncpg://test:test@{host}:{port}/testdb"


@pytest.fixture(scope="session")
def test_settings(database_url) -> Settings:
    """覆盖默认配置"""
    return Settings(
        DATABASE_URL=database_url,
        REDIS_URL="redis://localhost:6379/15",  # 测试用 DB 15
        JWT_SECRET="test-secret-key-for-testing",
        PHONE_AES_KEY="0123456789abcdef0123456789abcdef",
        SMS_MOCK=True,
        SMS_MOCK_CODE="123456",
        DEBUG=False,
    )


# ---- 数据库 Schema 初始化 ----

@pytest_asyncio.fixture(scope="session")
async def engine(database_url):
    """创建 async engine 并初始化所有表"""
    _engine = create_async_engine(database_url, echo=False)

    # 首先创建所有需要的 ENUM 类型 (PG 特有)
    async with _engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))

        # 创建所有 ENUM 类型
        enum_sqls = [
            "CREATE TYPE IF NOT EXISTS user_status AS ENUM ('active', 'banned_temp', 'banned_perm', 'deleted')",
            "CREATE TYPE IF NOT EXISTS message_type AS ENUM ('text', 'image', 'system', 'ai_generated')",
            "CREATE TYPE IF NOT EXISTS sender_type AS ENUM ('user', 'agent', 'system')",
            "CREATE TYPE IF NOT EXISTS moderation_status AS ENUM ('pending', 'approved', 'rejected', 'appealed', 'appeal_approved', 'appeal_rejected')",
            "CREATE TYPE IF NOT EXISTS moderation_trigger AS ENUM ('auto_block', 'auto_suspect', 'manual_report', 'appeal')",
            "CREATE TYPE IF NOT EXISTS agent_level AS ENUM ('L1', 'L2')",
            "CREATE TYPE IF NOT EXISTS agent_status AS ENUM ('active', 'paused', 'suspended', 'deleted')",
            "CREATE TYPE IF NOT EXISTS agent_owner_type AS ENUM ('user', 'system')",
            "CREATE TYPE IF NOT EXISTS room_status AS ENUM ('active', 'archived')",
            "CREATE TYPE IF NOT EXISTS topic_status AS ENUM ('draft', 'active', 'ended', 'archived')",
            "CREATE TYPE IF NOT EXISTS artwork_status AS ENUM ('generating', 'pending_review', 'approved', 'rejected', 'failed')",
            "CREATE TYPE IF NOT EXISTS point_tx_type AS ENUM ('recharge', 'create_agent', 'agent_speak', 'image_generate', 'free_daily', 'refund', 'admin_adjust')",
            "CREATE TYPE IF NOT EXISTS point_tx_status AS ENUM ('frozen', 'confirmed', 'refunded', 'expired')",
            "CREATE TYPE IF NOT EXISTS order_status AS ENUM ('pending', 'paid', 'failed', 'refunded', 'reconciling')",
            "CREATE TYPE IF NOT EXISTS payment_channel AS ENUM ('wechat', 'alipay')",
            "CREATE TYPE IF NOT EXISTS notification_type AS ENUM ('moderation_result', 'agent_status', 'account_security', 'task_status', 'transaction')",
            "CREATE TYPE IF NOT EXISTS ban_type AS ENUM ('temp', 'perm')",
            "CREATE TYPE IF NOT EXISTS sensitive_level AS ENUM ('block', 'suspect', 'observe')",
            "CREATE TYPE IF NOT EXISTS risk_action AS ENUM ('warn', 'rate_limit', 'pause', 'ban')",
            "CREATE TYPE IF NOT EXISTS provider_status AS ENUM ('active', 'disabled', 'degraded')",
            "CREATE TYPE IF NOT EXISTS ai_scene AS ENUM ('chat', 'image_gen', 'moderation', 'listen_eval', 'memory_summary')",
            "CREATE TYPE IF NOT EXISTS admin_role AS ENUM ('super_admin', 'ops_admin', 'reviewer')",
            "CREATE TYPE IF NOT EXISTS conversation_type AS ENUM ('user_to_user', 'user_to_agent')",
        ]
        for sql in enum_sqls:
            # PG 14+ 不支持 IF NOT EXISTS for ENUM, 用 DO block
            type_name = sql.split("IF NOT EXISTS ")[1].split(" AS ")[0]
            await conn.execute(text(f"""
                DO $$ BEGIN
                    {sql.replace('IF NOT EXISTS ', '')};
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
            """))

    # 然后创建所有 ORM 表
    from app.models import Base
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield _engine

    await _engine.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    """每个测试独立事务, 测试后回滚"""
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ---- Redis Mock ----

class FakeRedis:
    """内存 Redis mock, 避免测试依赖 Redis 服务"""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def exists(self, key: str) -> bool:
        return key in self._store

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value

    async def set(self, key: str, value: str) -> None:
        self._store[key] = value

    async def incr(self, key: str) -> int:
        val = int(self._store.get(key, "0")) + 1
        self._store[key] = str(val)
        return val

    async def decr(self, key: str) -> int:
        val = int(self._store.get(key, "0")) - 1
        self._store[key] = str(val)
        return val

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


@pytest.fixture
def fake_redis():
    return FakeRedis()


# ---- FastAPI TestClient ----

@pytest_asyncio.fixture
async def client(engine, test_settings, fake_redis) -> AsyncGenerator[AsyncClient, None]:
    """构建 httpx AsyncClient, 覆盖依赖注入"""
    from unittest.mock import patch

    from app.core.database import get_db
    from app.core.redis import get_redis, get_redis_pool
    from app.main import app

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    async def override_get_redis():
        yield fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    with patch("app.core.config.get_settings", return_value=test_settings), \
         patch("app.core.redis.get_redis_pool", return_value=fake_redis), \
         patch("app.core.deps.get_redis_pool", return_value=fake_redis):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()


# ---- 认证 Fixture ----

@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """注册一个测试用户并返回其 auth headers"""
    # 先发验证码
    await client.post("/api/v1/auth/sms/send", json={"phone": "13800138001", "purpose": "register"})
    # 注册
    resp = await client.post("/api/v1/auth/register", json={
        "phone": "13800138001",
        "code": "123456",
        "password": "Test1234!",
        "nickname": "测试用户",
    })
    data = resp.json()
    token = data["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_auth_headers(client: AsyncClient) -> dict:
    """注册第二个测试用户"""
    await client.post("/api/v1/auth/sms/send", json={"phone": "13900139001", "purpose": "register"})
    resp = await client.post("/api/v1/auth/register", json={
        "phone": "13900139001",
        "code": "123456",
        "password": "Test1234!",
        "nickname": "测试用户二",
    })
    data = resp.json()
    token = data["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
