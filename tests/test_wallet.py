import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch, AsyncMock

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import account
from application.models.ledger import Account as LedgerAccount, LedgerTransaction, LedgerEntry
from application.models.enums import AccountType, UserTier, TransactionType, TransactionStatus, EntryDirection
from application.services.ledger_service import LedgerService
from application.services.registration_service import RegistrationService
from application.utilities import oauth2
from application.utilities import exceptions as es


class TestVirtualBalanceIssuance:
    
    @pytest.mark.asyncio
    async def test_issue_virtual_balance_success(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.issue_virtual_balance(db_session, test_user.id, Decimal("10000"))
        await db_session.commit()
        assert transaction is not None
        assert transaction.type == TransactionType.VIRTUAL_ISSUANCE
        assert transaction.amount == Decimal("10000")
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("10000")

    @pytest.mark.asyncio
    async def test_issue_virtual_balance_custom_amount(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.issue_virtual_balance(db_session, test_user.id, Decimal("50000"))
        await db_session.commit()
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("50000")

    @pytest.mark.asyncio
    async def test_issue_virtual_balance_no_demo_wallet_fails(self, db_session, test_user, system_accounts):
        with pytest.raises(es.AccountNotFoundError):
            await LedgerService.issue_virtual_balance(db_session, test_user.id, Decimal("10000"))

    @pytest.mark.asyncio
    async def test_issue_virtual_balance_no_system_treasury_fails(self, db_session, test_user):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        with pytest.raises(es.SystemAccountNotFoundError):
            await LedgerService.issue_virtual_balance(db_session, test_user.id, Decimal("10000"))


class TestVirtualBalanceReset:
    
    @pytest.mark.asyncio
    async def test_free_reset_success_when_eligible(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.reset_virtual_balance(db_session, test_user.id, is_paid=False)
        await db_session.commit()
        assert transaction is not None
        assert transaction.type == TransactionType.VIRTUAL_RESET_FREE
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("10000")

    @pytest.mark.asyncio
    async def test_free_reset_fails_within_30_days(self, db_session, test_user, system_accounts):
        test_user.virtual_balance_reset_at = datetime.now(timezone.utc) - timedelta(days=15)
        await db_session.commit()
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        with pytest.raises(es.InvalidRequestError, match="30 days"):
            await LedgerService.reset_virtual_balance(db_session, test_user.id, is_paid=False)

    @pytest.mark.asyncio
    async def test_paid_reset_works_anytime(self, db_session, test_user, system_accounts):
        test_user.virtual_balance_reset_at = datetime.now(timezone.utc) - timedelta(days=5)
        await db_session.commit()
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.reset_virtual_balance(db_session, test_user.id, is_paid=True)
        await db_session.commit()
        assert transaction is not None
        assert transaction.type == TransactionType.VIRTUAL_RESET

    @pytest.mark.asyncio
    async def test_reset_after_30_days_free_available(self, db_session, test_user, system_accounts):
        test_user.virtual_balance_reset_at = datetime.now(timezone.utc) - timedelta(days=35)
        await db_session.commit()
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("500"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.reset_virtual_balance(db_session, test_user.id, is_paid=False)
        await db_session.commit()
        assert transaction is not None


class TestResetEligibility:
    
    @pytest.mark.asyncio
    async def test_check_eligibility_new_user(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("10000"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        eligibility = await LedgerService.check_reset_eligibility(db_session, test_user.id)
        assert eligibility["current_balance"] == Decimal("10000")
        assert eligibility["is_blown"] == False
        assert eligibility["free_reset_available"] == True

    @pytest.mark.asyncio
    async def test_check_eligibility_blown_wallet(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        eligibility = await LedgerService.check_reset_eligibility(db_session, test_user.id)
        assert eligibility["is_blown"] == True

    @pytest.mark.asyncio
    async def test_check_eligibility_negative_balance(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("-100"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        eligibility = await LedgerService.check_reset_eligibility(db_session, test_user.id)
        assert eligibility["is_blown"] == True

    @pytest.mark.asyncio
    async def test_check_eligibility_after_recent_reset(self, db_session, test_user, system_accounts):
        test_user.virtual_balance_reset_at = datetime.now(timezone.utc) - timedelta(days=10)
        await db_session.commit()
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("5000"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        eligibility = await LedgerService.check_reset_eligibility(db_session, test_user.id)
        assert eligibility["free_reset_available"] == False


class TestWalletInfo:
    
    @pytest.mark.asyncio
    async def test_get_wallet_info_demo_wallet(self, db_session, test_user):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("8500.50"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        info = await LedgerService.get_wallet_info(db_session, test_user.id)
        assert info is not None
        assert info["balance"] == Decimal("8500.50")

    @pytest.mark.asyncio
    async def test_get_wallet_info_no_wallet_returns_none(self, db_session, test_user):
        info = await LedgerService.get_wallet_info(db_session, test_user.id)
        assert info is None


class TestLedgerTransactionCreation:
    
    @pytest.mark.asyncio
    async def test_transaction_has_reference_id(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.issue_virtual_balance(db_session, test_user.id, Decimal("10000"))
        await db_session.commit()
        assert transaction.reference_id is not None

    @pytest.mark.asyncio
    async def test_transaction_creates_ledger_entries(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.issue_virtual_balance(db_session, test_user.id, Decimal("10000"))
        await db_session.commit()
        result = await db_session.execute(select(LedgerEntry).filter(LedgerEntry.transaction_id == transaction.id))
        entries = result.scalars().all()
        assert len(entries) == 2
        directions = {e.direction for e in entries}
        assert EntryDirection.DEBIT in directions
        assert EntryDirection.CREDIT in directions


class TestLiveWalletActivation:
    
    @pytest.mark.asyncio
    async def test_activate_live_wallet_success(self, db_session, plus_user, system_accounts):
        live_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=plus_user.id, type=AccountType.USER_LIVE_WALLET, name="Plus User Live", currency="USD", balance=Decimal("0"), is_active=False, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(live_wallet)
        await db_session.commit()
        wallet = await RegistrationService.activate_live_wallet(db_session, plus_user.id)
        await db_session.commit()
        await db_session.refresh(wallet)
        assert wallet.is_active == True

    @pytest.mark.asyncio
    async def test_activate_live_wallet_no_wallet_fails(self, db_session, plus_user, system_accounts):
        with pytest.raises(es.AccountNotFoundError):
            await RegistrationService.activate_live_wallet(db_session, plus_user.id)

    @pytest.mark.asyncio
    async def test_activate_live_wallet_already_active_ok(self, db_session, plus_user, system_accounts):
        live_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=plus_user.id, type=AccountType.USER_LIVE_WALLET, name="Plus User Live", currency="USD", balance=Decimal("1000"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(live_wallet)
        await db_session.commit()
        wallet = await RegistrationService.activate_live_wallet(db_session, plus_user.id)
        assert wallet.is_active == True


class TestDoubleEntryIntegrity:
    
    @pytest.mark.asyncio
    async def test_debit_credit_amounts_match(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.issue_virtual_balance(db_session, test_user.id, Decimal("10000"))
        await db_session.commit()
        result = await db_session.execute(select(LedgerEntry).filter(LedgerEntry.transaction_id == transaction.id))
        entries = result.scalars().all()
        debit_total = sum(e.amount for e in entries if e.direction == EntryDirection.DEBIT)
        credit_total = sum(e.amount for e in entries if e.direction == EntryDirection.CREDIT)
        assert debit_total == credit_total

    @pytest.mark.asyncio
    async def test_system_treasury_decrements_on_issuance(self, db_session, test_user, system_accounts):
        treasury = next(a for a in system_accounts if a.type == AccountType.SYSTEM_BANK_BALANCE)
        initial_balance = treasury.balance
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        await LedgerService.issue_virtual_balance(db_session, test_user.id, Decimal("10000"))
        await db_session.commit()
        await db_session.refresh(treasury)
        assert treasury.balance == initial_balance - Decimal("10000")


class TestWalletAccountTypes:
    
    @pytest.mark.asyncio
    async def test_demo_wallet_type_enum_value(self):
        assert AccountType.USER_DEMO_WALLET.value == "user_demo_wallet"

    @pytest.mark.asyncio
    async def test_live_wallet_type_enum_value(self):
        assert AccountType.USER_LIVE_WALLET.value == "user_live_wallet"

    @pytest.mark.asyncio
    async def test_system_bank_type_enum_value(self):
        assert AccountType.SYSTEM_BANK_BALANCE.value == "system_bank_balance"


class TestWalletEdgeCases:
    
    @pytest.mark.asyncio
    async def test_reset_with_zero_amount_wallet(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.reset_virtual_balance(db_session, test_user.id, is_paid=False)
        await db_session.commit()
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("10000")

    @pytest.mark.asyncio
    async def test_reset_with_partial_balance(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Test Demo Wallet", currency="USD", balance=Decimal("3500.75"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        transaction = await LedgerService.reset_virtual_balance(db_session, test_user.id, is_paid=False)
        await db_session.commit()
        await db_session.refresh(demo_wallet)
        assert demo_wallet.balance == Decimal("10000")

    @pytest.mark.asyncio
    async def test_unicode_in_wallet_name(self, db_session, test_user):
        wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Müller's Trading Account", currency="USD", balance=Decimal("10000"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(wallet)
        await db_session.commit()
        await db_session.refresh(wallet)
        assert "Müller" in wallet.name

    @pytest.mark.asyncio
    async def test_very_large_balance_precision(self, db_session, test_user):
        wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Big Balance Wallet", currency="USD", balance=Decimal("999999999.99"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(wallet)
        await db_session.commit()
        await db_session.refresh(wallet)
        assert wallet.balance == Decimal("999999999.99")

    @pytest.mark.asyncio
    async def test_decimal_precision_maintained(self, db_session, test_user):
        wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="Precision Wallet", currency="USD", balance=Decimal("1234.56789"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(wallet)
        await db_session.commit()
        await db_session.refresh(wallet)
        assert Decimal("1234.56") <= wallet.balance <= Decimal("1234.57")


class TestVirtualWalletSchema:
    
    def test_virtual_wallet_status_response(self):
        from application.schemas.virtual_wallet import VirtualWalletStatusResponse
        response = VirtualWalletStatusResponse(current_balance=Decimal("10000"), is_blown=False, free_reset_available=True, free_reset_date=None, days_since_last_reset=None, paid_reset_cost_usd=Decimal("5"))
        assert response.current_balance == Decimal("10000")

    def test_virtual_balance_reset_response(self):
        from application.schemas.virtual_wallet import VirtualBalanceResetResponse
        response = VirtualBalanceResetResponse(message="Balance reset successfully", new_balance=Decimal("10000"), reset_type="free", transaction_reference="TXN-12345")
        assert response.reset_type == "free"


class TestMultipleWallets:
    
    @pytest.mark.asyncio
    async def test_user_can_have_both_demo_and_live(self, db_session, plus_user):
        demo = LedgerAccount(id=uuid.uuid4(), owner_id=plus_user.id, type=AccountType.USER_DEMO_WALLET, name="Demo", currency="USD", balance=Decimal("10000"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        live = LedgerAccount(id=uuid.uuid4(), owner_id=plus_user.id, type=AccountType.USER_LIVE_WALLET, name="Live", currency="USD", balance=Decimal("0"), is_active=False, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo)
        db_session.add(live)
        await db_session.commit()
        result = await db_session.execute(select(LedgerAccount).filter(LedgerAccount.owner_id == plus_user.id))
        wallets = result.scalars().all()
        assert len(wallets) == 2

    @pytest.mark.asyncio
    async def test_demo_wallet_operations_dont_affect_live(self, db_session, plus_user, system_accounts):
        demo = LedgerAccount(id=uuid.uuid4(), owner_id=plus_user.id, type=AccountType.USER_DEMO_WALLET, name="Demo", currency="USD", balance=Decimal("0"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        live = LedgerAccount(id=uuid.uuid4(), owner_id=plus_user.id, type=AccountType.USER_LIVE_WALLET, name="Live", currency="USD", balance=Decimal("500"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo)
        db_session.add(live)
        await db_session.commit()
        await LedgerService.reset_virtual_balance(db_session, plus_user.id, is_paid=False)
        await db_session.commit()
        await db_session.refresh(demo)
        await db_session.refresh(live)
        assert demo.balance == Decimal("10000")
        assert live.balance == Decimal("500")
