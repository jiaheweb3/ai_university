"""
AetherVerse AI Engine — AIGC 水印路由
POST /aigc/embed-watermark
"""

from __future__ import annotations

import httpx
import structlog
from fastapi import APIRouter, Depends

from ..aigc.watermark import embed_watermark
from ..deps import verify_internal_key
from ..schemas import WatermarkRequest, WatermarkResponse

logger = structlog.get_logger(__name__)

router = APIRouter(dependencies=[Depends(verify_internal_key)])


@router.post("/embed-watermark", response_model=WatermarkResponse)
async def aigc_embed_watermark(req: WatermarkRequest) -> WatermarkResponse:
    """
    为 AI 生成图片嵌入不可见数字水印。
    下载图片 → 嵌入 LSB 水印 → 返回标记。
    """
    try:
        # 下载图片
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(req.image_url)
            resp.raise_for_status()
            image_bytes = resp.content

        # 嵌入水印
        metadata = req.metadata.model_dump()
        watermarked = embed_watermark(image_bytes, metadata)

        # TODO: 实际生产中应上传到 MinIO/OSS 并返回 URL
        # 当前返回成功标记
        await logger.ainfo(
            "watermark_embedded",
            content_id=req.metadata.content_id,
            original_size=len(image_bytes),
            watermarked_size=len(watermarked),
        )

        return WatermarkResponse(
            watermarked_image_url=req.image_url,  # 暂时返回原 URL
            status="ok",
        )

    except Exception as exc:
        await logger.aerror("watermark_embed_failed", error=str(exc))
        return WatermarkResponse(
            watermarked_image_url=None,
            status=f"error: {exc}",
        )
