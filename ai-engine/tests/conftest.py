"""
AI Engine 测试 — 公共 Fixtures
Mock Redis / Mock LLM Client / Mock RabbitMQ
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from shared.schemas import AgentContext, PersonaConfig, RoomContext, RoomContextMessage


# ── Mock Redis ───────────────────────────────────────────

class MockRedis:
    """内存版 Redis mock — 支持 get/set/ping"""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        self._store.clear()


@pytest.fixture
def mock_redis():
    return MockRedis()


# ── Mock OpenAI Response ─────────────────────────────────

@dataclass
class MockUsage:
    prompt_tokens: int = 100
    completion_tokens: int = 50


@dataclass
class MockChoice:
    message: Any = None

    def __post_init__(self):
        if self.message is None:
            self.message = MagicMock(content="这是模拟的 AI 回复")


@dataclass
class MockChatCompletion:
    choices: list = None
    usage: MockUsage = None

    def __post_init__(self):
        if self.choices is None:
            self.choices = [MockChoice()]
        if self.usage is None:
            self.usage = MockUsage()


# ── Mock ModelRouter ─────────────────────────────────────

class MockModelRouter:
    """Mock 版 ModelRouter — 返回固定结果"""

    def __init__(self, response_content: str = "这是模拟的 AI 回复"):
        self.response_content = response_content
        self.available_provider_count = 1

    async def call_model(self, scene, messages, **kwargs):
        from shared.schemas import GenerationResult
        return GenerationResult(
            content=self.response_content,
            model="mock-model",
            provider="mock",
            input_tokens=100,
            output_tokens=50,
            latency_ms=200,
            cost_yuan=0.0001,
        )

    async def route(self, scene):
        from app.model_router import ModelConfig, RoutingChain
        return RoutingChain(
            primary=ModelConfig(
                provider="mock", model="mock-model", base_url="http://mock", api_key="test"
            )
        )

    async def check_health(self):
        return {"mock": {"status": "active", "latency_ms": 100}}


@pytest.fixture
def mock_model_router():
    return MockModelRouter()


# ── 通用上下文 Fixtures ──────────────────────────────────

@pytest.fixture
def sample_agent_context() -> AgentContext:
    return AgentContext(
        agent_id=uuid4(),
        owner_id=uuid4(),
        name="小星",
        level="L1",
        persona_config=PersonaConfig(
            personality="活泼好奇的科技迷",
            speaking_style="轻松活泼，喜欢用 emoji",
            expertise="AI 技术、编程趣事",
            constraints="不讨论政治敏感话题",
        ),
        memory_summary="上次和用户聊了 AI 绘画的话题，用户对 Stable Diffusion 很感兴趣。",
    )


@pytest.fixture
def sample_room_context() -> RoomContext:
    return RoomContext(
        room_id=uuid4(),
        room_name="AI 爱好者",
        room_description="讨论 AI 技术和应用",
        current_topic="AI 绘画",
        recent_messages=[
            RoomContextMessage(
                id=uuid4(),
                sender_name="小明",
                sender_type="user",
                content="你们觉得 AI 画画能替代画师吗？",
                created_at=datetime.now(),
            ),
            RoomContextMessage(
                id=uuid4(),
                sender_name="小红",
                sender_type="user",
                content="我觉得不行，AI 没有创作灵感",
                created_at=datetime.now(),
            ),
            RoomContextMessage(
                id=uuid4(),
                sender_name="知远",
                sender_type="agent",
                content="这个问题可以从技术和商业两个角度来看",
                created_at=datetime.now(),
            ),
        ],
    )
