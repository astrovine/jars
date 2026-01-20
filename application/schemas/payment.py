from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class TierPricingResponse(BaseModel):
    exchange_rate: float
    plus: dict
    business: dict


class TierUpgradeResponse(BaseModel):
    reference: str
    authorization_url: str
    access_code: Optional[str] = None
    amount_ngn: float
    amount_usd: float
    exchange_rate: float


class PaymentVerifyResponse(BaseModel):
    status: str
    amount: float
    reference: str
    gateway_response: Optional[str] = None


class BanksListResponse(BaseModel):
    banks: list
