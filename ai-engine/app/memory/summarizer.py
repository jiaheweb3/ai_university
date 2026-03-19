"""
AetherVerse AI Engine — 记忆摘要
将多条对话记忆压缩为 ≤500 tokens 摘要，保持人格一致性
"""

from __future__ import annotations

import structlog

from shared.constants import AIScene

from ..model_router import ModelRouter
from ..persona.prompt_builder import get_jinja_env, estimate_tokens

logger = structlog.get_logger(__name__)


async def summarize_memories(
    agent_id: str,
    persona_config: dict | None,
    memories: list[dict],
    model_router: ModelRouter,
    *,
    max_tokens: int = 500,
) -> tuple[str, int, str]:
    """
    将记忆列表压缩为简短摘要。

    Args:
        agent_id: 智能体 ID
        persona_config: 人格配置 (personality, speaking_style)
        memories: 记忆列表 [{content, created_at}]
        model_router: 模型路由器
        max_tokens: 最大输出 token

    Returns:
        (summary, token_count, model_name)
    """
    if not memories:
        return "", 0, ""

    # 构建提示词
    env = get_jinja_env()
    template = env.get_template("memory_summarize.j2")

    agent_name = "智能体"
    persona_summary = ""
    if persona_config:
        agent_name = persona_config.get("name", "智能体")
        persona_summary = persona_config.get("personality", "")

    prompt = template.render(
        agent_name=agent_name,
        persona_summary=persona_summary,
        memories=memories,
    )

    try:
        result = await model_router.call_model(
            scene=AIScene.MEMORY_SUMMARY,
            messages=[
                {"role": "system", "content": "你是记忆管理系统，负责以智能体视角压缩对话记忆。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )

        summary = result.content.strip()
        token_count = estimate_tokens(summary)

        await logger.ainfo(
            "memory_summarized",
            agent_id=agent_id,
            memories_count=len(memories),
            summary_tokens=token_count,
            model=result.model,
        )

        return summary, token_count, result.model

    except Exception as exc:
        await logger.aerror("memory_summarize_failed", agent_id=agent_id, error=str(exc))
        # 降级: 截取最近 3 条拼接
        fallback = " | ".join(m.get("content", "")[:100] for m in memories[-3:])
        return fallback, estimate_tokens(fallback), "fallback"
