import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, func, Enum, Index, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base
from .enums import TransactionType, AccountType, EntryDirection, TransactionStatus

class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(Enum(AccountType, native_enum=True, name="account_type"), nullable=False)
    name = Column(String(100), nullable=True)
    currency = Column(String(3), default="NGN", nullable=False)

    balance = Column(Numeric(precision=20, scale=8), default=0, nullable=False)
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="accounts")
    entries = relationship("LedgerEntry", back_populates="account")

class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_id = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(Enum(TransactionType, native_enum=True, name="transaction_type"), nullable=False, index=True)
    status = Column(Enum(TransactionStatus, native_enum=True, name="transaction_status"), default=TransactionStatus.PENDING, nullable=False)
    amount = Column(Numeric(precision=20, scale=8), nullable=False)
    currency = Column(String(3), default="NGN", nullable=False)
    description = Column(String(255), nullable=True)
    external_reference = Column(String(255), nullable=True, index=True)
    tx_metadata = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    entries = relationship("LedgerEntry", back_populates="transaction", cascade="all, delete-orphan")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    transaction_id = Column(UUID(as_uuid=True), ForeignKey("ledger_transactions.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    direction = Column(Enum(EntryDirection, native_enum=True, name="entry_direction"), nullable=False)

    amount = Column(Numeric(precision=20, scale=8), nullable=False)
    balance_after = Column(Numeric(precision=20, scale=8), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    transaction = relationship("LedgerTransaction", back_populates="entries")
    account = relationship("Account", back_populates="entries")

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    currency_pair = Column(String, default="USD-NGN")
    rate = Column(Numeric(12, 4), nullable=False)
    source = Column(String, default="openexchangerates.org")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)