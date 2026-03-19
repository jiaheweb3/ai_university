"""
SQLAlchemy ORM — 创作系统
2 张表: topics, artworks
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from shared.constants import ArtworkStatus, TopicStatus


class Topic(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "topics"

    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list | None] = mapped_column(ARRAY(String(64)), nullable=True)
    reference_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(TopicStatus, name="topic_status", create_type=False),
        nullable=False,
        server_default="draft",
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True
    )
    deadline: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    participant_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    artwork_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_topics_status", "status", "deadline"),
    )


class Artwork(UUIDMixin, Base):
    __tablename__ = "artworks"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(ArtworkStatus, name="artwork_status", create_type=False),
        nullable=False,
        server_default="generating",
    )

    # AIGC 标识
    aigc_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aigc_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aigc_watermark: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # 创作过程元数据
    creative_process: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="'{}'")
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    __table_args__ = (
        Index("idx_artworks_topic", "topic_id", "status"),
        Index("idx_artworks_agent", "agent_id"),
        Index("idx_artworks_owner", "owner_id"),
        Index("idx_artworks_review", "status", postgresql_where=text("status = 'pending_review'")),
    )
