"""
测试 — 模型路由 (model_router)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from shared.constants import AIScene

from app.model_router import ModelConfig, ModelRouter, RoutingChain


class TestRoutingChain:
    def test_all_configs_with_primary_and_fallbacks(self):
        chain = RoutingChain(
            primary=ModelConfig(
                provider="deepseek", model="deepseek-chat", base_url="http://a", api_key="k1"
            ),
            fallbacks=[
                ModelConfig(
                    provider="zhipu", model="glm-4-flash", base_url="http://b", api_key="k2", is_fallback=True
                )
            ],
        )
        configs = chain.all_configs()
        assert len(configs) == 2
        assert configs[0].provider == "deepseek"
        assert configs[1].provider == "zhipu"

    def test_empty_chain(self):
        chain = RoutingChain()
        assert chain.all_configs() == []


class TestModelRouter:
    def test_init_no_keys(self):
        """无 API Key → 无客户端"""
        from app.config import Settings
        settings = Settings(DEEPSEEK_API_KEY="", ZHIPU_API_KEY="", OPENAI_API_KEY="")
        router = ModelRouter(settings)
        assert router.available_provider_count == 0

    def test_init_with_keys(self):
        """有 API Key → 创建对应客户端"""
        from app.config import Settings
        settings = Settings(DEEPSEEK_API_KEY="sk-test", ZHIPU_API_KEY="", OPENAI_API_KEY="")
        router = ModelRouter(settings)
        assert router.available_provider_count == 1

    @pytest.mark.asyncio
    async def test_route_defaults(self):
        """无 Redis → 使用默认路由"""
        from app.config import Settings
        settings = Settings(DEEPSEEK_API_KEY="sk-test")
        router = ModelRouter(settings, redis=None)
        chain = await router.route(AIScene.CHAT)
        assert chain.primary is not None
        assert chain.primary.provider == "deepseek"

    @pytest.mark.asyncio
    async def test_route_no_available_models(self):
        """无可用模型 → 空路由链"""
        from app.config import Settings
        settings = Settings(DEEPSEEK_API_KEY="", ZHIPU_API_KEY="", OPENAI_API_KEY="")
        router = ModelRouter(settings)
        chain = await router.route(AIScene.CHAT)
        assert chain.all_configs() == []

    @pytest.mark.asyncio
    async def test_call_model_no_providers_raises(self):
        """无供应商 → 抛出异常"""
        from shared.exceptions import AppException
        from app.config import Settings
        settings = Settings(DEEPSEEK_API_KEY="", ZHIPU_API_KEY="", OPENAI_API_KEY="")
        router = ModelRouter(settings)
        with pytest.raises(AppException) as exc_info:
            await router.call_model(
                AIScene.CHAT,
                [{"role": "user", "content": "test"}],
            )
        assert exc_info.value.code == 50002  # AI_MODEL_ERROR

    def test_estimate_cost_deepseek(self):
        """DeepSeek 成本估算"""
        router = ModelRouter()
        usage = MagicMock(prompt_tokens=1000, completion_tokens=500)
        cost = router._estimate_cost("deepseek", usage)
        # 1000 * 1/M + 500 * 2/M = 0.002
        assert abs(cost - 0.002) < 0.0001

    def test_estimate_cost_no_usage(self):
        router = ModelRouter()
        assert router._estimate_cost("deepseek", None) == 0.0
