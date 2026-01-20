from sqlalchemy import Column, String, ForeignKey, Boolean, LargeBinary, DateTime, Index, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base
from sqlalchemy.orm import relationship



class ExchangeKey(Base):
    __tablename__ = "exchange_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange_name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    api_secret_encrypted = Column(LargeBinary, nullable=False)
    is_valid = Column(Boolean, default=True)
    label = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="exchange_keys")

    __table_args__ = (
        Index('idx_user_exchange', 'user_id', 'exchange_name'),
        Index('idx_user_key', 'user_id', 'api_key'),
    )