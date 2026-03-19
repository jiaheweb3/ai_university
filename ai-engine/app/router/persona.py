"""
AetherVerse AI Engine — 人格 API 路由
POST /persona/build-prompt
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import verify_internal_key
from ..persona.prompt_builder import build_system_prompt
from ..schemas import BuildPromptRequest, BuildPromptResponse

router = APIRouter(dependencies=[Depends(verify_internal_key)])


@router.post("/build-prompt", response_model=BuildPromptResponse)
async def persona_build_prompt(req: BuildPromptRequest) -> BuildPromptResponse:
    """根据人格配置 + 记忆摘要 + 场景，构建完整系统提示词。"""
    prompt, token_count = build_system_prompt(
        persona_config=req.persona_config,
        memory_summary=req.memory_summary,
        scene=req.scene,
    )
    return BuildPromptResponse(system_prompt=prompt, token_count=token_count)
