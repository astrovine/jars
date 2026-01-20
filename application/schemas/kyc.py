from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from application.models.kyc import VerificationStatus


class KYCCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    country: str = Field(..., min_length=2, max_length=2)
    date_of_birth: Optional[date] = None
    id_document_url: Optional[str] = Field(None, max_length=500)
    past_trades: Optional[str] = Field(None, max_length=1000)

    @field_validator('country')
    @classmethod
    def validate_country(cls, v):
        return v.upper()


class KYCUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    date_of_birth: Optional[date] = None
    id_document_url: Optional[str] = Field(None, max_length=500)
    past_trades: Optional[str] = Field(None, max_length=1000)


class KYCAdminUpdate(BaseModel):
    status: VerificationStatus
    rejection_reason: Optional[str] = Field(None, max_length=500)


class KYCRejection(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class KYCResponse(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    country: str
    date_of_birth: Optional[date]
    id_document_url: Optional[str]
    past_trades: Optional[str]
    status: VerificationStatus
    rejection_reason: Optional[str]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
