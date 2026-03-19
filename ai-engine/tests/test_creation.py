"""
Tests — 图片生成模块
"""

import asyncio
import json

import pytest

from app.creation.image_generator import (
    STATUS_COMPLETED,
    STATUS_PENDING,
    TASK_KEY_PREFIX,
    get_task_status,
    start_image_generation,
)


class MockRedisForCreation:
    """最小化 Redis mock"""

    def __init__(self):
        self._store = {}

    async def set(self, key, value, ex=None):
        self._store[key] = value

    async def get(self, key):
        return self._store.get(key)


class MockModelRouterForCreation:
    available_provider_count = 0  # mock 模式

    async def call_model(self, **kw):
        class FakeResult:
            content = "a beautiful digital art"
            model = "mock"
            cost_yuan = 0
        return FakeResult()


class TestStartImageGeneration:
    @pytest.mark.asyncio
    async def test_returns_task_id(self):
        redis = MockRedisForCreation()
        mr = MockModelRouterForCreation()

        task_id, estimated = await start_image_generation(
            agent={"name": "画龙", "persona_config": {}},
            topic={"title": "星空", "description": "画一幅星空", "keywords": ["starry"]},
            request_id="req-001",
            redis=redis,
            model_router=mr,
        )

        assert task_id.startswith("img-")
        assert estimated > 0

    @pytest.mark.asyncio
    async def test_task_initial_status(self):
        redis = MockRedisForCreation()
        mr = MockModelRouterForCreation()

        task_id, _ = await start_image_generation(
            agent={"name": "画龙"},
            topic={"title": "海洋"},
            request_id="req-002",
            redis=redis,
            model_router=mr,
        )

        # 等一下后台任务完成
        await asyncio.sleep(3)

        status = await get_task_status(task_id, redis)
        assert status is not None
        # mock 模式下应该 completed
        assert status["status"] == STATUS_COMPLETED
        assert "placehold" in status["image_url"]


class TestGetTaskStatus:
    @pytest.mark.asyncio
    async def test_nonexistent_task(self):
        redis = MockRedisForCreation()
        status = await get_task_status("nonexistent", redis)
        assert status is None

    @pytest.mark.asyncio
    async def test_existing_task(self):
        redis = MockRedisForCreation()
        data = {"task_id": "test-1", "status": STATUS_PENDING}
        await redis.set(f"{TASK_KEY_PREFIX}test-1", json.dumps(data))

        status = await get_task_status("test-1", redis)
        assert status["status"] == STATUS_PENDING
