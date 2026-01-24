import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from application.models.domain_events import DomainEvent, EventType, AggregateType
from application.utilities.audit import setup_logger

logger = setup_logger(__name__)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, 'value'):  # Enum
        return value.value
    return value


def _serialize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: _serialize_value(v) for k, v in data.items() if v is not None}


class EventStore:
    
    @staticmethod
    async def publish(
        db: AsyncSession,
        event_type: EventType,
        aggregate_type: AggregateType,
        aggregate_id: uuid.UUID,
        payload: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[uuid.UUID] = None,
        causation_id: Optional[uuid.UUID] = None,
    ) -> DomainEvent:
        """
        Publish a domain event to the event store
        
        Args:
            db: Database session
            event_type: Type of event (like SUBSCRIPTION_CREATED)
            aggregate_type: Type of aggregate (SUBSCRIPTION etc)
            aggregate_id: ID of the aggregate
            payload: Full state snapshot
            user_id: User who triggered the event
            metadata: Request metadata (IP, user_agent, etc)
            correlation_id: Groups related events together
            causation_id: The event that caused this event, "event causing event" you get it?
        """
        event = DomainEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            user_id=user_id,
            payload=_serialize_payload(payload),
            metadata=_serialize_payload(metadata) if metadata else None,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        
        db.add(event)
        await db.flush()
        
        logger.info(
            f"[EVENT] {event_type.value} | "
            f"Aggregate: {aggregate_type.value}:{aggregate_id} | "
            f"User: {user_id}"
        )
        
        return event
    
    @staticmethod
    async def publish_subscription_created(
        db: AsyncSession,
        subscription_id: uuid.UUID,
        user_id: uuid.UUID,
        trader_id: uuid.UUID,
        allocation_percent: Decimal,
        reserved_amount: Decimal,
        is_shadow_mode: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DomainEvent:
        return await EventStore.publish(
            db=db,
            event_type=EventType.SUBSCRIPTION_CREATED,
            aggregate_type=AggregateType.SUBSCRIPTION,
            aggregate_id=subscription_id,
            user_id=user_id,
            payload={
                "subscription_id": subscription_id,
                "subscriber_id": user_id,
                "trader_id": trader_id,
                "allocation_percent": allocation_percent,
                "reserved_amount": reserved_amount,
                "is_shadow_mode": is_shadow_mode,
                "status": "active",
            },
            metadata={
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.now(timezone.utc),
            }
        )
    
    @staticmethod
    async def publish_subscription_paused(
        db: AsyncSession,
        subscription_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> DomainEvent:
        return await EventStore.publish(
            db=db,
            event_type=EventType.SUBSCRIPTION_PAUSED,
            aggregate_type=AggregateType.SUBSCRIPTION,
            aggregate_id=subscription_id,
            user_id=user_id,
            payload={
                "subscription_id": subscription_id,
                "reason": reason,
                "status": "paused",
            },
            metadata={"ip_address": ip_address}
        )
    
    @staticmethod
    async def publish_subscription_resumed(
        db: AsyncSession,
        subscription_id: uuid.UUID,
        user_id: uuid.UUID,
        new_reserved_amount: Decimal,
        ip_address: Optional[str] = None,
    ) -> DomainEvent:
        return await EventStore.publish(
            db=db,
            event_type=EventType.SUBSCRIPTION_RESUMED,
            aggregate_type=AggregateType.SUBSCRIPTION,
            aggregate_id=subscription_id,
            user_id=user_id,
            payload={
                "subscription_id": subscription_id,
                "reserved_amount": new_reserved_amount,
                "status": "active",
            },
            metadata={"ip_address": ip_address}
        )
    
    @staticmethod
    async def publish_subscription_cancelled(
        db: AsyncSession,
        subscription_id: uuid.UUID,
        user_id: uuid.UUID,
        released_amount: Decimal,
        ip_address: Optional[str] = None,
    ) -> DomainEvent:
        return await EventStore.publish(
            db=db,
            event_type=EventType.SUBSCRIPTION_CANCELLED,
            aggregate_type=AggregateType.SUBSCRIPTION,
            aggregate_id=subscription_id,
            user_id=user_id,
            payload={
                "subscription_id": subscription_id,
                "released_amount": released_amount,
                "status": "inactive",
            },
            metadata={"ip_address": ip_address}
        )
    
    @staticmethod
    async def publish_payment_completed(
        db: AsyncSession,
        payment_id: uuid.UUID,
        user_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        reference: str,
        provider: str = "paystack",
    ) -> DomainEvent:
        return await EventStore.publish(
            db=db,
            event_type=EventType.PAYMENT_COMPLETED,
            aggregate_type=AggregateType.PAYMENT,
            aggregate_id=payment_id,
            user_id=user_id,
            payload={
                "payment_id": payment_id,
                "amount": amount,
                "currency": currency,
                "reference": reference,
                "provider": provider,
                "status": "completed",
            }
        )

    @staticmethod
    async def get_events_for_aggregate(
        db: AsyncSession,
        aggregate_type: AggregateType,
        aggregate_id: uuid.UUID,
        limit: int = 100
    ) -> List[DomainEvent]:
        result = await db.execute(
            select(DomainEvent)
            .filter(
                DomainEvent.aggregate_type == aggregate_type,
                DomainEvent.aggregate_id == aggregate_id
            )
            .order_by(desc(DomainEvent.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_user_audit_trail(
        db: AsyncSession,
        user_id: uuid.UUID,
        event_types: Optional[List[EventType]] = None,
        limit: int = 100
    ) -> List[DomainEvent]:
        """Get audit trail for any user , cause I might get asked 'what did this user do?'"""
        query = select(DomainEvent).filter(DomainEvent.user_id == user_id)
        
        if event_types:
            query = query.filter(DomainEvent.event_type.in_(event_types))
        
        result = await db.execute(
            query.order_by(desc(DomainEvent.created_at)).limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_events_by_type(
        db: AsyncSession,
        event_type: EventType,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[DomainEvent]:
        query = select(DomainEvent).filter(DomainEvent.event_type == event_type)
        
        if since:
            query = query.filter(DomainEvent.created_at >= since)
        
        result = await db.execute(
            query.order_by(desc(DomainEvent.created_at)).limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_correlated_events(
        db: AsyncSession,
        correlation_id: uuid.UUID
    ) -> List[DomainEvent]:
        result = await db.execute(
            select(DomainEvent)
            .filter(DomainEvent.correlation_id == correlation_id)
            .order_by(DomainEvent.created_at)
        )
        return list(result.scalars().all())
