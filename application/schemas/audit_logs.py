from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID

class AuditLogBase(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    changes: Optional[str] = None
    extra_data: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    user_id: UUID
    trader_profile_id: Optional[UUID] = None

class AuditLogResponse(AuditLogBase):
    id: int
    user_id: UUID
    trader_profile_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

