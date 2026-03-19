"""
测试 — 监听评估 (evaluator)
"""

import json
import pytest
from unittest.mock import MagicMock

from shared.schemas import GenerationResult

from app.orchestrator.evaluator import evaluate_should_reply, _parse_evaluate_json


class TestEvaluateShoudReply:
    @pytest.mark.asyncio
    async def test_mention_always_true(self, sample_agent_context, sample_room_context, mock_model_router):
        """@提及 → 直接返回 should_reply=True"""
        result = await evaluate_should_reply(
            agent=sample_agent_context,
            room=sample_room_context,
            trigger_type="mention",
            model_router=mock_model_router,
        )
        assert result.should_reply is True
        assert result.confidence == 1.0
        assert result.model == "rule"

    @pytest.mark.asyncio
    async def test_periodic_llm_reply_yes(self, sample_agent_context, sample_room_context):
        """periodic 触发 → LLM 返回 should_reply=true"""
        from tests.conftest import MockModelRouter

        # Mock LLM 返回 JSON
        router = MockModelRouter(
            response_content='{"should_reply": true, "confidence": 0.85, "reason": "话题相关"}'
        )
        result = await evaluate_should_reply(
            agent=sample_agent_context,
            room=sample_room_context,
            trigger_type="periodic",
            model_router=router,
        )
        assert result.should_reply is True
        assert result.confidence == 0.85
        assert "话题相关" in result.reason

    @pytest.mark.asyncio
    async def test_periodic_llm_reply_no(self, sample_agent_context, sample_room_context):
        """periodic 触发 → LLM 返回 should_reply=false"""
        from tests.conftest import MockModelRouter

        router = MockModelRouter(
            response_content='{"should_reply": false, "confidence": 0.3, "reason": "话题无关"}'
        )
        result = await evaluate_should_reply(
            agent=sample_agent_context,
            room=sample_room_context,
            trigger_type="periodic",
            model_router=router,
        )
        assert result.should_reply is False


class TestParseEvaluateJson:
    def test_clean_json(self):
        result = _parse_evaluate_json('{"should_reply": true, "confidence": 0.9, "reason": "test"}')
        assert result["should_reply"] is True
        assert result["confidence"] == 0.9

    def test_markdown_wrapped(self):
        result = _parse_evaluate_json('```json\n{"should_reply": false, "confidence": 0.1}\n```')
        assert result["should_reply"] is False

    def test_with_extra_text(self):
        result = _parse_evaluate_json('我认为 {"should_reply": true, "confidence": 0.7, "reason": "ok"} 就这样')
        assert result["should_reply"] is True

    def test_invalid_json(self):
        result = _parse_evaluate_json("这不是 JSON")
        assert result["should_reply"] is False
        assert "解析失败" in result["reason"]
