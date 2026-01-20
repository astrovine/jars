import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, func, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base


class EventType(str, enum.Enum):
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_PAUSED = "subscription.paused"
    SUBSCRIPTION_RESUMED = "subscription.resumed"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_REACTIVATED = "subscription.reactivated"

    TIER_SUBSCRIBED = "tier.subscribed"
    TIER_RENEWED = "tier.renewed"
    TIER_EXPIRED = "tier.expired"
    TIER_UPGRADED = "tier.upgraded"

    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"

    TRADE_COPIED = "trade.copied"
    TRADE_EXECUTED = "trade.executed"
    TRADE_FAILED = "trade.failed"

    USER_REGISTERED = "user.registered"
    USER_VERIFIED = "user.verified"
    USER_API_KEY_ADDED = "user.api_key_added"
    USER_API_KEY_REMOVED = "user.api_key_removed"


class AggregateType(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    TIER_ACCOUNT = "tier_account"
    PAYMENT = "payment"
    TRADE = "trade"
    USER = "user"
    TRADER_PROFILE = "trader_profile"


class DomainEvent(Base):
    __tablename__ = "domain_events"
    __table_args__ = (
        Index('ix_domain_events_aggregate', 'aggregate_type', 'aggregate_id'),
        Index('ix_domain_events_user_time', 'user_id', 'created_at'),
        Index('ix_domain_events_type_time', 'event_type', 'created_at'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    event_type = Column(
        SQLEnum(EventType, native_enum=True, name='event_type_enum'),
        nullable=False,
        index=True
    )
    
    aggregate_type = Column(
        SQLEnum(AggregateType, native_enum=True, name='aggregate_type_enum'),
        nullable=False
    )
    aggregate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    payload = Column(JSONB, nullable=False, default={})
    event_metadata = Column(JSONB, nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True)
    causation_id = Column(UUID(as_uuid=True), nullable=True)    # The event that basically caused this one
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
