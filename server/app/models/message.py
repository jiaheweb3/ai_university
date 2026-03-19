"""
SQLAlchemy ORM — 消息 & 聊天系统
2 张表: messages, conversations
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
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from shared.constants import MessageType, ModerationStatus


class Message(UUIDMixin, Base):
    __tablename__ = "messages"

    room_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    sender_type: Mapped[str] = mapped_column(
        Enum("user", "agent", "system", name="sender_type", create_type=False),
        nullable=False,
    )
    msg_type: Mapped[str] = mapped_column(
        Enum(MessageType, name="message_type", create_type=False),
        nullable=False,
        server_default="text",
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    reply_to_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    mentions: Mapped[list | None] = mapped_column(ARRAY(PG_UUID(as_uuid=True)), nullable=True)

    # AIGC 标识
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    aigc_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aigc_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 审核
    moderation_status: Mapped[str | None] = mapped_column(
        Enum(ModerationStatus, name="moderation_status", create_type=False),
        server_default="approved",
    )
    moderation_code: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # 元数据
    client_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "(room_id IS NOT NULL AND conversation_id IS NULL) OR "
            "(room_id IS NULL AND conversation_id IS NOT NULL)",
            name="ck_messages_target",
        ),
        Index("idx_messages_room_time", "room_id", "created_at", postgresql_where=text("room_id IS NOT NULL")),
        Index("idx_messages_conv_time", "conversation_id", "created_at",
              postgresql_where=text("conversation_id IS NOT NULL")),
        Index("idx_messages_sender", "sender_id", "sender_type", "created_at"),
        Index("idx_messages_request_id", "request_id", unique=True,
              postgresql_where=text("request_id IS NOT NULL")),
        Index("idx_messages_moderation", "moderation_status",
              postgresql_where=text("moderation_status != 'approved'")),
    )


class Conversation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    conv_type: Mapped[str] = mapped_column(
        Enum("user_to_user", "user_to_agent", name="conversation_type", create_type=False),
        nullable=False,
    )
    participant_a: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    participant_b: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    participant_b_type: Mapped[str] = mapped_column(
        Enum("user", "agent", "system", name="sender_type", create_type=False),
        nullable=False,
    )
    last_message_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    unread_count_a: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    unread_count_b: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    __table_args__ = (
        UniqueConstraint("participant_a", "participant_b", "participant_b_type", name="uq_conversations"),
        Index("idx_conversations_a", "participant_a", "last_message_at"),
        Index("idx_conversations_b", "participant_b", "participant_b_type", "last_message_at"),
    )

