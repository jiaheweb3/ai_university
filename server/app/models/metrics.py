"""
SQLAlchemy ORM — 数据看板 (T+1 聚合)
2 张表: daily_metrics, daily_room_metrics
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    TIMESTAMP,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class DailyMetric(UUIDMixin, Base):
    __tablename__ = "daily_metrics"

    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    dau: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    mau: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    new_users: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    d1_retention: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    d3_retention: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    d7_retention: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    d14_retention: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    d30_retention: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    speak_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    agent_usage_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    total_messages: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    recharge_yuan: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    recharge_users: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    points_consumed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    ai_cost_yuan: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    arpu_yuan: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    pay_conversion: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    __table_args__ = (
        Index("idx_daily_metrics_date", "metric_date", unique=True),
    )


class DailyRoomMetric(UUIDMixin, Base):
    __tablename__ = "daily_room_metrics"

    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False
    )
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    active_users: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    avg_messages_per_user: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    peak_online: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    __table_args__ = (
        Index("idx_daily_room_date", "metric_date", "room_id", unique=True),
    )
