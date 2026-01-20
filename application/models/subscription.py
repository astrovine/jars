from sqlalchemy import Column, Numeric, ForeignKey, DateTime, func, Enum, UniqueConstraint, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base
from .enums import SubscriptionStatus, CopyMode, SubscriptionTier, SubscriptionTierStatus


class TradingTiers(Base):
    __tablename__ = "trading_tiers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tier_name = Column(Enum(SubscriptionTier), nullable=False, unique=True)
    max_follows = Column(Numeric, nullable=False)
    monthly_fee = Column(Numeric(precision=20, scale=8), nullable=False, default=0)
    fee_discount_percent = Column(Numeric(precision=5, scale=2), nullable=False, default=0)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) #Basically when last I updated the pricing
    
    tier_accounts = relationship("SubscriptionTierAccounts", back_populates="tier")


class SubscriptionTierAccounts(Base):
    __tablename__ = "subscription_tier_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    tier_id = Column(UUID(as_uuid=True), ForeignKey('trading_tiers.id'), nullable=False)
    payment_ref = Column(String(255), nullable=True) #paystack
    tier_status = Column(Enum(SubscriptionTierStatus), default=SubscriptionTierStatus.ACTIVE, nullable=False)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=False)
    activated_at = Column(DateTime(timezone=True), server_default=func.now())
    renewed_at = Column(DateTime(timezone=True), nullable=True)
    
    tier = relationship("TradingTiers", back_populates="tier_accounts")
    user = relationship("User", back_populates="tier_account")
    subscriptions = relationship("Subscription", back_populates="tier_account")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint('subscriber_id', 'trader_id', name='uq_subscriber_trader'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscriber_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    trader_id = Column(UUID(as_uuid=True), ForeignKey('trader_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    tier_account_id = Column(UUID(as_uuid=True), ForeignKey('subscription_tier_accounts.id'), nullable=False)
    sub_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.INACTIVE, nullable=False)
    copy_mode = Column(Enum(CopyMode), default=CopyMode.PROPORTIONAL, nullable=False)
    allocation_percent = Column(Numeric(precision=5, scale=2), nullable=False)  # like from 1-100%
    reserved_amount = Column(Numeric(precision=20, scale=8), default=0, nullable=False)  # Locked USDT
    stop_loss_percent = Column(Numeric(precision=5, scale=2), nullable=True)  # Auto unsubscribe threshold
    is_shadow_mode = Column(Boolean, default=False, nullable=False)
    virtual_pnl = Column(Numeric(precision=20, scale=8), default=0)  # Track paper trading P&L
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    paused_at = Column(DateTime(timezone=True), nullable=True)
    
    follower = relationship("User", back_populates="subscriptions")
    trader_profile = relationship("TraderProfile", back_populates="subscriptions")
    tier_account = relationship("SubscriptionTierAccounts", back_populates="subscriptions")
    trades = relationship("Trade", back_populates="subscription")