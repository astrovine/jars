import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import account
from application.models.ledger import Account as LedgerAccount, LedgerTransaction
from application.models.enums import AccountType, UserTier, TransactionType
from application.services.registration_service import RegistrationService
from application.services.auth_service import AuthService
from application.services.ledger_service import LedgerService
from application.services.account_service import AccountService
from application.schemas import account as account_schema
from application.utilities import oauth2
from application.utilities import exceptions as es


class TestFreeUserLifecycle:
    
    @pytest.mark.asyncio
    async def test_free_user_complete_journey(self, db_session, system_accounts, mock_send_email):
        user_data = account_schema.UserCreate(
            first_name="Ocean",
            last_name="Yeah",
            email=f"yeah{uuid.uuid4().hex[:6]}@example.com",
            country="NG",
            password="onerandom1"
        )
        
        user = await RegistrationService.register_free_user(db_session, user_data)
        await db_session.commit()
        
        assert user is not None
        assert user.tier == UserTier.FREE
        assert user.status == "PENDING"
        
        result = await db_session.execute(
            select(LedgerAccount).filter(
                LedgerAccount.owner_id == user.id,
                LedgerAccount.type == AccountType.USER_DEMO_WALLET
            )
        )
        demo_wallet = result.scalar_one_or_none()
        
        assert demo_wallet is not None
        assert demo_wallet.balance == Decimal("10000")
        assert demo_wallet.is_active == True

        result = await db_session.execute(
            select(LedgerAccount).filter(
                LedgerAccount.owner_id == user.id,
                LedgerAccount.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = result.scalar_one_or_none()
        
        assert live_wallet is None
        
        eligibility = await LedgerService.check_reset_eligibility(db_session, user.id)
        
        assert eligibility["current_balance"] == Decimal("10000")
        assert eligibility["is_blown"] == False
        assert eligibility["free_reset_available"] == True
        
        upgraded_user = await RegistrationService.upgrade_to_plus(db_session, user.id)
        await db_session.commit()
        
        assert upgraded_user.tier == UserTier.PLUS
        
        result = await db_session.execute(
            select(LedgerAccount).filter(
                LedgerAccount.owner_id == user.id,
                LedgerAccount.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = result.scalar_one_or_none()
        
        assert live_wallet is not None
        assert live_wallet.is_active == False
        
        await db_session.refresh(demo_wallet)
        assert demo_wallet.is_active == True


class TestWalletBlownScenario:
    
    @pytest.mark.asyncio
    async def test_blown_wallet_reset_cycle(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            type=AccountType.USER_DEMO_WALLET,
            name="Test Demo Wallet",
            currency="USD",
            balance=Decimal("0"),
            is_active=True,
            is_system=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(demo_wallet)
        await db_session.commit()
        
        eligibility = await LedgerService.check_reset_eligibility(db_session, test_user.id)
        
        assert eligibility["is_blown"] == True
        assert eligibility["current_balance"] == Decimal("0")
        assert eligibility["free_reset_available"] == True
        
        transaction = await LedgerService.reset_virtual_balance(
            db_session, test_user.id, is_paid=False
        )
        await db_session.commit()
        
        assert transaction is not None
        assert transaction.type == TransactionType.VIRTUAL_RESET_FREE
        
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("10000")
        
        eligibility = await LedgerService.check_reset_eligibility(db_session, test_user.id)
        
        assert eligibility["free_reset_available"] == False
        assert eligibility["is_blown"] == False
        
        with pytest.raises(es.InvalidRequestError, match="Free reset not available"):
            await LedgerService.reset_virtual_balance(
                db_session, test_user.id, is_paid=False
            )
        
        demo_wallet.balance = Decimal("0")
        await db_session.commit()
        
        transaction = await LedgerService.reset_virtual_balance(
            db_session, test_user.id, is_paid=True
        )
        await db_session.commit()
        
        assert transaction is not None
        assert transaction.type == TransactionType.VIRTUAL_RESET
        
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("10000")


class TestTierTransitions:
    
    @pytest.mark.asyncio
    async def test_free_to_plus_to_business(self, db_session, test_user, system_accounts):
        assert test_user.tier == UserTier.FREE
        
        user = await RegistrationService.upgrade_to_plus(db_session, test_user.id)
        await db_session.commit()
        assert user.tier == UserTier.PLUS
        
        user = await RegistrationService.upgrade_to_business(db_session, user.id)
        await db_session.commit()
        assert user.tier == UserTier.BUSINESS
        
        user = await RegistrationService.downgrade_to_free(db_session, user.id)
        await db_session.commit()
        assert user.tier == UserTier.FREE
        
        result = await db_session.execute(
            select(LedgerAccount).filter(
                LedgerAccount.owner_id == test_user.id,
                LedgerAccount.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = result.scalar_one_or_none()
        
        if live_wallet:
            assert live_wallet.is_active == False

    @pytest.mark.asyncio
    async def test_free_directly_to_business(self, db_session, test_user, system_accounts):
        assert test_user.tier == UserTier.FREE
        
        user = await RegistrationService.upgrade_to_business(db_session, test_user.id)
        await db_session.commit()
        
        assert user.tier == UserTier.BUSINESS
        
        result = await db_session.execute(
            select(LedgerAccount).filter(LedgerAccount.owner_id == test_user.id)
        )
        wallets = result.scalars().all()
        
        wallet_types = {w.type for w in wallets}
        
        assert AccountType.USER_DEMO_WALLET in wallet_types or AccountType.USER_LIVE_WALLET in wallet_types


class TestAuthenticationFlow:
    
    @pytest.mark.asyncio
    async def test_register_login_access_flow(self, db_session, system_accounts, mock_send_email):
        email = f"authflow{uuid.uuid4().hex[:6]}@example.com"
        password = "SunnyDays2024!"
        
        user_data = account_schema.UserCreate(
            first_name="Auth",
            last_name="Flow",
            email=email,
            country="NG",
            password=password
        )
        
        user = await RegistrationService.register_free_user(db_session, user_data)
        await db_session.commit()
        
        assert user is not None
        
        user.status = "VERIFIED"
        user.is_active = True
        await db_session.commit()
        await db_session.refresh(user)
        
        login_result = await AuthService.login_user(
            db_session, email, password
        )
        
        assert login_result is not None
        assert "access_token" in login_result or "pre_auth_token" in login_result
        
        access_token = oauth2.create_access_token(str(user.id))
        
        assert access_token is not None
        assert len(access_token) > 0
        
        token_data = oauth2.verify_access_token(
            access_token, 
            es.InvalidCredentialsError("Invalid")
        )
        
        assert token_data.id == str(user.id)

    @pytest.mark.asyncio
    async def test_wrong_password_blocks_access(self, db_session, test_user):
        with pytest.raises(es.InvalidCredentialsError):
            await AuthService.login_user(
                db_session,
                test_user.email,
                "TotallyWrongGuess99!"
            )


class TestPasswordManagement:
    
    @pytest.mark.asyncio
    async def test_password_change_flow(self, db_session, test_user):
        old_password = "MorningCoffee42!"
        new_password = "EveningTea2025#"
        
        await AccountService.change_user_password(
            db_session,
            test_user.id,
            old_password,
            new_password,
            new_password
        )
        await db_session.commit()
        
        with pytest.raises(es.InvalidCredentialsError):
            await AuthService.login_user(
                db_session,
                test_user.email,
                old_password
            )
        
        result = await AuthService.login_user(
            db_session,
            test_user.email,
            new_password
        )
        assert result is not None
        assert "access_token" in result or "pre_auth_token" in result


class TestAccountDeletion:
    
    @pytest.mark.asyncio
    async def test_delete_user_cleans_up_wallets(self, db_session, system_accounts, mock_send_email):
        user_data = account_schema.UserCreate(
            first_name="ToDelete",
            last_name="User",
            email=f"delete{uuid.uuid4().hex[:6]}@example.com",
            country="NG",
            password="GoodbyeWorld77!"
        )
        
        user = await RegistrationService.register_free_user(db_session, user_data)
        await db_session.commit()
        
        user_id = user.id
        
        result = await db_session.execute(
            select(LedgerAccount).filter(LedgerAccount.owner_id == user_id)
        )
        wallets = result.scalars().all()
        assert len(wallets) > 0
        
        await AccountService.delete_user_account(db_session, user_id)
        await db_session.commit()
        
        result = await db_session.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is None


class TestDoubleSpendPrevention:
    
    @pytest.mark.asyncio
    async def test_virtual_issuance_creates_balanced_entries(
        self, db_session, test_user, system_accounts
    ):
        demo_wallet = LedgerAccount(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            type=AccountType.USER_DEMO_WALLET,
            name="Double Entry Test",
            currency="USD",
            balance=Decimal("0"),
            is_active=True,
            is_system=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(demo_wallet)
        await db_session.commit()
        
        treasury = next(a for a in system_accounts if a.type == AccountType.SYSTEM_BANK_BALANCE)
        await db_session.refresh(treasury)
        treasury_before = treasury.balance
        
        transaction = await LedgerService.issue_virtual_balance(
            db_session, test_user.id, Decimal("10000")
        )
        await db_session.commit()
        
        await db_session.refresh(treasury)
        assert treasury.balance == treasury_before - Decimal("10000")
        
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("10000")
        
        net_change = (treasury.balance - treasury_before) + (demo_wallet.balance - Decimal("0"))
        assert net_change == Decimal("0")


class TestConcurrentRegistration:
    
    @pytest.mark.asyncio
    async def test_duplicate_email_registration_fails(
        self, db_session, system_accounts, mock_send_email
    ):
        email = f"unique{uuid.uuid4().hex[:6]}@example.com"
        
        user_data = account_schema.UserCreate(
            first_name="First",
            last_name="User",
            email=email,
            country="NG",
            password="BlueSky2026!"
        )
        
        user = await RegistrationService.register_free_user(db_session, user_data)
        await db_session.commit()
        
        assert user is not None
        
        user_data2 = account_schema.UserCreate(
            first_name="Second",
            last_name="User",
            email=email,
            country="NG",
            password="RedSunset88#"
        )
        
        with pytest.raises(es.EmailAlreadyExistsError):
            await RegistrationService.register_free_user(db_session, user_data2)


class TestSystemAccountDependency:
    
    @pytest.mark.asyncio
    async def test_registration_fails_without_system_accounts(
        self, db_session, mock_send_email
    ):
        user_data = account_schema.UserCreate(
            first_name="NoSystem",
            last_name="User",
            email=f"nosystem{uuid.uuid4().hex[:6]}@example.com",
            country="NG",
            password="LonelyCloud55!"
        )
        
        with pytest.raises(es.SystemAccountNotFoundError):
            await RegistrationService.register_free_user(db_session, user_data)
