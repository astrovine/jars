from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from application.models.enums import OrderSide, OrderType


class SignalCreate(BaseModel):
    leader_profile_id: UUID
    symbol: str = Field(..., min_length=1, max_length=20)
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    raw_exchange_response: Optional[Dict[str, Any]] = None
    emitted_at: datetime

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        return v.upper().strip()


class SignalResponse(BaseModel):
    id: UUID
    leader_profile_id: UUID
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal
    raw_exchange_response: Optional[Dict[str, Any]] = None
    emitted_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SignalPublic(BaseModel):
    id: UUID
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal
    emitted_at: datetime

    model_config = ConfigDict(from_attributes=True)
