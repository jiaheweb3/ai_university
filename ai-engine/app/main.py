"""
AetherVerse AI Engine — FastAPI 应用入口
Agent B 领地

启动: cd ai-engine && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.exceptions import AppException

from .config import get_settings
from .deps import (
    check_rabbitmq_health,
    check_redis_health,
    close_rabbitmq,
    close_redis,
    init_rabbitmq,
    init_redis,
)
from .log import setup_logging
from .model_router import ModelRouter
from .router import aigc, chat, creation, memory, models, moderation, persona, safety

logger = structlog.get_logger(__name__)

# ── 全局状态 ─────────────────────────────────────────────
_start_time: float = 0.0
_model_router: ModelRouter | None = None
_mq_consumer = None


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期：startup / shutdown"""
    global _start_time, _model_router, _mq_consumer

    settings = get_settings()

    # ── Startup ──────────────────────────────────────────
    setup_logging(json_format=not settings.DEBUG, level="DEBUG" if settings.DEBUG else "INFO")
    _start_time = time.monotonic()

    await logger.ainfo("ai_engine_starting", version=settings.VERSION)

    # 连接 Redis
    try:
        redis = await init_redis(settings)
    except Exception as exc:
        await logger.aerror("redis_init_failed", error=str(exc))
        redis = None

    # 连接 RabbitMQ
    try:
        rmq_conn = await init_rabbitmq(settings)
    except Exception as exc:
        await logger.aerror("rabbitmq_init_failed", error=str(exc))
        rmq_conn = None

    # 初始化模型路由
    _model_router = ModelRouter(settings, redis=redis)
    chat.set_model_router(_model_router)
    models.set_model_router(_model_router)
    memory.set_model_router(_model_router)
    creation.set_model_router(_model_router)
    moderation.set_model_router(_model_router)

    # 启动 MQ 消费者
    if rmq_conn and redis:
        try:
            from .mq_consumer import MQConsumer
            _mq_consumer = MQConsumer(rmq_conn, settings, _model_router, redis)
            await _mq_consumer.start()
        except Exception as exc:
            await logger.aerror("mq_consumer_start_failed", error=str(exc))

    await logger.ainfo(
        "ai_engine_started",
        providers_available=_model_router.available_provider_count,
        redis_connected=redis is not None,
        rabbitmq_connected=rmq_conn is not None,
    )

    yield

    # ── Shutdown ─────────────────────────────────────────
    if _mq_consumer:
        await _mq_consumer.stop()
    await close_rabbitmq()
    await close_redis()
    await logger.ainfo("ai_engine_stopped")


# ── FastAPI 应用 ─────────────────────────────────────────
app = FastAPI(
    title="AetherVerse AI Engine",
    version="0.1.0",
    docs_url="/internal/docs",
    lifespan=lifespan,
)


# ── 全局异常处理 ─────────────────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


# ── 路由注册 ─────────────────────────────────────────────
app.include_router(chat.router, prefix="/internal/v1/chat", tags=["Agent Chat"])
app.include_router(persona.router, prefix="/internal/v1/persona", tags=["Persona"])
app.include_router(models.router, prefix="/internal/v1/models", tags=["Models"])
app.include_router(memory.router, prefix="/internal/v1/memory", tags=["Memory"])
app.include_router(creation.router, prefix="/internal/v1/creation", tags=["Creation"])
app.include_router(moderation.router, prefix="/internal/v1/moderation", tags=["Moderation"])
app.include_router(safety.router, prefix="/internal/v1/safety", tags=["Safety"])
app.include_router(aigc.router, prefix="/internal/v1/aigc", tags=["AIGC"])


# ── 健康探针 ─────────────────────────────────────────────

@app.get("/internal/v1/health", tags=["Health"])
async def health():
    """存活探针 (Liveness) — 不检查外部依赖，只证明进程活着"""
    settings = get_settings()
    uptime = int(time.monotonic() - _start_time) if _start_time else 0
    return {
        "status": "ok",
        "version": settings.VERSION,
        "uptime_seconds": uptime,
    }


@app.get("/internal/v1/ready", tags=["Health"])
async def ready():
    """
    就绪探针 (Readiness) — 真实检查 Redis / RabbitMQ / 模型可用性。
    全部依赖就绪 → "ready"; 部分缺失 → "degraded"
    """
    redis_ok = await check_redis_health()
    rabbitmq_ok = await check_rabbitmq_health()
    models_available = _model_router.available_provider_count if _model_router else 0

    all_ok = redis_ok and rabbitmq_ok and models_available > 0
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": {
            "redis": redis_ok,
            "rabbitmq": rabbitmq_ok,
            "models_available": models_available,
        },
    }
