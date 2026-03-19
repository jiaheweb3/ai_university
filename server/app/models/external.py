"""
SQLAlchemy ORM — 外部 Agent 接入 (Phase 1B)
2 张表: external_agents, external_agent_logs
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Index,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ExternalAgent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "external_agents"

    developer_name: Mapped[str] = mapped_column(String(64), nullable=False)
    app_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    app_secret_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    jwt_secret_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    callback_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    allowed_scopes: Mapped[list] = mapped_column(
        ARRAY(String(64)), nullable=False, server_default="{}"
    )
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, nullable=False, server_default="60")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")


class ExternalAgentLog(UUIDMixin, Base):
    __tablename__ = "external_agent_logs"

    agent_app_id: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(128), nullable=False)
    method: Mapped[str] = mapped_column(String(8), nullable=False)
    status_code: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    request_body_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    __table_args__ = (
        Index("idx_ext_agent_logs_app", "agent_app_id", "created_at"),
    )
