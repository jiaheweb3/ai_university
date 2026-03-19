"""
SQLAlchemy ORM — 积分与计费系统
2 张表: point_transactions, recharge_orders
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    TIMESTAMP,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from shared.constants import OrderStatus, PayChannel, PointTxStatus, PointTxType


class PointTransaction(UUIDMixin, Base):
    __tablename__ = "point_transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    tx_type: Mapped[str] = mapped_column(
        Enum(PointTxType, name="point_tx_type", create_type=False), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(PointTxStatus, name="point_tx_status", create_type=False),
        nullable=False,
        server_default="frozen",
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    frozen_amount: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    balance_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    related_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    related_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_point_tx_user", "user_id", "created_at"),
        Index("idx_point_tx_status", "status", postgresql_where=text("status = 'frozen'")),
        Index("idx_point_tx_request", "request_id", unique=True,
              postgresql_where=text("request_id IS NOT NULL")),
    )


class RechargeOrder(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recharge_orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    channel: Mapped[str] = mapped_column(
        Enum(PayChannel, name="payment_channel", create_type=False), nullable=False
    )
    channel_order_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount_yuan: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    points_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(OrderStatus, name="order_status", create_type=False),
        nullable=False,
        server_default="pending",
    )
    paid_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_recharge_orders_user", "user_id", "created_at"),
        Index("idx_recharge_orders_status", "status", postgresql_where=text("status = 'pending'")),
    )
