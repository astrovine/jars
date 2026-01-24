from sqlalchemy import Column, String, Date, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
from sqlalchemy.orm import relationship

from .enums import VerificationStatus


class UserKYC(Base):
    __tablename__ = "user_kyc"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    country = Column(String(2), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    id_document_url = Column(String, nullable=True)
    status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    past_trades = Column(String, nullable=True)
    rejection_reason = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="kyc")