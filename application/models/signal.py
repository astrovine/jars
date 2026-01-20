from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, func, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from .base import Base
from .enums import OrderSide, OrderType


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (
        Index('ix_signals_leader_emitted', 'leader_profile_id', 'emitted_at'),
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    leader_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trader_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(
        Enum(OrderSide, native_enum=True, name="order_side"),
        nullable=False
    )

    order_type = Column(
        Enum(OrderType, native_enum=True, name="order_type"),
        nullable=False,
        default=OrderType.MARKET
    )

    quantity = Column(Numeric(precision=20, scale=8), nullable=False)
    price = Column(Numeric(precision=20, scale=8), nullable=False)
    raw_exchange_response = Column(JSONB, nullable=True)
    emitted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    trader_profile = relationship("TraderProfile", back_populates="signals")
    trades = relationship("Trade", back_populates="signal")

