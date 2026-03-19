"""
AetherVerse AI Engine — 记忆系统路由
POST /memory/summarize
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import verify_internal_key
from ..memory.summarizer import summarize_memories
from ..schemas import MemorySummarizeRequest, MemorySummarizeResponse

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


@router.post("/summarize", response_model=MemorySummarizeResponse)
async def memory_summarize(req: MemorySummarizeRequest) -> MemorySummarizeResponse:
    """生成记忆摘要。每 N 轮对话后由 server 调用。平台成本。"""
    mr = _get_model_router()
    memories_dicts = [m.model_dump() for m in req.memories]

    summary, token_count, model = await summarize_memories(
        agent_id=req.agent_id,
        persona_config=req.persona_config,
        memories=memories_dicts,
        model_router=mr,
        max_tokens=req.max_tokens,
    )

    return MemorySummarizeResponse(summary=summary, token_count=token_count, model=model)
