from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from application.models.base import get_db
from application.models.account import User
from application.models.enums import CopyMode
from application.schemas import subscription as sub_schema
from application.services.sub_service import SubscriptionService
from application.services.event_store import EventStore
from application.utilities import oauth2 as o2
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger, log_user_action

logger = setup_logger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post(
    "/follow",
    response_model=sub_schema.SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Follow a trader",
    description="Create a new subscription to copy a trader's trades. Validates tier limits and capital requirements."
)
async def follow_trader(
    sub_data: sub_schema.SubscriptionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(
        f"[FOLLOW] Request | User: {current_user.id} | Trader: {sub_data.trader_id} | "
        f"Allocation: {sub_data.allocation_percent}% | Shadow: {sub_data.is_shadow_mode} | IP: {ip_address}"
    )
    
    try:
        subscription = await SubscriptionService.create_subscription(
            db=db,
            subscriber_id=current_user.id,
            trader_id=sub_data.trader_id,
            allocation_percent=sub_data.allocation_percent,
            copy_mode=sub_data.copy_mode,
            is_shadow_mode=sub_data.is_shadow_mode,
            stop_loss_percent=sub_data.stop_loss_percent,
            testnet=False
        )
        
        await log_user_action(
            db=db,
            user_id=str(current_user.id),
            action="SUBSCRIPTION_CREATED",
            resource_type="SUBSCRIPTION",
            resource_id=str(subscription.sub_id),
            trader_profile_id=str(sub_data.trader_id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "allocation_percent": str(sub_data.allocation_percent),
                "reserved_amount": str(subscription.reserved_amount),
                "is_shadow_mode": sub_data.is_shadow_mode,
                "copy_mode": sub_data.copy_mode.value,
            }
        )
        await EventStore.publish_subscription_created(
            db=db,
            subscription_id=subscription.sub_id,
            user_id=current_user.id,
            trader_id=sub_data.trader_id,
            allocation_percent=sub_data.allocation_percent,
            reserved_amount=subscription.reserved_amount,
            is_shadow_mode=sub_data.is_shadow_mode,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
        )
        
        await db.commit()
        
        logger.info(f"[FOLLOW SUCCESS] Subscription: {subscription.sub_id} | Reserved: ${subscription.reserved_amount}")
        return subscription
        
    except es.SubscriptionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except es.UpgradeRequiredError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except es.TraderProfileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader not found")
    except es.TraderNotActiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except es.SelfSubscriptionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except es.SubscriptionAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except es.InsufficientCapitalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except es.APIKeyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please connect your Bybit account before following traders"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"[FOLLOW FAILED] User: {current_user.id} | Error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create subscription")


@router.delete(
    "/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a trader",
    description="Cancel subscription and release reserved funds"
)
async def unfollow_trader(
    subscription_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[UNFOLLOW] Request | Sub: {subscription_id} | User: {current_user.id} | IP: {ip_address}")
    
    try:
        subscription = await SubscriptionService.cancel_subscription(
            db=db,
            subscription_id=subscription_id,
            user_id=current_user.id
        )
        
        await log_user_action(
            db=db,
            user_id=str(current_user.id),
            action="SUBSCRIPTION_CANCELLED",
            resource_type="SUBSCRIPTION",
            resource_id=str(subscription_id),
            trader_profile_id=str(subscription.trader_id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
        )
        
        # Publish audit event
        await EventStore.publish_subscription_cancelled(
            db=db,
            subscription_id=subscription_id,
            user_id=current_user.id,
            released_amount=subscription.reserved_amount,
            ip_address=ip_address,
        )
        await db.commit()
        
        logger.info(f"[UNFOLLOW SUCCESS] Sub: {subscription_id}")
        return None
        
    except es.SubscriptionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    except es.SubscriptionNotActiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post(
    "/{subscription_id}/pause",
    response_model=sub_schema.SubscriptionResponse,
    summary="Pause subscription",
    description="Temporarily stop copying trades. Open positions are NOT affected."
)
async def pause_subscription(
    subscription_id: uuid.UUID,
    pause_data: sub_schema.SubscriptionPause,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(o2.get_current_user)
):
    """Whoever that reads this, please note that this doesn't stop open trades or current position it only halts copying any new trades"""
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[PAUSE] Request | Sub: {subscription_id} | User: {current_user.id} | Reason: {pause_data.reason}")
    
    try:
        subscription = await SubscriptionService.pause_subscription(
            db=db,
            subscription_id=subscription_id,
            user_id=current_user.id,
            reason=pause_data.reason
        )
        
        await log_user_action(
            db=db,
            user_id=str(current_user.id),
            action="SUBSCRIPTION_PAUSED",
            resource_type="SUBSCRIPTION",
            resource_id=str(subscription_id),
            trader_profile_id=str(subscription.trader_id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"reason": pause_data.reason}
        )

        await EventStore.publish_subscription_paused(
            db=db,
            subscription_id=subscription_id,
            user_id=current_user.id,
            reason=pause_data.reason,
            ip_address=ip_address,
        )
        
        await db.commit()
        
        logger.info(f"[PAUSE SUCCESS] Sub: {subscription_id}")
        return subscription
        
    except es.SubscriptionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    except es.SubscriptionNotActiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{subscription_id}/resume",
    response_model=sub_schema.SubscriptionResponse,
    summary="Resume subscription",
    description="Resume copying trades. Re-validates capital requirements."
)
async def resume_subscription(
    subscription_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[RESUME] Request | Sub: {subscription_id} | User: {current_user.id}")
    
    try:
        subscription = await SubscriptionService.resume_subscription(
            db=db,
            subscription_id=subscription_id,
            user_id=current_user.id,
            testnet=False
        )
        
        await log_user_action(
            db=db,
            user_id=str(current_user.id),
            action="SUBSCRIPTION_RESUMED",
            resource_type="SUBSCRIPTION",
            resource_id=str(subscription_id),
            trader_profile_id=str(subscription.trader_id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
        )
        await EventStore.publish_subscription_resumed(
            db=db,
            subscription_id=subscription_id,
            user_id=current_user.id,
            new_reserved_amount=subscription.reserved_amount,
            ip_address=ip_address,
        )
        
        await db.commit()
        
        logger.info(f"[RESUME SUCCESS] Sub: {subscription_id}")
        return subscription
        
    except es.SubscriptionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    except es.SubscriptionNotActiveError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except es.InsufficientCapitalError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume: {str(e)}"
        )

@router.get(
    "",
    response_model=List[sub_schema.SubscriptionResponse],
    summary="List my subscriptions",
    description="Get all subscriptions for the current user"
)
async def get_my_subscriptions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(o2.get_current_user),
    active_only: bool = True
):
    subscriptions = await SubscriptionService.get_user_subscriptions(
        db=db,
        user_id=current_user.id,
        active_only=active_only
    )
    logger.debug(f"[LIST] Returned {len(subscriptions)} subscriptions for user {current_user.id}")
    return subscriptions


@router.get(
    "/as-trader",
    response_model=List[sub_schema.SubscriptionResponse],
    summary="List my subscribers",
    description="Get all users subscribed to you"
)
async def get_my_subscribers(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(o2.get_current_user),
    active_only: bool = True
):
    if not current_user.trader_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have a trader profile")
    
    subscriptions = await SubscriptionService.get_trader_subscribers(
        db=db,
        trader_id=current_user.trader_profile.id,
        active_only=active_only
    )
    logger.debug(f"[SUBSCRIBERS] Returned {len(subscriptions)} for trader {current_user.trader_profile.id}")
    return subscriptions


@router.get(
    "/{subscription_id}",
    response_model=sub_schema.SubscriptionResponse,
    summary="Get subscription details"
)
async def get_subscription(
    subscription_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(o2.get_current_user)
):
    subscription = await SubscriptionService.get_subscription_by_id(
        db=db,
        subscription_id=subscription_id,
        user_id=current_user.id
    )
    
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    return subscription


@router.get(
    "/tier/info",
    response_model=sub_schema.TierInfoResponse,
    summary="Get my tier info",
    description="Get current tier subscription details and remaining slots"
)
async def get_tier_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(o2.get_current_user)
):
    try:
        tier_account, current_count, max_follows = await SubscriptionService.validate_tier_limit(
            db=db,
            user_id=current_user.id
        )
        
        return sub_schema.TierInfoResponse(
            tier_name=tier_account.tier.tier_name.value,
            max_follows=max_follows,
            current_follows=current_count,
            remaining_slots=max_follows - current_count,
            expires_at=tier_account.subscription_expires_at,
            is_active=True
        )
        
    except es.SubscriptionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except es.UpgradeRequiredError:
        # User has a tier but is at limit, still return info
        tier_account, current_count, max_follows = await SubscriptionService.validate_tier_limit.__wrapped__(
            db=db,
            user_id=current_user.id
        )
        return sub_schema.TierInfoResponse(
            tier_name=tier_account.tier.tier_name.value,
            max_follows=max_follows,
            current_follows=current_count,
            remaining_slots=0,
            expires_at=tier_account.subscription_expires_at,
            is_active=True
        )
