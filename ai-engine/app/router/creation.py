"""
AetherVerse AI Engine — 创作路由
POST /creation/generate-image  |  GET /creation/status/{task_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..creation.image_generator import get_task_status, start_image_generation
from ..deps import get_redis, verify_internal_key
from ..schemas import ImageGenAccepted, ImageGenRequest, ImageTaskStatus

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


@router.post("/generate-image", response_model=ImageGenAccepted, status_code=202)
async def creation_generate_image(
    req: ImageGenRequest,
    redis=Depends(get_redis),
) -> ImageGenAccepted:
    """启动图片生成任务。异步执行，返回 task_id。消耗用户积分 (20-30)。"""
    mr = _get_model_router()
    agent_dict = req.agent.model_dump(mode="json")
    topic_dict = req.topic.model_dump()

    task_id, estimated = await start_image_generation(
        agent=agent_dict,
        topic=topic_dict,
        request_id=req.request_id,
        redis=redis,
        model_router=mr,
        image_size=req.image_size,
    )

    return ImageGenAccepted(task_id=task_id, estimated_seconds=estimated)


@router.get("/status/{task_id}", response_model=ImageTaskStatus)
async def creation_status(
    task_id: str,
    redis=Depends(get_redis),
) -> ImageTaskStatus:
    """查询图片生成任务状态。"""
    status = await get_task_status(task_id, redis)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return ImageTaskStatus(**status)
