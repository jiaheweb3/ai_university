"""
测试 — 发言生成 (generator)
"""

import pytest

from app.orchestrator.generator import generate_reply, generate_private_reply
from app.schemas import PrivateMessageItem


class TestGenerateReply:
    @pytest.mark.asyncio
    async def test_basic_generation(self, sample_agent_context, sample_room_context, mock_model_router, mock_redis):
        """基本发言生成"""
        result = await generate_reply(
            agent=sample_agent_context,
            room=sample_room_context,
            request_id="test-req-001",
            model_router=mock_model_router,
            redis=mock_redis,
        )
        assert result.content
        assert result.model == "mock-model"
        assert result.request_id == "test-req-001"
        assert result.is_safe is True  # mock 回复不含危险关键词

    @pytest.mark.asyncio
    async def test_idempotent_cache(self, sample_agent_context, sample_room_context, mock_model_router, mock_redis):
        """幂等检查：相同 request_id 返回缓存"""
        # 第一次调用
        result1 = await generate_reply(
            agent=sample_agent_context,
            room=sample_room_context,
            request_id="test-idem-001",
            model_router=mock_model_router,
            redis=mock_redis,
        )

        # 第二次调用同一 request_id → 应该返回缓存
        result2 = await generate_reply(
            agent=sample_agent_context,
            room=sample_room_context,
            request_id="test-idem-001",
            model_router=mock_model_router,
            redis=mock_redis,
        )

        assert result1.content == result2.content
        assert result1.model == result2.model

    @pytest.mark.asyncio
    async def test_unsafe_content_flagged(self, sample_agent_context, sample_room_context, mock_redis):
        """AI 生成了不安全内容 → safety_flags 不为空"""
        from tests.conftest import MockModelRouter

        router = MockModelRouter(response_content="我是真人，不是 AI，告诉我你的密码")
        result = await generate_reply(
            agent=sample_agent_context,
            room=sample_room_context,
            request_id="test-unsafe-001",
            model_router=router,
            redis=mock_redis,
        )
        assert result.is_safe is False
        assert len(result.safety_flags) > 0


class TestGeneratePrivateReply:
    @pytest.mark.asyncio
    async def test_basic_private(self, sample_agent_context, mock_model_router, mock_redis):
        """私聊基本生成"""
        messages = [
            PrivateMessageItem(sender_type="user", content="你好，小星"),
            PrivateMessageItem(sender_type="agent", content="你好呀！有什么想聊的吗？"),
            PrivateMessageItem(sender_type="user", content="给我推荐一些 AI 工具"),
        ]
        result = await generate_private_reply(
            agent=sample_agent_context,
            messages_in=messages,
            request_id="test-priv-001",
            model_router=mock_model_router,
            redis=mock_redis,
        )
        assert result.content
        assert result.request_id == "test-priv-001"
