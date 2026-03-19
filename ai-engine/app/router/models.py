"""
AetherVerse AI Engine — 模型管理 API 路由
GET /models/health  |  POST /models/route
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import verify_internal_key
from ..schemas import ModelHealthResponse, ModelRouteRequest, ModelRouteResponse, ProviderHealth

router = APIRouter(dependencies=[Depends(verify_internal_key)])

# ModelRouter 引用（从 chat 模块共享）
_model_router = None


def set_model_router(mr) -> None:
    global _model_router
    _model_router = mr


def _get_model_router():
    if _model_router is None:
        from ..config import get_settings
        from ..model_router import ModelRouter
        return ModelRouter(get_settings())
    return _model_router


@router.get("/health", response_model=ModelHealthResponse)
async def models_health() -> ModelHealthResponse:
    """所有模型供应商的健康状态。"""
    mr = _get_model_router()
    health = await mr.check_health()
    providers = [
        ProviderHealth(name=name, status=info.get("status", "unknown"), latency_ms=info.get("latency_ms"))
        for name, info in health.items()
    ]
    return ModelHealthResponse(providers=providers)


@router.post("/route", response_model=ModelRouteResponse)
async def models_route(req: ModelRouteRequest) -> ModelRouteResponse:
    """调试用：给定场景，返回路由决策。"""
    mr = _get_model_router()
    chain = await mr.route(req.scene)

    configs = chain.all_configs()
    if req.fallback_level < len(configs):
        config = configs[req.fallback_level]
    elif configs:
        config = configs[-1]
    else:
        return ModelRouteResponse(
            provider="none", model="none", base_url="", timeout_ms=0, is_fallback=False
        )

    return ModelRouteResponse(
        provider=config.provider,
        model=config.model,
        base_url=config.base_url,
        timeout_ms=config.timeout_ms,
        is_fallback=config.is_fallback,
    )
