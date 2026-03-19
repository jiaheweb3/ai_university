"""
AetherVerse Server — Redis 异步连接池
"""

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import get_settings

_redis_pool: aioredis.Redis | None = None


async def init_redis() -> None:
    """应用启动时初始化 Redis 连接池"""
    global _redis_pool
    settings = get_settings()
    _redis_pool = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
    )


async def close_redis() -> None:
    """应用关闭时释放 Redis 连接"""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


def get_redis_pool() -> aioredis.Redis:
    """同步获取 Redis 实例 (非 generator, 用于 service 层)"""
    if _redis_pool is None:
        raise RuntimeError("Redis 未初始化，请先调用 init_redis()")
    return _redis_pool


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI 依赖注入: 获取 Redis 连接"""
    yield get_redis_pool()
