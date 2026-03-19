"""
SQLAlchemy ORM — 房间系统
2 张表: rooms, room_members
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from shared.constants import RoomStatus


class Room(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "rooms"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, server_default="general")
    tags: Mapped[list | None] = mapped_column(ARRAY(String(256)), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(RoomStatus, name="room_status", create_type=False),
        nullable=False,
        server_default="active",
    )
    max_members: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="200")
    online_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    message_count: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    members = relationship("RoomMember", back_populates="room", lazy="selectin")

    __table_args__ = (
        Index("idx_rooms_status", "status"),
        Index("idx_rooms_category", "category"),
    )


class RoomMember(UUIDMixin, Base):
    __tablename__ = "room_members"

    room_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    member_type: Mapped[str] = mapped_column(
        Enum("user", "agent", "system", name="sender_type", create_type=False),
        nullable=False,
    )
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    left_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    room = relationship("Room", back_populates="members")

    __table_args__ = (
        UniqueConstraint("room_id", "member_id", "member_type", name="uq_room_members"),
        Index("idx_room_members_room", "room_id", postgresql_where=text("left_at IS NULL")),
        Index("idx_room_members_member", "member_id", "member_type"),
    )
