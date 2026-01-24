from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, func, Enum, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base
from .enums import OrderSide, TradeStatus


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index('ix_trades_subscription_created', 'subscription_id', 'created_at'),
        Index('ix_trades_signal_status', 'signal_id', 'status'),
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("signals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    exchange_key_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exchange_keys.id", ondelete="SET NULL"),
        nullable=True
    )
    binance_order_id = Column(String(100), nullable=True, index=True)
    status = Column(
        Enum(TradeStatus, native_enum=True, name="trade_status"),
        nullable=False,
        default=TradeStatus.PENDING,
        index=True
    )
    side = Column(
        Enum(OrderSide, native_enum=True, name="order_side_trade"),
        nullable=False
    )
    requested_amount = Column(Numeric(precision=20, scale=8), nullable=False)
    filled_amount = Column(Numeric(precision=20, scale=8), nullable=True)
    filled_price = Column(Numeric(precision=20, scale=8), nullable=True)
    fee_paid = Column(Numeric(precision=20, scale=8), nullable=True)
    fee_currency = Column(String(10), nullable=True)
    realized_pnl = Column(Numeric(18, 8), nullable=True, comment="Final PnL snapshot when trade closes")
    error_message = Column(String(500), nullable=True)
    latency_ms = Column(Integer, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    executed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    signal = relationship("Signal", back_populates="trades")
    subscription = relationship("Subscription", back_populates="trades")
    exchange_key = relationship("ExchangeKey")

