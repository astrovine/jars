from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from application.models.enums import TransactionType, AccountType


class LedgerEntryBase(BaseModel):
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    reference_id: Optional[UUID] = None
    description: Optional[str] = None
    balance_after: Decimal


class LedgerEntryCreate(BaseModel):
    user_id: UUID
    amount: Decimal = Field(..., ne=0)
    currency: str = Field(..., min_length=2, max_length=10)
    transaction_type: TransactionType
    reference_id: Optional[UUID] = None
    description: Optional[str] = Field(None, max_length=255)
    balance_after: Decimal


class LedgerEntryResponse(BaseModel):
    id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    reference_id: Optional[UUID]
    description: Optional[str]
    balance_after: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BalanceResponse(BaseModel):
    user_id: UUID
    currency: str
    balance: Decimal


class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="NGN", min_length=2, max_length=10)
    callback_url: Optional[str] = None
    description: Optional[str] = Field(None, max_length=255)


class WithdrawalRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., min_length=2, max_length=10)
    description: Optional[str] = Field(None, max_length=255)


class LedgerSummary(BaseModel):
    total_deposits: Decimal
    total_withdrawals: Decimal
    total_fees_paid: Decimal
    total_profits: Decimal
    current_balance: Decimal


class CreatNewAccount(BaseModel):
    currency: str = "NGN"
    type: AccountType = AccountType.USER_DEMO_WALLET
    is_active: bool = False


class NewAccountResponse(BaseModel):
    id: UUID
    currency: str
    type: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class WalletInfo(BaseModel):
    user_id: UUID
    currency: str
    balance: Decimal
    is_active: bool = True


class WalletSummary(BaseModel):
    user_id: UUID
    currency: str
    balance: Decimal
    total_deposits: Decimal
    total_withdrawals: Decimal
    pending_amount: Decimal = Decimal("0")


class DepositInitResponse(BaseModel):
    authorization_url: str
    access_code: str
    reference: str


class TransactionHistoryResponse(BaseModel):
    entries: List[LedgerEntryResponse]
    total: int
    limit: int
    offset: int
