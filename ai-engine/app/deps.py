"""
AetherVerse AI Engine — FastAPI 依赖注入
Redis (asyncio) / RabbitMQ (aio-pika) / 内部 API Key 校验
"""

from __future__ import annotations

from typing import AsyncGenerator
from urllib.parse import urlparse, urlunparse

import redis.asyncio as aioredis
import structlog
from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection
from fastapi import Depends, Header, HTTPException, status

from shared.exceptions import ErrorCode

from .config import Settings, get_settings

logger = structlog.get_logger(__name__)

# ── 全局连接池（lifespan 管理生命周期） ──────────────────
_redis_pool: aioredis.Redis | None = None
_rabbitmq_conn: AbstractRobustConnection | None = None


# ── Redis ────────────────────────────────────────────────
async def init_redis(settings: Settings) -> aioredis.Redis:
    global _redis_pool
    _redis_pool = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    await logger.ainfo("redis_connected", url=_mask_url(settings.REDIS_URL))
    return _redis_pool


async def close_redis() -> None:
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None
        await logger.ainfo("redis_closed")


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    if _redis_pool is None:
        raise HTTPException(status_code=503, detail="Redis not available")
    yield _redis_pool


# ── RabbitMQ ─────────────────────────────────────────────
async def init_rabbitmq(settings: Settings) -> AbstractRobustConnection:
    global _rabbitmq_conn
    _rabbitmq_conn = await connect_robust(settings.RABBITMQ_URL)
    await logger.ainfo("rabbitmq_connected", url=_mask_url(settings.RABBITMQ_URL))
    return _rabbitmq_conn


async def close_rabbitmq() -> None:
    global _rabbitmq_conn
    if _rabbitmq_conn:
        await _rabbitmq_conn.close()
        _rabbitmq_conn = None
        await logger.ainfo("rabbitmq_closed")


def get_rabbitmq_conn() -> AbstractRobustConnection:
    if _rabbitmq_conn is None:
        raise HTTPException(status_code=503, detail="RabbitMQ not available")
    return _rabbitmq_conn


# ── 内部 API Key 校验 ───────────────────────────────────
async def verify_internal_key(
    x_internal_key: str = Header(..., alias="X-Internal-Key"),
    settings: Settings = Depends(get_settings),
) -> str:
    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.TOKEN_INVALID, "message": "Invalid internal API key"},
        )
    return x_internal_key


# ── 健康检查辅助 ─────────────────────────────────────────
async def check_redis_health() -> bool:
    """PING Redis，成功返回 True"""
    if _redis_pool is None:
        return False
    try:
        return await _redis_pool.ping()
    except Exception:
        return False


async def check_rabbitmq_health() -> bool:
    """检查 RabbitMQ 连接是否存活"""
    if _rabbitmq_conn is None:
        return False
    try:
        return not _rabbitmq_conn.is_closed
    except Exception:
        return False


def _mask_url(url: str) -> str:
    """脱敏 URL 中的密码部分"""
    try:
        parsed = urlparse(url)
        if parsed.password:
            masked = parsed._replace(
                netloc=f"{parsed.username or ''}:***@{parsed.hostname}"
                + (f":{parsed.port}" if parsed.port else "")
            )
            return urlunparse(masked)
    except Exception:
        pass
    return url
