from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class RefreshTokenBase(BaseModel):
    token: str
    is_revoked: bool = False
    expires_at: datetime

class RefreshTokenCreate(RefreshTokenBase):
    user_id: UUID
    jti: UUID

class RefreshTokenResponse(RefreshTokenBase):
    jti: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

