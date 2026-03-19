"""
SQLAlchemy ORM — 用户系统
5 张表: users, user_dids, user_settings, user_blocks, login_attempts
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import INET, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from shared.constants import UserStatus


class User(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    phone_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    phone_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    nickname: Mapped[str] = mapped_column(String(32), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(400), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(UserStatus, name="user_status", create_type=False),
        nullable=False,
        server_default="active",
    )
    points_balance: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    points_frozen: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    free_chat_remaining: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="20")
    free_image_remaining: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="2")
    free_quota_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    agent_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    last_active_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # 关系
    dids = relationship("UserDID", back_populates="user", lazy="selectin")
    settings = relationship("UserSetting", back_populates="user", uselist=False, lazy="selectin")

    __table_args__ = (
        CheckConstraint("points_balance >= 0", name="ck_users_points_balance"),
        CheckConstraint("points_frozen >= 0", name="ck_users_points_frozen"),
        CheckConstraint("agent_count >= 0 AND agent_count <= 3", name="ck_users_agent_count"),
        Index("idx_users_phone_hash", "phone_hash", unique=True, postgresql_where=text("deleted_at IS NULL")),
        Index("idx_users_status", "status"),
        Index("idx_users_created_at", "created_at"),
    )


class UserDID(UUIDMixin, Base):
    __tablename__ = "user_dids"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    did_value: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    did_method: Mapped[str] = mapped_column(String(32), nullable=False, server_default="aetherverse")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    user = relationship("User", back_populates="dids")

    __table_args__ = (
        Index("idx_user_dids_user", "user_id"),
    )


class UserSetting(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    notification_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    privacy_show_agents: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    user = relationship("User", back_populates="settings")


class UserBlock(Base):
    __tablename__ = "user_blocks"

    blocker_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    blocked_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    blocked_type: Mapped[str] = mapped_column(
        Enum("user", "agent", "system", name="sender_type", create_type=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )


class LoginAttempt(UUIDMixin, Base):
    __tablename__ = "login_attempts"

    phone_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str] = mapped_column(INET, nullable=False)
    device_info: Mapped[str | None] = mapped_column(String(512), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    __table_args__ = (
        Index("idx_login_attempts_phone", "phone_hash", "created_at"),
        Index("idx_login_attempts_ip", "ip_address", "created_at"),
    )
