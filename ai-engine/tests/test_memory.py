"""
Tests — 记忆摘要模块
"""

import pytest

from app.memory.summarizer import summarize_memories


class MockModelRouterForMemory:
    available_provider_count = 1

    async def call_model(self, *, scene, messages, max_tokens=500, temperature=0.3, **kw):
        class FakeResult:
            content = "我记得和用户聊过关于AI的话题。用户对技术很感兴趣，尤其是深度学习。"
            model = "mock-model"
            cost_yuan = 0.001
        return FakeResult()


class TestSummarizeMemories:
    @pytest.mark.asyncio
    async def test_basic_summarize(self):
        memories = [
            {"content": "用户问了我关于Python的问题", "created_at": "2026-03-19T10:00:00"},
            {"content": "我们讨论了FastAPI框架", "created_at": "2026-03-19T10:05:00"},
            {"content": "用户表示对异步编程很感兴趣", "created_at": "2026-03-19T10:10:00"},
        ]

        summary, token_count, model = await summarize_memories(
            agent_id="agent-001",
            persona_config={"name": "小星", "personality": "热情开朗"},
            memories=memories,
            model_router=MockModelRouterForMemory(),
        )

        assert len(summary) > 0
        assert token_count > 0
        assert model == "mock-model"

    @pytest.mark.asyncio
    async def test_empty_memories(self):
        summary, token_count, model = await summarize_memories(
            agent_id="agent-001",
            persona_config=None,
            memories=[],
            model_router=MockModelRouterForMemory(),
        )

        assert summary == ""
        assert token_count == 0
        assert model == ""

    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        class FailingRouter:
            available_provider_count = 0

            async def call_model(self, **kw):
                raise RuntimeError("no providers")

        memories = [
            {"content": "记忆内容1"},
            {"content": "记忆内容2"},
            {"content": "记忆内容3"},
            {"content": "记忆内容4"},
        ]

        summary, token_count, model = await summarize_memories(
            agent_id="agent-001",
            persona_config=None,
            memories=memories,
            model_router=FailingRouter(),
        )

        assert model == "fallback"
        assert "记忆内容" in summary
        # 降级截取最近 3 条
        assert "记忆内容2" in summary or "记忆内容3" in summary or "记忆内容4" in summary

    @pytest.mark.asyncio
    async def test_max_tokens_passed(self):
        class TokenTrackingRouter:
            available_provider_count = 1
            last_max_tokens = None

            async def call_model(self, *, scene, messages, max_tokens=500, **kw):
                TokenTrackingRouter.last_max_tokens = max_tokens
                class FakeResult:
                    content = "摘要"
                    model = "test"
                    cost_yuan = 0
                return FakeResult()

        memories = [{"content": "test"}]
        await summarize_memories(
            agent_id="agent-001",
            persona_config=None,
            memories=memories,
            model_router=TokenTrackingRouter(),
            max_tokens=300,
        )

        assert TokenTrackingRouter.last_max_tokens == 300
