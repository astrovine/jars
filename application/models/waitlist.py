from sqlalchemy import Column, String, DateTime
from application.models.base import Base
import uuid
from datetime import datetime

class WaitlistEntry(Base):
    __tablename__ = "waitlist"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
