"""
AetherVerse AI Engine — 安全检测路由
POST /safety/check-impersonation  |  /check-social-engineering
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import verify_internal_key
from ..safety.quick_check import check_impersonation, check_social_engineering
from ..schemas import (
    ImpersonationCheckRequest,
    ImpersonationCheckResponse,
    SocialEngineeringCheckRequest,
    SocialEngineeringCheckResponse,
)

router = APIRouter(dependencies=[Depends(verify_internal_key)])


@router.post("/check-impersonation", response_model=ImpersonationCheckResponse)
async def safety_check_impersonation(req: ImpersonationCheckRequest) -> ImpersonationCheckResponse:
    """检测智能体输出是否包含冒充真人的表述。"""
    is_imp, patterns = check_impersonation(req.text)
    return ImpersonationCheckResponse(is_impersonation=is_imp, matched_patterns=patterns)


@router.post("/check-social-engineering", response_model=SocialEngineeringCheckResponse)
async def safety_check_social_engineering(req: SocialEngineeringCheckRequest) -> SocialEngineeringCheckResponse:
    """检测智能体是否诱导用户泄露敏感信息。"""
    is_se, indicators = check_social_engineering(req.text, req.conversation_history)
    return SocialEngineeringCheckResponse(is_social_engineering=is_se, risk_indicators=indicators)
