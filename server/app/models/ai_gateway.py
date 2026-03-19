"""
SQLAlchemy ORM — AI 网关管理
5 张表: ai_providers, ai_api_keys, ai_routing_rules, ai_usage_logs, ai_budget_config
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from shared.constants import AIScene


class AIProvider(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ai_providers"

    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "disabled", "degraded", name="provider_status", create_type=False),
        nullable=False,
        server_default="active",
    )
    health_check_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    last_health_check: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class AIApiKey(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ai_api_keys"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ai_providers.id"), nullable=False
    )
    key_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_hint: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    daily_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    reset_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index("idx_ai_keys_provider", "provider_id", "is_active"),
    )


class AIRoutingRule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ai_routing_rules"

    scene: Mapped[str] = mapped_column(
        Enum(AIScene, name="ai_scene", create_type=False), nullable=False
    )
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")
    provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ai_providers.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10000")
    max_retries: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    __table_args__ = (
        Index("idx_routing_scene", "scene", "priority", postgresql_where=text("is_active = TRUE")),
    )


class AIUsageLog(UUIDMixin, Base):
    __tablename__ = "ai_usage_logs"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ai_providers.id"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    scene: Mapped[str] = mapped_column(
        Enum(AIScene, name="ai_scene", create_type=False), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    cost_yuan: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False, server_default="0")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    __table_args__ = (
        Index("idx_ai_usage_time", "created_at"),
        Index("idx_ai_usage_provider", "provider_id", "created_at"),
        Index("idx_ai_usage_user", "user_id", "created_at",
              postgresql_where=text("user_id IS NOT NULL")),
        Index("idx_ai_usage_scene", "scene", "created_at"),
    )


class AIBudgetConfig(UUIDMixin, Base):
    __tablename__ = "ai_budget_config"

    daily_limit_yuan: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    alert_threshold: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="0.80"
    )
    alert_webhook: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
