"""
AetherVerse AI Engine — 聊天 API 路由
POST /chat/evaluate  |  POST /chat/generate  |  POST /chat/generate-private
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends

from shared.schemas import AgentContext, RoomContext

from ..deps import get_redis, verify_internal_key
from ..model_router import ModelRouter
from ..orchestrator.evaluator import evaluate_should_reply
from ..orchestrator.generator import generate_private_reply, generate_reply
from ..schemas import (
    EvaluateRequest,
    EvaluateResponse,
    GenerateRequest,
    GenerateResponse,
    PrivateGenerateRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter(dependencies=[Depends(verify_internal_key)])

# ModelRouter 单例（lifespan 中初始化注入）
_model_router: ModelRouter | None = None


def set_model_router(mr: ModelRouter) -> None:
    global _model_router
    _model_router = mr


def _get_model_router() -> ModelRouter:
    if _model_router is None:
        # 延迟构建
        from ..config import get_settings
        return ModelRouter(get_settings())
    return _model_router


@router.post("/evaluate", response_model=EvaluateResponse)
async def chat_evaluate(
    req: EvaluateRequest,
    redis=Depends(get_redis),
) -> EvaluateResponse:
    """评估智能体是否应回复（监听模式）。平台成本，不消耗用户积分。"""
    model_router = _get_model_router()
    return await evaluate_should_reply(
        agent=req.agent,
        room=req.room,
        trigger_type=req.trigger_type,
        model_router=model_router,
    )


@router.post("/generate", response_model=GenerateResponse)
async def chat_generate(
    req: GenerateRequest,
    redis=Depends(get_redis),
) -> GenerateResponse:
    """生成智能体回复。消耗用户积分 (2-3 积分/次)。"""
    model_router = _get_model_router()
    return await generate_reply(
        agent=req.agent,
        room=req.room,
        request_id=req.request_id,
        model_router=model_router,
        redis=redis,
        max_tokens=req.max_tokens,
    )


@router.post("/generate-private", response_model=GenerateResponse)
async def chat_generate_private(
    req: PrivateGenerateRequest,
    redis=Depends(get_redis),
) -> GenerateResponse:
    """生成智能体私聊回复。"""
    model_router = _get_model_router()
    return await generate_private_reply(
        agent=req.agent,
        messages_in=req.messages,
        request_id=req.request_id,
        model_router=model_router,
        redis=redis,
    )
