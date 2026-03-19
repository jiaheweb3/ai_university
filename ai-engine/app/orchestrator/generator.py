"""
AetherVerse AI Engine — 发言生成
支持房间聊天和私聊场景，含幂等缓存 + AI 自检
"""

from __future__ import annotations

import json

import redis.asyncio as aioredis
import structlog

from shared.constants import AIScene
from shared.schemas import AgentContext, RoomContext

from ..config import get_settings
from ..model_router import ModelRouter
from ..persona.prompt_builder import build_system_prompt
from ..safety.quick_check import quick_check
from ..schemas import GenerateResponse, PrivateMessageItem

logger = structlog.get_logger(__name__)

# 安全过滤时的替代内容
_SAFETY_FILTERED_CONTENT = "[该内容已被安全系统过滤]"


async def generate_reply(
    agent: AgentContext,
    room: RoomContext,
    request_id: str,
    model_router: ModelRouter,
    redis: aioredis.Redis,
    *,
    max_tokens: int = 300,
) -> GenerateResponse:
    """
    生成智能体在房间中的回复。

    流程:
    1. 幂等检查（Redis 缓存）
    2. 构建 system prompt
    3. 组装消息列表
    4. 调用 LLM
    5. AI 自检 (冒充/社工)
    6. 缓存结果
    """

    # ── 1. 幂等检查 ──────────────────────────────────────
    cached = await _check_idempotent(redis, request_id)
    if cached:
        await logger.ainfo("idempotent_hit", request_id=request_id)
        return cached

    # ── 2. 构建 system prompt ────────────────────────────
    system_prompt = agent.system_prompt
    if not system_prompt and agent.persona_config:
        persona_dict = agent.persona_config.model_dump() if agent.persona_config else {}
        system_prompt, _ = build_system_prompt(
            persona_config=persona_dict,
            memory_summary=agent.memory_summary,
            scene="room_chat",
        )

    # ── 3. 组装消息列表 ──────────────────────────────────
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # 加入最近的房间消息作为对话上下文
    for msg in room.recent_messages[-15:]:
        role = "assistant" if msg.sender_type == "agent" and msg.sender_name == agent.name else "user"
        messages.append({
            "role": role,
            "content": f"[{msg.sender_name}]: {msg.content}",
        })

    # 最后一条消息确保是 user 角色（模型期望 user → assistant 交替）
    if messages and messages[-1]["role"] == "assistant":
        messages.append({"role": "user", "content": "[系统]: 请继续参与对话"})

    # ── 4. 调用 LLM ──────────────────────────────────────
    result = await model_router.call_model(
        scene=AIScene.CHAT,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )

    # ── 5. AI 自检 ───────────────────────────────────────
    safety_result = quick_check(result.content)

    # BUG-2 fix: 不安全内容必须在引擎侧过滤，不能依赖后端二次校验
    final_content = result.content if safety_result.is_safe else _SAFETY_FILTERED_CONTENT
    if not safety_result.is_safe:
        await logger.awarning(
            "unsafe_content_filtered",
            request_id=request_id,
            flags=safety_result.flags,
        )

    response = GenerateResponse(
        content=final_content,
        model=result.model,
        provider=result.provider,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        cost_yuan=result.cost_yuan,
        request_id=request_id,
        is_safe=safety_result.is_safe,
        safety_flags=safety_result.flags,
    )

    # ── 6. 缓存幂等结果 ──────────────────────────────────
    await _set_idempotent(redis, request_id, response)

    return response


async def generate_private_reply(
    agent: AgentContext,
    messages_in: list[PrivateMessageItem],
    request_id: str,
    model_router: ModelRouter,
    redis: aioredis.Redis,
) -> GenerateResponse:
    """
    私聊场景的发言生成。
    """

    # ── 幂等检查 ─────────────────────────────────────────
    cached = await _check_idempotent(redis, request_id)
    if cached:
        return cached

    # ── 构建 system prompt ───────────────────────────────
    system_prompt = agent.system_prompt
    if not system_prompt and agent.persona_config:
        persona_dict = agent.persona_config.model_dump() if agent.persona_config else {}
        system_prompt, _ = build_system_prompt(
            persona_config=persona_dict,
            memory_summary=agent.memory_summary,
            scene="private_chat",
        )

    # ── 组装消息列表 ─────────────────────────────────────
    llm_messages: list[dict[str, str]] = []
    if system_prompt:
        llm_messages.append({"role": "system", "content": system_prompt})

    for msg in messages_in[-15:]:
        role = "assistant" if msg.sender_type == "agent" else "user"
        llm_messages.append({"role": role, "content": msg.content})

    # 确保最后是 user
    if llm_messages and llm_messages[-1]["role"] == "assistant":
        llm_messages.append({"role": "user", "content": "请继续"})

    # ── 调用 LLM ─────────────────────────────────────────
    result = await model_router.call_model(
        scene=AIScene.CHAT,
        messages=llm_messages,
        max_tokens=300,
        temperature=0.7,
    )

    safety_result = quick_check(result.content)

    # BUG-2 fix: 不安全内容替换为安全提示
    final_content = result.content if safety_result.is_safe else _SAFETY_FILTERED_CONTENT
    if not safety_result.is_safe:
        await logger.awarning(
            "unsafe_content_filtered_private",
            request_id=request_id,
            flags=safety_result.flags,
        )

    response = GenerateResponse(
        content=final_content,
        model=result.model,
        provider=result.provider,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        cost_yuan=result.cost_yuan,
        request_id=request_id,
        is_safe=safety_result.is_safe,
        safety_flags=safety_result.flags,
    )

    await _set_idempotent(redis, request_id, response)
    return response


# ── 幂等辅助 ─────────────────────────────────────────────

async def _check_idempotent(redis: aioredis.Redis, request_id: str) -> GenerateResponse | None:
    """从 Redis 查找幂等缓存"""
    try:
        raw = await redis.get(f"idempotent:{request_id}")
        if raw:
            return GenerateResponse.model_validate_json(raw)
    except Exception as exc:
        await logger.awarning("idempotent_check_failed", error=str(exc))
    return None


async def _set_idempotent(redis: aioredis.Redis, request_id: str, response: GenerateResponse) -> None:
    """设置幂等缓存"""
    settings = get_settings()
    try:
        await redis.set(
            f"idempotent:{request_id}",
            response.model_dump_json(),
            ex=settings.IDEMPOTENT_TTL_SEC,
        )
    except Exception as exc:
        await logger.awarning("idempotent_set_failed", error=str(exc))
