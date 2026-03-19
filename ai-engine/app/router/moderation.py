"""
AetherVerse AI Engine — 审核路由
POST /moderation/check-text  |  /check-image  |  /check-persona
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import verify_internal_key
from ..moderation.moderator import check_image, check_persona, check_text
from ..schemas import (
    ImageModerationRequest,
    ModerationResult,
    PersonaModerationRequest,
    TextModerationRequest,
)

router = APIRouter(dependencies=[Depends(verify_internal_key)])

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


@router.post("/check-text", response_model=ModerationResult)
async def moderation_check_text(req: TextModerationRequest) -> ModerationResult:
    """AI 文本审核。同步调用。平台成本。"""
    mr = _get_model_router()
    result = await check_text(
        text=req.text,
        model_router=mr,
        context=req.context,
        sender_type=req.sender_type,
    )
    return ModerationResult(**result)


@router.post("/check-image", response_model=ModerationResult)
async def moderation_check_image(req: ImageModerationRequest) -> ModerationResult:
    """AI 图片审核。当前 Mock。"""
    mr = _get_model_router()
    result = await check_image(image_url=req.image_url, model_router=mr)
    return ModerationResult(**result)


@router.post("/check-persona", response_model=ModerationResult)
async def moderation_check_persona(req: PersonaModerationRequest) -> ModerationResult:
    """智能体人格审核。"""
    mr = _get_model_router()
    result = await check_persona(
        persona_config=req.persona_config,
        agent_name=req.agent_name,
        model_router=mr,
    )
    return ModerationResult(**result)
