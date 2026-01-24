from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from uuid import UUID
import re

class ExchangeKeyCreate(BaseModel):
    exchange_name: str = Field(..., min_length=2, max_length=50)
    api_key: str = Field(..., min_length=10, max_length=256)
    api_secret: str = Field(..., min_length=10, max_length=256)
    label: Optional[str] = Field(None, max_length=100)

    @field_validator('exchange_name')
    @classmethod
    def validate_exchange(cls, v):
        allowed = ['binance', 'bybit', 'okx']
        if v.lower() not in allowed:
            raise ValueError(f'Exchange must be one of: {", ".join(allowed)}')
        return v.lower()

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('API key contains invalid characters')
        return v


class ExchangeKeyUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=100)
    is_valid: Optional[bool] = None


class ExchangeKeyResponse(BaseModel):
    id: UUID
    user_id: UUID
    exchange_name: str
    api_key: str
    label: Optional[str]
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)


class ExchangeKeyTestResult(BaseModel):
    is_valid: bool
    can_trade: bool
    can_withdraw: bool
    message: str
