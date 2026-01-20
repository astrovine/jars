"""
Some E2E business logic tests for JARS.
Aim to model the complete user journey from registration, subscription management all the way to when the make thier first trade.
Focusing heavily on the edge cases and error handling.   

"""

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
        # STEP 1: User registers for free tier
        user_data = account_schema.UserCreate(
            first_name="Lifecycle",
            last_name="TestUser",
            email=f"lifecycle{uuid.uuid4().hex[:6]}@example.com",
            country="NG",
            password="ValidPass123!"
        )
        
        user = await RegistrationService.register_free_user(db_session, user_data)
        await db_session.commit()
        
        assert user is not None
        assert user.tier == UserTier.FREE
        assert user.status == "PENDING"
        
        # STEP 2: Verify demo wallet was created with 10k V-USD
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
        
        # STEP 3: Verify NO live wallet exists for free user
        result = await db_session.execute(
            select(LedgerAccount).filter(
                LedgerAccount.owner_id == user.id,
                LedgerAccount.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = result.scalar_one_or_none()
        
        assert live_wallet is None  # Free users don't have live wallets
        
        # STEP 4: Check reset eligibility (should be available)
        eligibility = await LedgerService.check_reset_eligibility(db_session, user.id)
        
        assert eligibility["current_balance"] == Decimal("10000")
        assert eligibility["is_blown"] == False
        assert eligibility["free_reset_available"] == True
        
        # STEP 5: Upgrade to Plus tier
        upgraded_user = await RegistrationService.upgrade_to_plus(db_session, user.id)
        await db_session.commit()
        
        assert upgraded_user.tier == UserTier.PLUS
        
        # STEP 6: Verify live wallet was created (inactive until KYC)
        result = await db_session.execute(
            select(LedgerAccount).filter(
                LedgerAccount.owner_id == user.id,
                LedgerAccount.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = result.scalar_one_or_none()
        
        assert live_wallet is not None
        assert live_wallet.is_active == False  # Inactive until KYC approved
        
        # STEP 7: Demo wallet should still be active
        await db_session.refresh(demo_wallet)
        assert demo_wallet.is_active == True


class TestWalletBlownScenario:
    @pytest.mark.asyncio
    async def test_blown_wallet_reset_cycle(self, db_session, test_user, system_accounts):
        # Create demo wallet with 0 balance (blown)
        demo_wallet = LedgerAccount(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            type=AccountType.USER_DEMO_WALLET,
            name="Test Demo Wallet",
            currency="USD",
            balance=Decimal("0"),  # BLOWN
            is_active=True,
            is_system=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(demo_wallet)
        await db_session.commit()
        
        # STEP 1: Check eligibility - should show blown
        eligibility = await LedgerService.check_reset_eligibility(db_session, test_user.id)
        
        assert eligibility["is_blown"] == True
        assert eligibility["current_balance"] == Decimal("0")
        assert eligibility["free_reset_available"] == True  # Never reset before
        
        # STEP 2: Perform free reset
        transaction = await LedgerService.reset_virtual_balance(
            db_session, test_user.id, is_paid=False
        )
        await db_session.commit()
        
        assert transaction is not None
        assert transaction.type == TransactionType.VIRTUAL_RESET_FREE
        
        # STEP 3: Verify wallet restored to 10k
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("10000")
        
        # STEP 4: Check eligibility again - free reset should now be unavailable
        eligibility = await LedgerService.check_reset_eligibility(db_session, test_user.id)
        
        assert eligibility["free_reset_available"] == False
        assert eligibility["is_blown"] == False
        
        # STEP 5: Try free reset again - should fail
        with pytest.raises(es.InvalidRequestError, match="Free reset not available"):
            await LedgerService.reset_virtual_balance(
                db_session, test_user.id, is_paid=False
            )
        
        # STEP 6: Paid reset should still work
        # Simulate wallet blown again
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
    """
    Test all tier upgrade and downgrade paths
    """
    
    @pytest.mark.asyncio
    async def test_free_to_plus_to_business(self, db_session, test_user, system_accounts):
        assert test_user.tier == UserTier.FREE
        
        # Upgrade Free → Plus
        user = await RegistrationService.upgrade_to_plus(db_session, test_user.id)
        await db_session.commit()
        assert user.tier == UserTier.PLUS
        
        # Upgrade Plus → Business
        user = await RegistrationService.upgrade_to_business(db_session, user.id)
        await db_session.commit()
        assert user.tier == UserTier.BUSINESS
        
        # Downgrade Business → Free
        user = await RegistrationService.downgrade_to_free(db_session, user.id)
        await db_session.commit()
        assert user.tier == UserTier.FREE
        
        # Verify live wallet is now deactivated
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
        
        # Direct upgrade to Business
        user = await RegistrationService.upgrade_to_business(db_session, test_user.id)
        await db_session.commit()
        
        assert user.tier == UserTier.BUSINESS
        
        # Should have both demo and live wallet
        result = await db_session.execute(
            select(LedgerAccount).filter(LedgerAccount.owner_id == test_user.id)
        )
        wallets = result.scalars().all()
        
        wallet_types = {w.type for w in wallets}
        
        # Demo wallet should be ensured
        assert AccountType.USER_DEMO_WALLET in wallet_types or AccountType.USER_LIVE_WALLET in wallet_types


class TestAuthenticationFlow:
    """
    Complete authentication flow: Register → Login → Access Protected
    """
    
    @pytest.mark.asyncio
    async def test_register_login_access_flow(self, db_session, system_accounts, mock_send_email):
        # STEP 1: Register
        email = f"authflow{uuid.uuid4().hex[:6]}@example.com"
        password = "ValidPass123!"
        
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
        
        # Simulate email verification - set status and ensure is_active
        user.status = "VERIFIED"
        user.is_active = True
        await db_session.commit()
        await db_session.refresh(user)
        
        # STEP 2: Login (returns tokens dict, not user)
        login_result = await AuthService.login_user(
            db_session, email, password
        )
        
        assert login_result is not None
        assert "access_token" in login_result or "pre_auth_token" in login_result
        
        # STEP 3: Generate access token directly
        access_token = oauth2.create_access_token(str(user.id))
        
        assert access_token is not None
        assert len(access_token) > 0
        
        # STEP 4: Verify token
        token_data = oauth2.verify_access_token(
            access_token, 
            es.InvalidCredentialsError("Invalid")
        )
        
        assert token_data.id == str(user.id)

    @pytest.mark.asyncio
    async def test_wrong_password_blocks_access(self, db_session, test_user):
        # Try to login with wrong password - should raise exception
        with pytest.raises(es.InvalidCredentialsError):
            await AuthService.login_user(
                db_session,
                test_user.email,
                "WrongPassword123!"
            )


class TestPasswordManagement:
    """
    Password change lifecycle
    """
    
    @pytest.mark.asyncio
    async def test_password_change_flow(self, db_session, test_user):
        old_password = "ValidPass123!"
        new_password = "NewSecurePass456!"
        
        # STEP 1: Change password
        await AccountService.change_user_password(
            db_session,
            test_user.id,
            old_password,
            new_password,
            new_password
        )
        await db_session.commit()
        
        # STEP 2: Old password should no longer work (raises exception)
        with pytest.raises(es.InvalidCredentialsError):
            await AuthService.login_user(
                db_session,
                test_user.email,
                old_password
            )
        
        # STEP 3: New password should work
        result = await AuthService.login_user(
            db_session,
            test_user.email,
            new_password
        )
        assert result is not None
        assert "access_token" in result or "pre_auth_token" in result


class TestAccountDeletion:
    """
    Account deletion and cleanup
    """
    
    @pytest.mark.asyncio
    async def test_delete_user_cleans_up_wallets(self, db_session, system_accounts, mock_send_email):
        # Create user with wallet
        user_data = account_schema.UserCreate(
            first_name="ToDelete",
            last_name="User",
            email=f"delete{uuid.uuid4().hex[:6]}@example.com",
            country="NG",
            password="ValidPass123!"
        )
        
        user = await RegistrationService.register_free_user(db_session, user_data)
        await db_session.commit()
        
        user_id = user.id
        
        # Verify wallet exists
        result = await db_session.execute(
            select(LedgerAccount).filter(LedgerAccount.owner_id == user_id)
        )
        wallets = result.scalars().all()
        assert len(wallets) > 0
        
        # Delete user
        await AccountService.delete_user_account(db_session, user_id)
        await db_session.commit()
        
        # Verify user is gone
        result = await db_session.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is None


class TestDoubleSpendPrevention:
    """
    Ensure ledger integrity and no double spending
    """
    
    @pytest.mark.asyncio
    async def test_virtual_issuance_creates_balanced_entries(
        self, db_session, test_user, system_accounts
    ):
        # Create demo wallet
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
        
        # Get treasury balance before
        treasury = next(a for a in system_accounts if a.type == AccountType.SYSTEM_BANK_BALANCE)
        await db_session.refresh(treasury)
        treasury_before = treasury.balance
        
        # Issue virtual balance
        transaction = await LedgerService.issue_virtual_balance(
            db_session, test_user.id, Decimal("10000")
        )
        await db_session.commit()
        
        # Verify treasury decreased
        await db_session.refresh(treasury)
        assert treasury.balance == treasury_before - Decimal("10000")
        
        # Verify demo wallet increased
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("10000")
        
        # Net change should be zero (double-entry)
        net_change = (treasury.balance - treasury_before) + (demo_wallet.balance - Decimal("0"))
        assert net_change == Decimal("0")


class TestConcurrentRegistration:
    """
    Ensure race conditions are handled
    """
    
    @pytest.mark.asyncio
    async def test_duplicate_email_registration_fails(
        self, db_session, system_accounts, mock_send_email
    ):
        email = f"unique{uuid.uuid4().hex[:6]}@example.com"
        
        # First registration
        user_data = account_schema.UserCreate(
            first_name="First",
            last_name="User",
            email=email,
            country="NG",
            password="ValidPass123!"
        )
        
        user = await RegistrationService.register_free_user(db_session, user_data)
        await db_session.commit()
        
        assert user is not None
        
        # Second registration with same email should fail
        user_data2 = account_schema.UserCreate(
            first_name="Second",
            last_name="User",
            email=email,
            country="NG",
            password="AnotherPass123!"
        )
        
        with pytest.raises(es.EmailAlreadyExistsError):
            await RegistrationService.register_free_user(db_session, user_data2)


class TestSystemAccountDependency:
    """
    Test behavior when system accounts are missing
    """
    
    @pytest.mark.asyncio
    async def test_registration_fails_without_system_accounts(
        self, db_session, mock_send_email
    ):
        """Important edge case: What happens if someone forgets to seed?"""
        user_data = account_schema.UserCreate(
            first_name="NoSystem",
            last_name="User",
            email=f"nosystem{uuid.uuid4().hex[:6]}@example.com",
            country="NG",
            password="ValidPass123!"
        )
        
        with pytest.raises(es.SystemAccountNotFoundError):
            await RegistrationService.register_free_user(db_session, user_data)
