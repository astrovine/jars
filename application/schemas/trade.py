from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from application.models.enums import TradeStatus, OrderSide

class TradeBase(BaseModel):
    signal_id: UUID
    subscription_id: UUID
    exchange_key_id: Optional[UUID] = None
    binance_order_id: Optional[str] = None
    status: TradeStatus = TradeStatus.PENDING
    side: OrderSide
    requested_amount: Decimal
    filled_amount: Optional[Decimal] = None
    filled_price: Optional[Decimal] = None
    fee_paid: Optional[Decimal] = None
    fee_currency: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: Optional[int] = None

class TradeCreate(BaseModel):
    signal_id: UUID
    subscription_id: UUID
    exchange_key_id: Optional[UUID] = None
    side: OrderSide
    requested_amount: Decimal = Field(..., gt=0)

class TradeUpdate(BaseModel):
    status: Optional[TradeStatus] = None
    binance_order_id: Optional[str] = None
    filled_amount: Optional[Decimal] = None
    filled_price: Optional[Decimal] = None
    fee_paid: Optional[Decimal] = None
    fee_currency: Optional[str] = None
    realized_pnl: Optional[Decimal] = None
    error_message: Optional[str] = Field(None, max_length=500)
    latency_ms: Optional[int] = None

class TradeResponse(BaseModel):
    id: UUID
    signal_id: UUID
    subscription_id: UUID
    exchange_key_id: Optional[UUID]
    binance_order_id: Optional[str]
    status: TradeStatus
    side: OrderSide
    requested_amount: Decimal
    filled_amount: Optional[Decimal]
    filled_price: Optional[Decimal]
    fee_paid: Optional[Decimal]
    fee_currency: Optional[str]
    realized_pnl: Optional[Decimal]
    error_message: Optional[str]
    latency_ms: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TradeExecutionResult(BaseModel):
    trade_id: UUID
    status: TradeStatus
    binance_order_id: Optional[str] = None
    filled_amount: Optional[Decimal] = None
    filled_price: Optional[Decimal] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None

class TradeSummary(BaseModel):
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_volume: Decimal
    total_pnl: Decimal
