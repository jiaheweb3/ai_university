"""
AetherVerse Server — FastAPI 应用入口
lifespan 管理 + 路由注册 + 全局异常处理
"""

import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.redis import close_redis, init_redis
from shared.exceptions import AppException

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期: 启动/关闭时初始化/释放资源"""
    settings = get_settings()
    logger.info("aetherverse_starting", debug=settings.DEBUG)

    await init_db()
    await init_redis()
    logger.info("infrastructure_ready")

    yield

    await close_redis()
    await close_db()
    logger.info("aetherverse_shutdown")


app = FastAPI(
    title="AetherVerse API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Phase 1 开发阶段允许所有, 上线前改为白名单
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- 全局异常处理 ----
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": 50001, "message": "服务器内部错误"},
    )


# ---- request_id 中间件 ----
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:16])
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    structlog.contextvars.unbind_contextvars("request_id")
    return response


# ---- 健康检查 ----
@app.get("/health")
async def health():
    return {"status": "ok", "service": "aetherverse-server"}


# ---- 路由注册 ----
from app.api.auth import router as auth_router  # noqa: E402
from app.api.rooms import router as rooms_router  # noqa: E402
from app.api.users import router as users_router  # noqa: E402

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(rooms_router, prefix="/api/v1/rooms", tags=["Rooms"])
