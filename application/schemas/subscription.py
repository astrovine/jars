"""
Subscription Schemas

Pydantic models for subscription API requests and responses.
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from application.models.enums import SubscriptionStatus, CopyMode


class SubscriptionCreate(BaseModel):
    """Request to create a new subscription (follow a trader)."""
    trader_id: UUID = Field(..., description="UUID of the trader profile to follow")
    allocation_percent: Decimal = Field(
        ..., 
        ge=1, 
        le=100, 
        description="Percentage of Bybit balance to allocate (1-100)"
    )
    copy_mode: CopyMode = Field(
        default=CopyMode.PROPORTIONAL,
        description="How to size copied trades"
    )
    is_shadow_mode: bool = Field(
        default=False,
        description="Paper trading mode - no real trades executed"
    )
    stop_loss_percent: Optional[Decimal] = Field(
        None, 
        ge=1, 
        le=50, 
        description="Auto-unsubscribe if losses exceed this percentage"
    )

    @field_validator('allocation_percent')
    @classmethod
    def validate_allocation(cls, v):
        if v <= 0:
            raise ValueError('Allocation must be greater than 0')
        if v > 100:
            raise ValueError('Allocation cannot exceed 100%')
        return v


class SubscriptionUpdate(BaseModel):
    """Request to update subscription settings."""
    allocation_percent: Optional[Decimal] = Field(None, ge=1, le=100)
    copy_mode: Optional[CopyMode] = None
    stop_loss_percent: Optional[Decimal] = Field(None, ge=1, le=50)


class SubscriptionPause(BaseModel):
    """Request to pause a subscription."""
    reason: Optional[str] = Field(None, max_length=255, description="Reason for pausing")


class SubscriptionResume(BaseModel):
    """Request to resume a paused subscription."""
    pass


class SubscriptionResponse(BaseModel):
    """Response model for subscription data."""
    sub_id: UUID
    subscriber_id: UUID
    trader_id: UUID
    tier_account_id: UUID
    sub_status: SubscriptionStatus
    copy_mode: CopyMode
    allocation_percent: Decimal
    reserved_amount: Decimal
    stop_loss_percent: Optional[Decimal]
    is_shadow_mode: bool
    virtual_pnl: Decimal
    created_at: datetime
    updated_at: datetime
    paused_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class SubscriptionWithTrader(SubscriptionResponse):
    """Subscription response with trader details included."""
    trader_alias: Optional[str] = None
    trader_performance_fee: Optional[Decimal] = None
    trader_min_capital: Optional[Decimal] = None


class SubscriptionStats(BaseModel):
    """Stats about a user's subscriptions."""
    active_count: int
    paused_count: int
    total_reserved: Decimal
    tier_limit: int
    remaining_slots: int


class TierInfoResponse(BaseModel):
    """User's current tier information."""
    tier_name: str
    max_follows: int
    current_follows: int
    remaining_slots: int
    expires_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
