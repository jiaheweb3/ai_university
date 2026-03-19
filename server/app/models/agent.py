"""
SQLAlchemy ORM — 智能体系统
4 张表: agents, agent_memories, agent_room_assignments, persona_templates
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from shared.constants import AgentLevel, AgentOwnerType, AgentStatus


class Agent(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "agents"

    owner_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    owner_type: Mapped[str] = mapped_column(
        Enum(AgentOwnerType, name="agent_owner_type", create_type=False),
        nullable=False,
        server_default="user",
    )
    name: Mapped[str] = mapped_column(String(24), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    level: Mapped[str] = mapped_column(
        Enum(AgentLevel, name="agent_level", create_type=False),
        nullable=False,
        server_default="L1",
    )
    status: Mapped[str] = mapped_column(
        Enum(AgentStatus, name="agent_status", create_type=False),
        nullable=False,
        server_default="active",
    )
    persona_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    knowledge_base: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # 运行时状态
    current_room_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True
    )
    is_speaking: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_speak_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    speak_count_today: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    task_count_today: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    # 暖场配置
    fallback_timeout_sec: Mapped[int | None] = mapped_column(SmallInteger, server_default="30")
    daily_topic_schedule: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    memories = relationship("AgentMemory", back_populates="agent", lazy="selectin")

    __table_args__ = (
        CheckConstraint("task_count_today >= 0 AND task_count_today <= 3", name="ck_agents_task_count"),
        Index("idx_agents_owner", "owner_id", "owner_type", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_agents_status", "status"),
        Index("idx_agents_room", "current_room_id", postgresql_where=text("current_room_id IS NOT NULL")),
    )


class AgentMemory(UUIDMixin, Base):
    __tablename__ = "agent_memories"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    agent = relationship("Agent", back_populates="memories")

    __table_args__ = (
        Index("idx_agent_memories_agent", "agent_id", "created_at",
              postgresql_where=text("deleted_at IS NULL")),
    )


class AgentRoomAssignment(UUIDMixin, Base):
    __tablename__ = "agent_room_assignments"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    assigned_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    removed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("agent_id", "room_id", name="uq_agent_room"),
        Index("idx_agent_room_active", "room_id", postgresql_where=text("is_active = TRUE")),
    )


class PersonaTemplate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "persona_templates"

    name: Mapped[str] = mapped_column(String(24), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    persona_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_onboarding: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
