from decimal import Decimal
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field


class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, le=1000000, description="Amount in Naira (min: 100, max: 1,000,000)")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 5000.00
            }
        }


class DepositResponse(BaseModel):
    reference: str
    authorization_url: str
    access_code: str

    class Config:
        json_schema_extra = {
            "example": {
                "reference": "dep_abc123_def456",
                "authorization_url": "https://checkout.paystack.com/xxx",
                "access_code": "xxx"
            }
        }


class DepositVerifyResponse(BaseModel):
    status: str
    reference: str
    amount: Optional[Decimal] = None
    message: str


class BalanceResponse(BaseModel):
    balance: Decimal
    currency: str = "NGN"
    account_id: UUID
    is_active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "balance": 15000.00,
                "currency": "NGN",
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_active": True
            }
        }


class TransactionHistoryItem(BaseModel):
    id: UUID
    transaction_id: UUID
    direction: str
    amount: Decimal
    balance_after: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionDetail(BaseModel):
    id: UUID
    reference_id: str
    type: str
    status: str
    amount: Decimal
    currency: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TransactionHistoryResponse(BaseModel):
    transactions: List[TransactionHistoryItem]
    total: int
    limit: int
    offset: int


class WalletSummary(BaseModel):
    balance: Decimal
    currency: str
    total_deposits: Decimal
    total_fees_paid: Decimal
    pending_transactions: int

