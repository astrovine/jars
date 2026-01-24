from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
import re


class TraderProfileCreate(BaseModel):
    alias: str = Field(..., min_length=3, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    performance_fee_percentage: Decimal = Field(default=Decimal("20.00"), ge=0, le=50)
    min_allocation_amount: Decimal = Field(default=Decimal("72700.26"), ge=0)

    @field_validator('alias')
    @classmethod
    def validate_alias(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Alias must contain only letters, numbers, and underscores')
        return v.lower()


class TraderProfileUpdate(BaseModel):
    bio: Optional[str] = Field(None, max_length=500)
    performance_fee_percentage: Optional[Decimal] = Field(None, ge=0, le=50)
    min_allocation_amount: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class TraderProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    alias: str
    bio: Optional[str]
    performance_fee_percentage: Decimal
    min_allocation_amount: Decimal
    is_active: bool
    stats_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TraderProfilePublic(BaseModel):
    id: UUID
    alias: str
    bio: Optional[str]
    performance_fee_percentage: Decimal
    min_allocation_amount: Decimal
    is_active: bool
    stats_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TraderStatsUpdate(BaseModel):
    roi: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: Optional[int] = None
    followers: Optional[int] = None
    total_pnl: Optional[Decimal] = None
