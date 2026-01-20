from sqlalchemy import Column, String, Boolean, Numeric, ForeignKey, DateTime, func, Enum, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from .base import Base
from .enums import TraderProfileStatus


class TraderProfile(Base):
    __tablename__ = "trader_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    alias = Column(String(50), nullable=False, unique=True, index=True)
    bio = Column(String(500), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    performance_fee_percentage = Column(
        Numeric(precision=5, scale=2),
        nullable=False,
        default=20.00
    )
    min_allocation_amount = Column(
        Numeric(precision=20, scale=8),
        nullable=False,
        default=0
    )
    min_capital_requirement = Column(
        Numeric(precision=20, scale=8),
        nullable=False,
        default=50.00
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    status = Column(Enum(TraderProfileStatus), default=TraderProfileStatus.DRAFT, nullable=False)
    stats_snapshot = Column(
        JSONB,
        nullable=True,
        default={}
    )
    probation_trades_count = Column(Integer, default=0)
    probation_start_date = Column(DateTime(timezone=True), nullable=True)

    # Performance Stats for Public view and all
    risk_score = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    total_roi = Column(Float, default=0.0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    user = relationship("User", back_populates="trader_profile")
    subscriptions = relationship("Subscription", back_populates="trader_profile")
    signals = relationship("Signal", back_populates="trader_profile")

