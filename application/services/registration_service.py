import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from application.models import account, ledger as ledger_models
from application.models.enums import AccountType, UserTier
from application.schemas import account as at
from application.services.ledger_service import LedgerService
from application.utilities import exceptions as es
from application.utilities import oauth2
from application.utilities.audit import setup_logger
from application.core.tasks import task_send_verification_email

logger = setup_logger(__name__)

VIRTUAL_BALANCE_AMOUNT = Decimal("10000")


class RegistrationService:

    @staticmethod
    async def create_user_base(
        db: AsyncSession,
        user_data: at.UserCreate,
        tier: UserTier = UserTier.FREE
    ) -> account.User:
        result = await db.execute(
            select(account.User).filter(account.User.email == user_data.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise es.EmailAlreadyExistsError()

        password_hash = oauth2.get_password_hash(user_data.password)
        
        new_user = account.User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            status='PENDING',
            password=password_hash,
            country=user_data.country,
            tier=tier,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_user)
        await db.flush()
        
        return new_user

    @staticmethod
    async def setup_email_verification(db: AsyncSession, user: account.User) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user.email_verification_token = token_hash
        user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        await db.flush()
        return token

    @staticmethod
    async def register_free_user(db: AsyncSession, user_data: at.UserCreate) -> account.User:
        logger.info(f"[FREE REGISTRATION] Starting for {user_data.email}")
        
        new_user = await RegistrationService.create_user_base(db, user_data, UserTier.FREE)
        logger.info(f"[FREE REGISTRATION] User created | ID: {new_user.id}")

        demo_wallet = ledger_models.Account(
            owner_id=new_user.id,
            currency="USD",
            name=f'{new_user.first_name} {new_user.last_name} Demo',
            type=AccountType.USER_DEMO_WALLET,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(demo_wallet)
        await db.flush()
        logger.info(f"[FREE REGISTRATION] Demo wallet created | Wallet ID: {demo_wallet.id}")

        await LedgerService.issue_virtual_balance(db, new_user.id, VIRTUAL_BALANCE_AMOUNT)
        logger.info(f"[FREE REGISTRATION] {VIRTUAL_BALANCE_AMOUNT} V-USDT issued")

        token = await RegistrationService.setup_email_verification(db, new_user)
        task_send_verification_email.delay(new_user.email, token)
        
        return new_user

    @staticmethod
    async def register_plus_user(db: AsyncSession, user_data: at.UserCreate) -> account.User:
        logger.info(f"[PLUS REGISTRATION] Starting for {user_data.email}")
        
        new_user = await RegistrationService.create_user_base(db, user_data, UserTier.PLUS)
        logger.info(f"[PLUS REGISTRATION] User created | ID: {new_user.id}")

        demo_wallet = ledger_models.Account(
            owner_id=new_user.id,
            currency="USD",
            name=f'{new_user.first_name} {new_user.last_name} Demo',
            type=AccountType.USER_DEMO_WALLET,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(demo_wallet)
        
        live_wallet = ledger_models.Account(
            owner_id=new_user.id,
            currency="USD",
            name=f'{new_user.first_name} {new_user.last_name} Live',
            type=AccountType.USER_LIVE_WALLET,
            is_active=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(live_wallet)
        await db.flush()
        
        logger.info(f"[PLUS REGISTRATION] Wallets created | Demo: {demo_wallet.id} | Live: {live_wallet.id}")

        await LedgerService.issue_virtual_balance(db, new_user.id, VIRTUAL_BALANCE_AMOUNT)
        
        token = await RegistrationService.setup_email_verification(db, new_user)
        task_send_verification_email.delay(new_user.email, token)
        
        return new_user

    @staticmethod
    async def register_business_user(db: AsyncSession, user_data: at.UserCreate) -> account.User:
        logger.info(f"[BUSINESS REGISTRATION] Starting for {user_data.email}")
        
        new_user = await RegistrationService.create_user_base(db, user_data, UserTier.BUSINESS)
        logger.info(f"[BUSINESS REGISTRATION] User created | ID: {new_user.id}")

        demo_wallet = ledger_models.Account(
            owner_id=new_user.id,
            currency="USD",
            name=f'{new_user.first_name} {new_user.last_name} Demo',
            type=AccountType.USER_DEMO_WALLET,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(demo_wallet)
        
        live_wallet = ledger_models.Account(
            owner_id=new_user.id,
            currency="USD",
            name=f'{new_user.first_name} {new_user.last_name} Live',
            type=AccountType.USER_LIVE_WALLET,
            is_active=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(live_wallet)
        await db.flush()
        
        logger.info(f"[BUSINESS REGISTRATION] Wallets created | Demo: {demo_wallet.id} | Live: {live_wallet.id}")

        await LedgerService.issue_virtual_balance(db, new_user.id, VIRTUAL_BALANCE_AMOUNT)
        
        token = await RegistrationService.setup_email_verification(db, new_user)
        task_send_verification_email.delay(new_user.email, token)
        
        return new_user

    @staticmethod
    async def activate_live_wallet(db: AsyncSession, user_id: uuid.UUID) -> ledger_models.Account:
        result = await db.execute(
            select(ledger_models.Account).filter(
                ledger_models.Account.owner_id == user_id,
                ledger_models.Account.type == AccountType.USER_LIVE_WALLET
            )
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            raise es.AccountNotFoundError("Live wallet not found for user")
        
        wallet.is_active = True
        await db.flush()
        
        logger.info(f"[WALLET ACTIVATED] Live wallet {wallet.id} activated for user {user_id}")
        return wallet

    @staticmethod
    async def downgrade_to_free(db: AsyncSession, user_id: uuid.UUID) -> account.User:
        result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise es.UserNotFoundError()
        
        user.tier = UserTier.FREE
        
        live_wallet_result = await db.execute(
            select(ledger_models.Account).filter(
                ledger_models.Account.owner_id == user_id,
                ledger_models.Account.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = live_wallet_result.scalar_one_or_none()
        if live_wallet:
            live_wallet.is_active = False
        
        await db.flush()
        logger.info(f"[TIER DOWNGRADE] User {user_id} downgraded to FREE tier")
        
        return user

    @staticmethod
    async def upgrade_to_plus(db: AsyncSession, user_id: uuid.UUID) -> account.User:
        result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise es.UserNotFoundError()
        
        if user.tier == UserTier.PLUS:
            raise es.InvalidRequestError("User is already on Plus tier")
        
        if user.tier == UserTier.BUSINESS:
            raise es.InvalidRequestError("Cannot downgrade from Business to Plus via upgrade endpoint")
        
        logger.info(f"[TIER UPGRADE] Upgrading user {user_id} from {user.tier.value} to PLUS")
        
        live_wallet_result = await db.execute(
            select(ledger_models.Account).filter(
                ledger_models.Account.owner_id == user_id,
                ledger_models.Account.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = live_wallet_result.scalar_one_or_none()
        
        if live_wallet:
            live_wallet.is_active = False
            logger.info(f"[TIER UPGRADE] Reusing existing live wallet {live_wallet.id}")
        else:
            live_wallet = ledger_models.Account(
                owner_id=user_id,
                currency="USD",
                name=f'{user.first_name} {user.last_name} Live',
                type=AccountType.USER_LIVE_WALLET,
                is_active=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(live_wallet)
            logger.info(f"[TIER UPGRADE] Created new live wallet for user {user_id}")
        
        demo_wallet_result = await db.execute(
            select(ledger_models.Account).filter(
                ledger_models.Account.owner_id == user_id,
                ledger_models.Account.type == AccountType.USER_DEMO_WALLET
            )
        )
        demo_wallet = demo_wallet_result.scalar_one_or_none()
        
        if not demo_wallet:
            demo_wallet = ledger_models.Account(
                owner_id=user_id,
                currency="USD",
                name=f'{user.first_name} {user.last_name} Demo',
                type=AccountType.USER_DEMO_WALLET,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(demo_wallet)
            await db.flush()
            await LedgerService.issue_virtual_balance(db, user_id, VIRTUAL_BALANCE_AMOUNT)
            logger.info(f"[TIER UPGRADE] Created missing demo wallet and issued virtual balance")
        
        user.tier = UserTier.PLUS
        await db.flush()
        
        logger.info(f"[TIER UPGRADE SUCCESS] User {user_id} upgraded to PLUS tier")
        return user

    @staticmethod
    async def upgrade_to_business(db: AsyncSession, user_id: uuid.UUID) -> account.User:
        result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise es.UserNotFoundError()
        
        if user.tier == UserTier.BUSINESS:
            raise es.InvalidRequestError("User is already on Business tier")
        
        logger.info(f"[TIER UPGRADE] Upgrading user {user_id} from {user.tier.value} to BUSINESS")
        
        live_wallet_result = await db.execute(
            select(ledger_models.Account).filter(
                ledger_models.Account.owner_id == user_id,
                ledger_models.Account.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = live_wallet_result.scalar_one_or_none()
        
        if live_wallet:
            live_wallet.is_active = False
            logger.info(f"[TIER UPGRADE] Reusing existing live wallet {live_wallet.id}")
        else:
            live_wallet = ledger_models.Account(
                owner_id=user_id,
                currency="USD",
                name=f'{user.first_name} {user.last_name} Live',
                type=AccountType.USER_LIVE_WALLET,
                is_active=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(live_wallet)
            logger.info(f"[TIER UPGRADE] Created new live wallet for user {user_id}")
        
        demo_wallet_result = await db.execute(
            select(ledger_models.Account).filter(
                ledger_models.Account.owner_id == user_id,
                ledger_models.Account.type == AccountType.USER_DEMO_WALLET
            )
        )
        demo_wallet = demo_wallet_result.scalar_one_or_none()
        
        if not demo_wallet:
            demo_wallet = ledger_models.Account(
                owner_id=user_id,
                currency="USD",
                name=f'{user.first_name} {user.last_name} Demo',
                type=AccountType.USER_DEMO_WALLET,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(demo_wallet)
            await db.flush()
            await LedgerService.issue_virtual_balance(db, user_id, VIRTUAL_BALANCE_AMOUNT)
            logger.info(f"[TIER UPGRADE] Created missing demo wallet and issued virtual balance")
        
        user.tier = UserTier.BUSINESS
        await db.flush()
        
        logger.info(f"[TIER UPGRADE SUCCESS] User {user_id} upgraded to BUSINESS tier")
        return user

    @staticmethod
    async def ensure_demo_wallet(db: AsyncSession, user_id: uuid.UUID) -> ledger_models.Account:
        result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise es.UserNotFoundError()
        
        wallet_result = await db.execute(
            select(ledger_models.Account).filter(
                ledger_models.Account.owner_id == user_id,
                ledger_models.Account.type == AccountType.USER_DEMO_WALLET
            )
        )
        wallet = wallet_result.scalar_one_or_none()
        
        if wallet:
            logger.info(f"[DEMO WALLET] User {user_id} already has demo wallet {wallet.id}")
            return wallet
        
        wallet = ledger_models.Account(
            owner_id=user_id,
            currency="USD",
            name=f'{user.first_name} {user.last_name} Demo',
            type=AccountType.USER_DEMO_WALLET,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(wallet)
        await db.flush()
        
        await LedgerService.issue_virtual_balance(db, user_id, VIRTUAL_BALANCE_AMOUNT)
        
        logger.info(f"[DEMO WALLET] Created demo wallet {wallet.id} for user {user_id} with {VIRTUAL_BALANCE_AMOUNT} V-USD")
        return wallet

    @staticmethod
    def upgrade_to_plus_sync(db, user_id: uuid.UUID, payment_ref: str = None):
        from application.models.subscription import TradingTiers, SubscriptionTierAccounts
        from application.models.enums import SubscriptionTier, SubscriptionTierStatus
        from datetime import timedelta
        
        result = db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error(f"[SYNC UPGRADE] User {user_id} not found")
            return None
        
        if user.tier == UserTier.PLUS:
            logger.info(f"[SYNC UPGRADE] User {user_id} already on Plus tier")
            return user
        
        logger.info(f"[SYNC UPGRADE] Upgrading user {user_id} to PLUS")
        
        wallet_result = db.execute(
            select(ledger_models.Account).filter(
                ledger_models.Account.owner_id == user_id,
                ledger_models.Account.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = wallet_result.scalar_one_or_none()
        
        if not live_wallet:
            live_wallet = ledger_models.Account(
                owner_id=user_id,
                currency="USD",
                name=f'{user.first_name} {user.last_name} Live',
                type=AccountType.USER_LIVE_WALLET,
                is_active=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(live_wallet)

        tier_result = db.execute(
            select(TradingTiers).filter(TradingTiers.tier_name == SubscriptionTier.PLUS)
        )
        trading_tier = tier_result.scalar_one_or_none()
        
        if trading_tier:
            existing_account = db.execute(
                select(SubscriptionTierAccounts).filter(
                    SubscriptionTierAccounts.user_id == user_id
                )
            ).scalar_one_or_none()
            
            if existing_account:
                existing_account.tier_id = trading_tier.id
                existing_account.tier_status = SubscriptionTierStatus.ACTIVE
                existing_account.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
                existing_account.renewed_at = datetime.now(timezone.utc)
                existing_account.payment_ref = payment_ref
            else:
                tier_account = SubscriptionTierAccounts(
                    user_id=user_id,
                    tier_id=trading_tier.id,
                    payment_ref=payment_ref,
                    tier_status=SubscriptionTierStatus.ACTIVE,
                    subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=30)
                )
                db.add(tier_account)
            logger.info(f"[SYNC UPGRADE] Created/updated tier account for user {user_id}")
        else:
            logger.warning(f"[SYNC UPGRADE] TradingTiers STANDARD not found in DB")
        
        user.tier = UserTier.PLUS
        db.flush()
        
        logger.info(f"[SYNC UPGRADE SUCCESS] User {user_id} upgraded to PLUS")
        return user

    @staticmethod
    def upgrade_to_business_sync(db, user_id: uuid.UUID, payment_ref: str = None):
        from application.models.subscription import TradingTiers, SubscriptionTierAccounts
        from application.models.enums import SubscriptionTier, SubscriptionTierStatus
        from datetime import timedelta
        
        result = db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error(f"[SYNC UPGRADE] User {user_id} not found")
            return None
        
        if user.tier == UserTier.BUSINESS:
            logger.info(f"[SYNC UPGRADE] User {user_id} already on Business tier")
            return user
        
        logger.info(f"[SYNC UPGRADE] Upgrading user {user_id} to BUSINESS")
        
        wallet_result = db.execute(
            select(ledger_models.Account).filter(
                ledger_models.Account.owner_id == user_id,
                ledger_models.Account.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = wallet_result.scalar_one_or_none()
        
        if not live_wallet:
            live_wallet = ledger_models.Account(
                owner_id=user_id,
                currency="USD",
                name=f'{user.first_name} {user.last_name} Live',
                type=AccountType.USER_LIVE_WALLET,
                is_active=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(live_wallet)

        tier_result = db.execute(
            select(TradingTiers).filter(TradingTiers.tier_name == SubscriptionTier.BUSINESS)
        )
        trading_tier = tier_result.scalar_one_or_none()
        
        if trading_tier:
            existing_account = db.execute(
                select(SubscriptionTierAccounts).filter(
                    SubscriptionTierAccounts.user_id == user_id
                )
            ).scalar_one_or_none()
            
            if existing_account:
                existing_account.tier_id = trading_tier.id
                existing_account.tier_status = SubscriptionTierStatus.ACTIVE
                existing_account.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
                existing_account.renewed_at = datetime.now(timezone.utc)
                existing_account.payment_ref = payment_ref
            else:
                tier_account = SubscriptionTierAccounts(
                    user_id=user_id,
                    tier_id=trading_tier.id,
                    payment_ref=payment_ref,
                    tier_status=SubscriptionTierStatus.ACTIVE,
                    subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=30)
                )
                db.add(tier_account)
            logger.info(f"[SYNC UPGRADE] Created/updated tier account for user {user_id}")
        else:
            logger.warning(f"[SYNC UPGRADE] TradingTiers PREMIUM not found in DB")
        
        user.tier = UserTier.BUSINESS
        db.flush()
        
        logger.info(f"[SYNC UPGRADE SUCCESS] User {user_id} upgraded to BUSINESS")
        return user
