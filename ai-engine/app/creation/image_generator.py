"""
AetherVerse AI Engine — 图片生成
异步创作流程：接受任务 → Redis 追踪状态 → 调用图片模型 → 回调结果
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime

import redis.asyncio as aioredis
import structlog

from shared.constants import AIScene

from ..model_router import ModelRouter
from ..persona.prompt_builder import get_jinja_env

logger = structlog.get_logger(__name__)

# 任务状态常量
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

# Redis key 前缀
TASK_KEY_PREFIX = "creation:task:"


async def start_image_generation(
    agent: dict,
    topic: dict,
    request_id: str,
    redis: aioredis.Redis,
    model_router: ModelRouter,
    *,
    image_size: str = "1024x1024",
) -> tuple[str, int]:
    """
    启动图片生成任务。

    返回 (task_id, estimated_seconds)。
    实际生成在后台协程中执行。
    """
    task_id = f"img-{uuid.uuid4().hex[:12]}"

    # 保存任务初始状态到 Redis
    task_data = {
        "task_id": task_id,
        "request_id": request_id,
        "status": STATUS_PENDING,
        "created_at": datetime.now().isoformat(),
        "agent_name": agent.get("name", ""),
        "topic_title": topic.get("title", ""),
        "image_size": image_size,
        "image_url": None,
        "thumbnail_url": None,
        "creative_process": None,
        "model": None,
        "cost_yuan": None,
        "error_message": None,
    }
    await redis.set(f"{TASK_KEY_PREFIX}{task_id}", json.dumps(task_data, ensure_ascii=False), ex=7200)

    # 后台执行生成
    asyncio.create_task(_generate_image_async(task_id, agent, topic, image_size, redis, model_router))

    return task_id, 30  # 预估 30 秒


async def get_task_status(task_id: str, redis: aioredis.Redis) -> dict | None:
    """查询任务状态"""
    raw = await redis.get(f"{TASK_KEY_PREFIX}{task_id}")
    if raw is None:
        return None
    return json.loads(raw)


async def _generate_image_async(
    task_id: str,
    agent: dict,
    topic: dict,
    image_size: str,
    redis: aioredis.Redis,
    model_router: ModelRouter,
) -> None:
    """后台异步生成图片"""

    try:
        # 更新状态 → processing
        await _update_task_status(task_id, redis, status=STATUS_PROCESSING)

        # Step 1: 将创作主题转化为英文 prompt
        prompt = await _translate_to_art_prompt(agent, topic, model_router)

        # Step 2: 调用图片模型
        # 当前 mock 模式 — 无 API Key 时返回占位图
        if model_router.available_provider_count == 0:
            # Mock 返回
            await asyncio.sleep(2)  # 模拟延迟
            image_url = f"https://placehold.co/{image_size}/png?text=AI+Art"
            model_name = "mock"
            cost = 0.0
        else:
            # 实际调用 CogView 等
            result = await model_router.call_model(
                scene=AIScene.IMAGE_GEN,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1,  # 图片模型不需要 text output
            )
            image_url = result.content  # CogView 返回的 URL
            model_name = result.model
            cost = result.cost_yuan

        # 更新状态 → completed
        creative_process = {
            "original_topic": topic.get("title", ""),
            "translated_prompt": prompt,
            "image_size": image_size,
            "generated_at": datetime.now().isoformat(),
        }

        await _update_task_status(
            task_id,
            redis,
            status=STATUS_COMPLETED,
            image_url=image_url,
            thumbnail_url=image_url,  # 缩略图暂时同 URL
            creative_process=json.dumps(creative_process, ensure_ascii=False),
            model=model_name,
            cost_yuan=cost,
        )

        await logger.ainfo("image_generation_completed", task_id=task_id, model=model_name)

    except Exception as exc:
        await logger.aerror("image_generation_failed", task_id=task_id, error=str(exc))
        await _update_task_status(
            task_id,
            redis,
            status=STATUS_FAILED,
            error_message=str(exc),
        )


async def _translate_to_art_prompt(agent: dict, topic: dict, model_router: ModelRouter) -> str:
    """将中文创作主题转化为英文 AI 绘画 prompt"""
    env = get_jinja_env()
    template = env.get_template("image_gen_prompt.j2")

    agent_style = ""
    persona = agent.get("persona_config")
    if persona and isinstance(persona, dict):
        agent_style = persona.get("speaking_style", "")

    user_prompt = template.render(topic=topic, agent_style=agent_style)

    try:
        result = await model_router.call_model(
            scene=AIScene.CHAT,
            messages=[
                {"role": "system", "content": "你是专业的 AI 绘画 prompt 工程师。只输出英文 prompt。"},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=200,
            temperature=0.8,
        )
        return result.content.strip()
    except Exception:
        # 降级: 直接拼接关键词
        title = topic.get("title", "art")
        keywords = topic.get("keywords", [])
        return f"{title}, {', '.join(keywords)}, high quality, detailed, digital art"


async def _update_task_status(task_id: str, redis: aioredis.Redis, **updates) -> None:
    """更新 Redis 中的任务状态"""
    raw = await redis.get(f"{TASK_KEY_PREFIX}{task_id}")
    if raw is None:
        return
    data = json.loads(raw)
    data.update(updates)
    await redis.set(f"{TASK_KEY_PREFIX}{task_id}", json.dumps(data, ensure_ascii=False), ex=7200)
