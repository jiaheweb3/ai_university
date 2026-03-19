"""
SQLAlchemy ORM — 审核系统
2 张表: moderation_queue, sensitive_words
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from shared.constants import ModerationStatus, SensitiveWordLevel


class ModerationQueue(UUIDMixin, Base):
    __tablename__ = "moderation_queue"

    content_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(
        Enum("auto_block", "auto_suspect", "manual_report", "appeal",
             name="moderation_trigger", create_type=False),
        nullable=False,
    )
    trigger_detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(ModerationStatus, name="moderation_status", create_type=False),
        nullable=False,
        server_default="pending",
    )
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="5")
    context_messages: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # 审核结果
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    review_result: Mapped[str | None] = mapped_column(String(32), nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # 申诉
    appeal_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    appeal_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    __table_args__ = (
        Index("idx_moderation_status", "status", "priority", "created_at"),
        Index("idx_moderation_content", "content_id", "content_type"),
        Index("idx_moderation_reviewer", "reviewer_id",
              postgresql_where=text("reviewer_id IS NOT NULL")),
    )


class SensitiveWord(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sensitive_words"

    word: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[str] = mapped_column(
        Enum(SensitiveWordLevel, name="sensitive_level", create_type=False), nullable=False
    )
    variants: Mapped[list | None] = mapped_column(ARRAY(String(256)), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    __table_args__ = (
        Index("idx_sensitive_words_active", "is_active", "category"),
    )
