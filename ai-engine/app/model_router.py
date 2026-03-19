"""
AetherVerse AI Engine — 模型路由核心
多供应商管理 (DeepSeek / Zhipu / OpenAI 兼容) + 场景路由 + fallback 降级
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

import structlog
from openai import AsyncOpenAI

from shared.constants import AIScene
from shared.exceptions import AppException, ErrorCode

from .config import Settings, get_settings
from .schemas import GenerationResult

logger = structlog.get_logger(__name__)


# ── 数据结构 ─────────────────────────────────────────────

@dataclass
class ModelConfig:
    """路由决策结果"""
    provider: str
    model: str
    base_url: str
    api_key: str
    timeout_ms: int = 10_000
    is_fallback: bool = False


@dataclass
class RoutingChain:
    """一个场景的完整路由链（主 + fallback）"""
    primary: ModelConfig | None = None
    fallbacks: list[ModelConfig] = field(default_factory=list)

    def all_configs(self) -> list[ModelConfig]:
        configs = []
        if self.primary:
            configs.append(self.primary)
        configs.extend(self.fallbacks)
        return configs


# ── 默认路由配置 ─────────────────────────────────────────

_DEFAULT_ROUTES: dict[str, list[dict]] = {
    AIScene.CHAT: [
        {"provider": "deepseek", "model": "deepseek-chat", "is_fallback": False},
        {"provider": "zhipu", "model": "glm-4-flash", "is_fallback": True},
    ],
    AIScene.LISTEN_EVAL: [
        {"provider": "deepseek", "model": "deepseek-chat", "is_fallback": False},
        {"provider": "zhipu", "model": "glm-4-flash", "is_fallback": True},
    ],
    AIScene.MEMORY_SUMMARY: [
        {"provider": "deepseek", "model": "deepseek-chat", "is_fallback": False},
    ],
    AIScene.IMAGE_GEN: [
        {"provider": "zhipu", "model": "cogview-3-plus", "is_fallback": False},
    ],
    AIScene.MODERATION: [
        {"provider": "deepseek", "model": "deepseek-chat", "is_fallback": False},
    ],
}


class ModelRouter:
    """AI 模型统一路由器"""

    def __init__(self, settings: Settings | None = None, redis: Any = None) -> None:
        self._settings = settings or get_settings()
        self._redis = redis
        self._clients: dict[str, AsyncOpenAI] = {}
        self._route_cache: dict[str, tuple[float, RoutingChain]] = {}
        self._init_clients()

    # ── 初始化 OpenAI 兼容客户端 ──────────────────────────

    def _init_clients(self) -> None:
        """为每个有 API Key 的供应商创建 AsyncOpenAI 客户端"""
        providers = {
            "deepseek": (self._settings.DEEPSEEK_API_KEY, self._settings.DEEPSEEK_BASE_URL),
            "zhipu": (self._settings.ZHIPU_API_KEY, self._settings.ZHIPU_BASE_URL),
            "openai": (self._settings.OPENAI_API_KEY, self._settings.OPENAI_BASE_URL),
        }
        for name, (api_key, base_url) in providers.items():
            if api_key:
                self._clients[name] = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=self._settings.MODEL_TIMEOUT_SEC,
                    max_retries=self._settings.MODEL_MAX_RETRIES,
                )

    # ── 路由决策 ──────────────────────────────────────────

    async def route(self, scene: AIScene) -> RoutingChain:
        """
        根据场景获取路由链。
        优先从 Redis 读取 admin 配置的路由规则，缓存 TTL 内用本地缓存。
        Redis 不可用时降级到默认配置。
        """
        cache_key = f"route:{scene}"
        now = time.monotonic()

        # 本地缓存命中
        if cache_key in self._route_cache:
            ts, chain = self._route_cache[cache_key]
            if now - ts < self._settings.ROUTING_CACHE_TTL_SEC:
                return chain

        # 尝试从 Redis 读取
        chain = await self._load_from_redis(scene)
        if chain is None:
            chain = self._load_defaults(scene)

        self._route_cache[cache_key] = (now, chain)
        return chain

    async def _load_from_redis(self, scene: AIScene) -> RoutingChain | None:
        """从 Redis hash ai:routing:{scene} 加载路由规则"""
        if self._redis is None:
            return None
        try:
            raw = await self._redis.get(f"ai:routing:{scene}")
            if not raw:
                return None
            rules = json.loads(raw)
            return self._build_chain(rules)
        except Exception as exc:
            await logger.awarning("redis_routing_load_failed", scene=scene, error=str(exc))
            return None

    def _load_defaults(self, scene: AIScene) -> RoutingChain:
        """从默认配置加载路由链"""
        rules = _DEFAULT_ROUTES.get(scene, _DEFAULT_ROUTES[AIScene.CHAT])
        return self._build_chain(rules)

    def _build_chain(self, rules: list[dict]) -> RoutingChain:
        """将规则列表构建为 RoutingChain"""
        chain = RoutingChain()
        for rule in rules:
            provider = rule["provider"]
            api_key = self._get_api_key(provider)
            if not api_key:
                continue
            config = ModelConfig(
                provider=provider,
                model=rule["model"],
                base_url=self._get_base_url(provider),
                api_key=api_key,
                timeout_ms=rule.get("timeout_ms", self._settings.MODEL_TIMEOUT_SEC * 1000),
                is_fallback=rule.get("is_fallback", False),
            )
            if not config.is_fallback and chain.primary is None:
                chain.primary = config
            else:
                chain.fallbacks.append(config)
        return chain

    def _get_api_key(self, provider: str) -> str:
        mapping = {
            "deepseek": self._settings.DEEPSEEK_API_KEY,
            "zhipu": self._settings.ZHIPU_API_KEY,
            "openai": self._settings.OPENAI_API_KEY,
        }
        return mapping.get(provider, "")

    def _get_base_url(self, provider: str) -> str:
        mapping = {
            "deepseek": self._settings.DEEPSEEK_BASE_URL,
            "zhipu": self._settings.ZHIPU_BASE_URL,
            "openai": self._settings.OPENAI_BASE_URL,
        }
        return mapping.get(provider, "")

    # ── 调用模型 ──────────────────────────────────────────

    async def call_model(
        self,
        scene: AIScene,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 300,
        temperature: float = 0.7,
        response_format: dict | None = None,
    ) -> GenerationResult:
        """
        按场景调用模型。主模型超时/失败 → 自动 fallback。
        返回 GenerationResult。
        """
        chain = await self.route(scene)
        configs = chain.all_configs()

        if not configs:
            raise AppException(
                code=ErrorCode.AI_MODEL_ERROR,
                message="No available AI model for this scene",
                detail=f"scene={scene}, no API keys configured",
                status_code=503,
            )

        last_error: Exception | None = None
        for config in configs:
            try:
                result = await self._call_single(config, messages, max_tokens, temperature, response_format)
                return result
            except asyncio.TimeoutError:
                await logger.awarning(
                    "model_timeout", provider=config.provider, model=config.model, scene=scene
                )
                last_error = asyncio.TimeoutError(f"{config.provider}/{config.model} timeout")
            except Exception as exc:
                await logger.awarning(
                    "model_call_failed",
                    provider=config.provider,
                    model=config.model,
                    scene=scene,
                    error=str(exc),
                )
                last_error = exc

        raise AppException(
            code=ErrorCode.AI_MODEL_ERROR,
            message="All AI models failed",
            detail=str(last_error),
            status_code=503,
        )

    async def _call_single(
        self,
        config: ModelConfig,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        response_format: dict | None,
    ) -> GenerationResult:
        """调用单个模型"""
        client = self._clients.get(config.provider)
        if client is None:
            # 动态创建
            client = AsyncOpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=config.timeout_ms / 1000,
            )
            self._clients[config.provider] = client

        start = time.monotonic()
        kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "timeout": config.timeout_ms / 1000,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = await client.chat.completions.create(**kwargs)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        choice = response.choices[0]
        usage = response.usage

        return GenerationResult(
            content=choice.message.content or "",
            model=config.model,
            provider=config.provider,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency_ms=elapsed_ms,
            cost_yuan=self._estimate_cost(config.provider, usage),
        )

    def _estimate_cost(self, provider: str, usage: Any) -> float:
        """粗估成本（元）。价格从 Settings 配置读取。"""
        if not usage:
            return 0.0
        input_t = usage.prompt_tokens or 0
        output_t = usage.completion_tokens or 0
        prices = {
            "deepseek": (self._settings.PRICE_DEEPSEEK_INPUT, self._settings.PRICE_DEEPSEEK_OUTPUT),
            "zhipu": (self._settings.PRICE_ZHIPU_INPUT, self._settings.PRICE_ZHIPU_OUTPUT),
            "openai": (self._settings.PRICE_OPENAI_INPUT, self._settings.PRICE_OPENAI_OUTPUT),
        }
        ip, op = prices.get(provider, (1.0 / 1_000_000, 2.0 / 1_000_000))
        return round(input_t * ip + output_t * op, 6)

    # ── 健康检查 ──────────────────────────────────────────

    async def check_health(self) -> dict[str, dict]:
        """检查所有已配置供应商的可用性"""
        result = {}
        for name, client in self._clients.items():
            try:
                start = time.monotonic()
                await asyncio.wait_for(
                    client.models.list(),
                    timeout=5.0,
                )
                latency = int((time.monotonic() - start) * 1000)
                result[name] = {"status": "active", "latency_ms": latency}
            except Exception as exc:
                result[name] = {"status": "error", "error": str(exc)}
        return result

    @property
    def available_provider_count(self) -> int:
        return len(self._clients)
