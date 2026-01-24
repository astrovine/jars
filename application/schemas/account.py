from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
import re
import enum
from application.models.enums import SubscriptionTier, UserTier


class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    country: str = Field(..., min_length=2, max_length=100)
    phone_number: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=128)
    tier: SubscriptionTier = SubscriptionTier.FREE

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v):
        if not v.replace(' ', '').replace('-', '').isalpha():
            raise ValueError('Name must contain only letters, spaces, and hyphens')
        return v.strip()


class PlusUserCreate(UserCreate):
    date_of_birth: Optional[datetime] = None
    id_document_url: Optional[str] = Field(None, max_length=500)
    skip_kyc: bool = Field(default=True)


class BusinessUserCreate(UserCreate):
    date_of_birth: Optional[datetime] = None
    id_document_url: Optional[str] = Field(None, max_length=500)
    company_name: Optional[str] = Field(None, max_length=100)
    skip_kyc: bool = Field(default=True)


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    country: Optional[str] = Field(None, min_length=2, max_length=100)


class UserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    status: str
    country: Optional[str]
    is_active: bool
    is_2fa_enabled: bool
    tier: UserTier
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserFullResponse(UserResponse):
    kyc: Optional["KYCSummary"] = None
    trader_profile: Optional["TraderProfileSummary"] = None
    wallet_balance: Optional[Decimal] = None
    wallet_currency: Optional[str] = None
    wallet_active: Optional[bool] = None


class KYCSummary(BaseModel):
    status: str
    first_name: str
    last_name: str
    country: str

    model_config = ConfigDict(from_attributes=True)


class TraderProfileSummary(BaseModel):
    id: UUID
    alias: str
    is_active: bool
    performance_fee_percentage: float

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class LoginResponse(BaseModel):
    require_2fa: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    pre_auth_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    message: Optional[str] = None


UserFullResponse.model_rebuild()
