from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class VirtualWalletStatusResponse(BaseModel):
    current_balance: Decimal
    is_blown: bool
    free_reset_available: bool
    free_reset_date: datetime | None
    days_since_last_reset: int | None
    paid_reset_cost_usd: Decimal

    class Config:
        from_attributes = True


class VirtualBalanceResetResponse(BaseModel):
    message: str
    new_balance: Decimal
    reset_type: str
    transaction_reference: str
