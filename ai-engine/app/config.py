"""
AetherVerse AI Engine — 配置管理
从环境变量 / .env 加载，Pydantic Settings 验证
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AI 引擎全局配置"""

    # ---- 服务 ----
    SERVICE_NAME: str = "aetherverse-ai-engine"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ---- 内部认证 ----
    INTERNAL_API_KEY: str = "changeme"

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- RabbitMQ ----
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    MQ_EXCHANGE: str = "aetherverse.internal"

    # ---- AI 模型供应商 ----
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    ZHIPU_API_KEY: str = ""
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # ---- 超时 & 限制 ----
    MODEL_TIMEOUT_SEC: int = 10
    MODEL_MAX_RETRIES: int = 1
    IDEMPOTENT_TTL_SEC: int = 3600  # 幂等缓存 1 小时

    # ---- 路由缓存 ----
    ROUTING_CACHE_TTL_SEC: int = 60

    # ---- 提示词 ----
    PROMPTS_DIR: str = "prompts"

    # ---- 模型计价 (元/token) ----
    PRICE_DEEPSEEK_INPUT: float = 1.0 / 1_000_000
    PRICE_DEEPSEEK_OUTPUT: float = 2.0 / 1_000_000
    PRICE_ZHIPU_INPUT: float = 0.1 / 1_000_000
    PRICE_ZHIPU_OUTPUT: float = 0.1 / 1_000_000
    PRICE_OPENAI_INPUT: float = 3.0 / 1_000_000
    PRICE_OPENAI_OUTPUT: float = 6.0 / 1_000_000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


@lru_cache
def get_settings() -> Settings:
    return Settings()
