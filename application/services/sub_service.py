"""
Subscription Service

Features:
- Tier enforcement (max follows per tier)
- Whale validator (minimum capital requirements)
- Shadow balance (fund reservation)
- Shadow mode (paper trading)
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple, Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.models.subscription import Subscription, SubscriptionTierAccounts, TradingTiers
from application.models.trader_profile import TraderProfile
from application.models.account import User
from application.models.enums import (
    SubscriptionStatus, 
    SubscriptionTierStatus, 
    TraderProfileStatus,
    CopyMode
)
from application.services.bybit_service import BybitService, BYBIT_MIN_ORDER_SIZE
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger

logger = setup_logger(__name__)


class SubscriptionService:
    @staticmethod
    async def validate_tier_limit(
        db: AsyncSession, 
        user_id: uuid.UUID
    ) -> Tuple[SubscriptionTierAccounts, int, int]:
        result = await db.execute(
            select(SubscriptionTierAccounts)
            .options(selectinload(SubscriptionTierAccounts.tier))
            .filter(
                SubscriptionTierAccounts.user_id == user_id,
                SubscriptionTierAccounts.tier_status.in_([
                    SubscriptionTierStatus.ACTIVE, 
                    SubscriptionTierStatus.RENEWED
                ])
            )
        )
        tier_account = result.scalar_one_or_none()
        
        if not tier_account:
            logger.warning(f"User {user_id} has no active tier subscription")
            raise es.SubscriptionNotFoundError("No active tier subscription. Please subscribe to a tier first.")
        if tier_account.subscription_expires_at < datetime.now(timezone.utc):
            logger.warning(f"User {user_id} tier has expired")
            tier_account.tier_status = SubscriptionTierStatus.EXPIRED
            await db.flush()
            raise es.SubscriptionNotFoundError("Your tier subscription has expired. Please renew.")
        count_result = await db.execute(
            select(func.count()).select_from(Subscription).filter(
                Subscription.subscriber_id == user_id,
                Subscription.sub_status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED])
            )
        )
        current_count = count_result.scalar() or 0
        max_follows = int(tier_account.tier.max_follows)
        
        if current_count >= max_follows:
            logger.warning(f"User {user_id} at max follows: {current_count}/{max_follows}")
            raise es.UpgradeRequiredError(
                f"You've reached your tier limit of {max_follows} traders. "
                "Upgrade your tier to follow more traders."
            )
        
        logger.info(f"User {user_id} tier validated: {current_count}/{max_follows} follows")
        return tier_account, current_count, max_follows
    
    @staticmethod
    async def validate_trader(
        db: AsyncSession, 
        trader_id: uuid.UUID, 
        follower_id: uuid.UUID
    ) -> TraderProfile:
        result = await db.execute(
            select(TraderProfile).filter(TraderProfile.id == trader_id)
        )
        trader = result.scalar_one_or_none()
        
        if not trader:
            logger.error(f"Trader {trader_id} not found")
            raise es.TraderProfileNotFoundError()
        
        if trader.status != TraderProfileStatus.ACTIVE:
            logger.warning(f"Trader {trader_id} is not active: {trader.status}")
            raise es.TraderNotActiveError("This trader is not currently accepting followers.")
        
        if trader.user_id == follower_id:
            logger.warning(f"User {follower_id} tried to follow themselves")
            raise es.SelfSubscriptionError("You literary cannot follow yourself, Lmao")
        
        return trader
    
    @staticmethod
    async def validate_capital_requirements(
        db: AsyncSession,
        user_id: uuid.UUID,
        allocation_percent: Decimal,
        min_capital_required: Decimal,
        testnet: bool = False
    ) -> Tuple[bool, Decimal]:

        is_valid, allocated_amount, reason = await BybitService.validate_trading_capital(
            db, user_id, allocation_percent, min_capital_required, testnet
        )
        
        if not is_valid:
            logger.warning(f"User {user_id} failed capital validation: {reason}")
            raise es.InsufficientCapitalError(reason)
        
        return is_valid, allocated_amount
    
    @staticmethod
    async def check_existing_subscription(
        db: AsyncSession,
        subscriber_id: uuid.UUID,
        trader_id: uuid.UUID
    ) -> Optional[Subscription]:
        result = await db.execute(
            select(Subscription).filter(
                Subscription.subscriber_id == subscriber_id,
                Subscription.trader_id == trader_id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        subscriber_id: uuid.UUID,
        trader_id: uuid.UUID,
        allocation_percent: Decimal,
        copy_mode: CopyMode = CopyMode.PROPORTIONAL,
        is_shadow_mode: bool = False,
        stop_loss_percent: Optional[Decimal] = None,
        testnet: bool = False
    ) -> Subscription:
        logger.info(f"Creating subscription: user={subscriber_id}, trader={trader_id}, allocation={allocation_percent}%")

        tier_account, current_count, max_follows = await SubscriptionService.validate_tier_limit(
            db, subscriber_id
        )
        trader = await SubscriptionService.validate_trader(db, trader_id, subscriber_id)

        existing = await SubscriptionService.check_existing_subscription(db, subscriber_id, trader_id)
        if existing:
            if existing.sub_status == SubscriptionStatus.INACTIVE:
                logger.info(f"Reactivating existing subscription {existing.sub_id}")
                return await SubscriptionService.reactivate_subscription(
                    db, existing, allocation_percent, copy_mode, is_shadow_mode, stop_loss_percent, testnet
                )
            else:
                logger.warning(f"User {subscriber_id} already subscribed to trader {trader_id}")
                raise es.SubscriptionAlreadyExistsError("You are already following this trader.")

        reserved_amount = Decimal('0')
        if not is_shadow_mode:
            _, reserved_amount = await SubscriptionService.validate_capital_requirements(
                db, subscriber_id, allocation_percent, trader.min_capital_requirement, testnet
            )

        new_subscription = Subscription(
            subscriber_id=subscriber_id,
            trader_id=trader_id,
            tier_account_id=tier_account.id,
            sub_status=SubscriptionStatus.ACTIVE,
            copy_mode=copy_mode,
            allocation_percent=allocation_percent,
            reserved_amount=reserved_amount,
            stop_loss_percent=stop_loss_percent,
            is_shadow_mode=is_shadow_mode,
            virtual_pnl=Decimal('0'),
        )
        
        db.add(new_subscription)
        await db.flush()
        await db.refresh(new_subscription)
        
        logger.info(
            f"Subscription created: {new_subscription.sub_id} | "
            f"User: {subscriber_id} -> Trader: {trader.alias} | "
            f"Reserved: ${reserved_amount:.2f} | Shadow: {is_shadow_mode}"
        )
        
        return new_subscription
    
    @staticmethod
    async def reactivate_subscription(
        db: AsyncSession,
        subscription: Subscription,
        allocation_percent: Decimal,
        copy_mode: CopyMode,
        is_shadow_mode: bool,
        stop_loss_percent: Optional[Decimal],
        testnet: bool = False
    ) -> Subscription:
        reserved_amount = Decimal('0')
        if not is_shadow_mode:
            result = await db.execute(
                select(TraderProfile).filter(TraderProfile.id == subscription.trader_id)
            )
            trader = result.scalar_one()
            _, reserved_amount = await SubscriptionService.validate_capital_requirements(
                db, subscription.subscriber_id, allocation_percent, 
                trader.min_capital_requirement, testnet
            )
        
        subscription.sub_status = SubscriptionStatus.ACTIVE
        subscription.allocation_percent = allocation_percent
        subscription.copy_mode = copy_mode
        subscription.is_shadow_mode = is_shadow_mode
        subscription.stop_loss_percent = stop_loss_percent
        subscription.reserved_amount = reserved_amount
        subscription.paused_at = None
        
        await db.flush()
        await db.refresh(subscription)
        
        logger.info(f"Subscription reactivated: {subscription.sub_id}")
        return subscription
    
    @staticmethod
    async def pause_subscription(
        db: AsyncSession,
        subscription_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> Subscription:
        """
        Pause a subscription. They don't copy new trades
        """
        result = await db.execute(
            select(Subscription).filter(
                Subscription.sub_id == subscription_id,
                Subscription.subscriber_id == user_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise es.SubscriptionNotFoundError()
        
        if subscription.sub_status == SubscriptionStatus.PAUSED:
            raise es.SubscriptionNotActiveError("Subscription is already paused.")
        
        if subscription.sub_status != SubscriptionStatus.ACTIVE:
            raise es.SubscriptionNotActiveError("Can only pause active subscriptions.")
        
        subscription.sub_status = SubscriptionStatus.PAUSED
        subscription.paused_at = datetime.now(timezone.utc)
        
        await db.flush()
        await db.refresh(subscription)
        
        logger.info(f"Subscription paused: {subscription_id} | Reason: {reason or 'Not specified'}")
        return subscription
    
    @staticmethod
    async def resume_subscription(
        db: AsyncSession,
        subscription_id: uuid.UUID,
        user_id: uuid.UUID,
        testnet: bool = False
    ) -> Subscription:
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.trader_profile))
            .filter(
                Subscription.sub_id == subscription_id,
                Subscription.subscriber_id == user_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise es.SubscriptionNotFoundError()
        
        if subscription.sub_status != SubscriptionStatus.PAUSED:
            raise es.SubscriptionNotActiveError("Can only resume paused subscriptions.")

        if not subscription.is_shadow_mode:
            _, reserved_amount = await SubscriptionService.validate_capital_requirements(
                db, user_id, subscription.allocation_percent,
                subscription.trader_profile.min_capital_requirement, testnet
            )
            subscription.reserved_amount = reserved_amount
        
        subscription.sub_status = SubscriptionStatus.ACTIVE
        subscription.paused_at = None
        
        await db.flush()
        await db.refresh(subscription)
        
        logger.info(f"Subscription resumed: {subscription_id}")
        return subscription
    
    @staticmethod
    async def cancel_subscription(
        db: AsyncSession,
        subscription_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Subscription:
        result = await db.execute(
            select(Subscription).filter(
                Subscription.sub_id == subscription_id,
                Subscription.subscriber_id == user_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise es.SubscriptionNotFoundError()
        
        if subscription.sub_status == SubscriptionStatus.INACTIVE:
            raise es.SubscriptionNotActiveError("Subscription is already cancelled.")
        
        old_status = subscription.sub_status
        subscription.sub_status = SubscriptionStatus.INACTIVE
        subscription.reserved_amount = Decimal('0')  # Release funds
        
        await db.flush()
        await db.refresh(subscription)
        
        logger.info(f"Subscription cancelled: {subscription_id} | Previous status: {old_status}")
        return subscription

    @staticmethod
    async def get_user_subscriptions(
        db: AsyncSession,
        user_id: uuid.UUID,
        active_only: bool = True
    ) -> List[Subscription]:
        query = select(Subscription).filter(Subscription.subscriber_id == user_id)
        
        if active_only:
            query = query.filter(
                Subscription.sub_status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PAUSED])
            )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_trader_subscribers(
        db: AsyncSession,
        trader_id: uuid.UUID,
        active_only: bool = True
    ) -> List[Subscription]:
        stmt = await db.execute(select(TraderProfile).filter(TraderProfile.id == trader_id))
        result = stmt.scalar_one_or_none()
        if not result:
            logger.error(f"Could not find trader {trader_id}")
            raise es.TraderProfileNotFoundError
        query = select(Subscription).filter(Subscription.trader_id == trader_id)
        
        if active_only:
            query = query.filter(Subscription.sub_status == SubscriptionStatus.ACTIVE)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_subscription_by_id(
        db: AsyncSession,
        subscription_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> Optional[Subscription]:
        query = select(Subscription).filter(Subscription.sub_id == subscription_id)
        
        if user_id:
            query = query.filter(Subscription.subscriber_id == user_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
