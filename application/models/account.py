from sqlalchemy import Column, String, Boolean, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base
from .enums import SubscriptionTier, UserTier


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(255), nullable=False, default="NOT VERIFIED")
    password = Column(String(255), nullable=False)
    two_factor_secret = Column(String(255), nullable=True)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    password_reset_token = Column(String(255), nullable=True)
    email_verification_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    country = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)
    virtual_balance_reset_at = Column(DateTime(timezone=True), nullable=True)
    virtual_balance_blown_at = Column(DateTime(timezone=True), nullable=True)
    
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

    trader_profile = relationship("TraderProfile", back_populates="user", uselist=False)
    kyc = relationship("UserKYC", back_populates="user", uselist=False)
    tier_account = relationship("SubscriptionTierAccounts", back_populates="user", uselist=False)
    subscriptions = relationship("Subscription", back_populates="follower")
    exchange_keys = relationship("ExchangeKey", back_populates="user")
    accounts = relationship("Account", back_populates="user")
