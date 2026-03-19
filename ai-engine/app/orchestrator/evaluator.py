"""
AetherVerse AI Engine — 监听评估
判断智能体是否应该在当前对话中回复
"""

from __future__ import annotations

import json

import structlog

from shared.constants import AIScene
from shared.schemas import AgentContext, RoomContext

from ..model_router import ModelRouter
from ..persona.prompt_builder import build_evaluate_prompt
from ..schemas import EvaluateResponse

logger = structlog.get_logger(__name__)


async def evaluate_should_reply(
    agent: AgentContext,
    room: RoomContext,
    trigger_type: str,
    model_router: ModelRouter,
) -> EvaluateResponse:
    """
    评估智能体是否应回复。

    - trigger_type == "mention": 直接返回 should_reply=True
    - trigger_type == "periodic": 调用 LLM 判断
    """

    # ── @提及 → 直接回复 ─────────────────────────────────
    if trigger_type == "mention":
        return EvaluateResponse(
            should_reply=True,
            confidence=1.0,
            reason="被@提及，直接回复",
            model="rule",
            tokens_used=0,
        )

    # ── 定期评估 → LLM 判断 ──────────────────────────────
    persona_summary = ""
    if agent.persona_config:
        persona_summary = agent.persona_config.personality or ""

    recent = [
        {
            "sender_name": msg.sender_name,
            "sender_type": msg.sender_type,
            "content": msg.content,
        }
        for msg in room.recent_messages[-20:]
    ]

    user_prompt = build_evaluate_prompt(
        agent_name=agent.name or "智能体",
        persona_summary=persona_summary,
        recent_messages=recent,
    )

    try:
        result = await model_router.call_model(
            scene=AIScene.LISTEN_EVAL,
            messages=[
                {"role": "system", "content": "你是一个聊天评估系统，只输出 JSON。"},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=100,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        # 解析 JSON 响应
        parsed = _parse_evaluate_json(result.content)

        return EvaluateResponse(
            should_reply=parsed.get("should_reply", False),
            confidence=min(1.0, max(0.0, float(parsed.get("confidence", 0.5)))),
            reason=parsed.get("reason", ""),
            model=result.model,
            tokens_used=result.input_tokens + result.output_tokens,
        )

    except Exception as exc:
        await logger.awarning("evaluate_failed", agent_id=str(agent.agent_id), error=str(exc))
        # 评估失败时保守处理：不回复
        return EvaluateResponse(
            should_reply=False,
            confidence=0.0,
            reason=f"评估异常: {exc}",
        )


def _parse_evaluate_json(content: str) -> dict:
    """
    从 LLM 输出中解析 JSON。
    兼容 ```json ... ``` 包裹和纯 JSON。
    """
    content = content.strip()

    # 去掉 markdown 代码块包裹
    if content.startswith("```"):
        lines = content.split("\n")
        # 去掉首行 ```json 和末行 ```
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 最后尝试提取花括号内容
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass
        return {"should_reply": False, "confidence": 0.0, "reason": "JSON 解析失败"}
