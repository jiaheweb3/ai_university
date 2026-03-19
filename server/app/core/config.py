"""
AetherVerse Server — 配置管理
使用 pydantic-settings 从环境变量 / .env 加载
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- 数据库 ----
    DATABASE_URL: str = "postgresql+asyncpg://aetherverse:dev_password_change_me@localhost:5432/aetherverse"

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- RabbitMQ ----
    RABBITMQ_URL: str = "amqp://aetherverse:dev_password_change_me@localhost:5672/"

    # ---- 对象存储 ----
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "aetherverse"
    S3_SECRET_KEY: str = "dev_password_change_me"
    S3_BUCKET: str = "aetherverse"

    # ---- JWT ----
    JWT_SECRET: str = "change-this-to-a-random-256-bit-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ---- 手机号加密 ----
    PHONE_AES_KEY: str = "0123456789abcdef0123456789abcdef"  # 32 字节 hex → 16 bytes AES-128

    # ---- AI 引擎通信 ----
    AI_ENGINE_URL: str = "http://localhost:8001"
    INTERNAL_API_KEY: str = "change-this-internal-key"

    # ---- SMS (Phase 1 dev: mock) ----
    SMS_MOCK: bool = True  # True = 固定验证码 123456
    SMS_MOCK_CODE: str = "123456"

    # ---- 开发模式 ----
    DEBUG: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
