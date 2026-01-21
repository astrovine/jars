import pytest
import pytest_asyncio
import uuid
import json
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch, AsyncMock, MagicMock
from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from application.models import account
from application.models.ledger import (
    Account as LedgerAccount, 
    LedgerTransaction, 
    LedgerEntry
)
from application.models.enums import (
    AccountType, 
    UserTier, 
    TransactionType, 
    TransactionStatus, 
    EntryDirection
)
from application.services.ledger_service import LedgerService
from application.utilities import oauth2
from application.utilities import exceptions as es

@pytest_asyncio.fixture
async def user_with_live_wallet(db_session: AsyncSession, test_user, system_accounts):
    live_wallet = LedgerAccount(
        id=uuid.uuid4(),
        owner_id=test_user.id,
        type=AccountType.USER_LIVE_WALLET,
        name=f"{test_user.first_name} {test_user.last_name} Live",
        currency="NGN",
        balance=Decimal("0"),
        is_active=True,
        is_system=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(live_wallet)
    await db_session.commit()
    await db_session.refresh(live_wallet)
    return test_user, live_wallet


@pytest_asyncio.fixture
async def user_with_funded_wallet(db_session: AsyncSession, test_user, system_accounts):
    live_wallet = LedgerAccount(
        id=uuid.uuid4(),
        owner_id=test_user.id,
        type=AccountType.USER_LIVE_WALLET,
        name=f"{test_user.first_name} {test_user.last_name} Live",
        currency="NGN",
        balance=Decimal("50000.00"),
        is_active=True,
        is_system=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(live_wallet)
    await db_session.commit()
    await db_session.refresh(live_wallet)
    return test_user, live_wallet


@pytest_asyncio.fixture
async def pending_deposit(db_session: AsyncSession, user_with_live_wallet, system_accounts):
    user, wallet = user_with_live_wallet
    reference = f"test_deposit_{uuid.uuid4().hex[:12]}"
    
    transaction = await LedgerService.create_pending_deposit(
        db=db_session,
        user_id=user.id,
        amount_kobo=1000000,  # ₦10,000
        reference=reference,
        description="Test pending deposit"
    )
    await db_session.commit()
    return transaction, user, wallet


class TestDepositCreation:
    @pytest.mark.asyncio
    async def test_create_pending_deposit_success(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet
        reference = f"deposit_{uuid.uuid4().hex[:12]}"
        amount_kobo = 5000000  # ₦50,000
        
        transaction = await LedgerService.create_pending_deposit(
            db=db_session,
            user_id=user.id,
            amount_kobo=amount_kobo,
            reference=reference,
            description="Paystack deposit via card"
        )
        await db_session.commit()
        
        assert transaction is not None
        assert transaction.reference_id == reference
        assert transaction.status == TransactionStatus.PENDING
        assert transaction.type == TransactionType.DEPOSIT
        assert transaction.amount == Decimal("50000.00")
        assert transaction.currency == "NGN"

        metadata = json.loads(transaction.tx_metadata)
        assert metadata["user_id"] == str(user.id)
        assert metadata["amount_kobo"] == amount_kobo

    @pytest.mark.asyncio
    async def test_create_pending_deposit_minimum_amount(
            self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet
        reference = f"min_deposit_{uuid.uuid4().hex[:12]}"

        transaction = await LedgerService.create_pending_deposit(
            db=db_session,
            user_id=user.id,
            amount_kobo=1000000,  # 1,000,000 kobo = ₦10,000
            reference=reference
        )
        await db_session.commit()
        assert transaction.amount == Decimal("10000.00")

    @pytest.mark.asyncio
    async def test_create_pending_deposit_large_amount(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet
        reference = f"large_deposit_{uuid.uuid4().hex[:12]}"
        
        transaction = await LedgerService.create_pending_deposit(
            db=db_session,
            user_id=user.id,
            amount_kobo=1000000000,  # ₦10,000,000
            reference=reference
        )
        await db_session.commit()
        
        assert transaction.amount == Decimal("10000000.00")

    @pytest.mark.asyncio
    async def test_create_pending_deposit_duplicate_reference_fails(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet
        reference = f"duplicate_test_{uuid.uuid4().hex[:12]}"

        await LedgerService.create_pending_deposit(
            db=db_session,
            user_id=user.id,
            amount_kobo=1000000,
            reference=reference
        )
        await db_session.commit()

        with pytest.raises(es.DuplicateTransactionError) as exc_info:
            await LedgerService.create_pending_deposit(
                db=db_session,
                user_id=user.id,
                amount_kobo=2000000, 
                reference=reference
            )
        
        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_deposit_user_without_wallet_still_creates_pending(
        self, db_session, test_user, system_accounts
    ):
        """ A pending deposit can be created even if user has no wallet yet and all
        I am thinking this is valid because a webhook from paystack might arrive before wallet creation completes and besides
        processing step should fail, but the pending record will still exist for audit
        """
        reference = f"no_wallet_{uuid.uuid4().hex[:12]}"
        
        transaction = await LedgerService.create_pending_deposit(
            db=db_session,
            user_id=test_user.id,
            amount_kobo=1000000,
            reference=reference
        )
        await db_session.commit()
        
        assert transaction.status == TransactionStatus.PENDING


class TestDepositProcessingSuccess:

    @pytest.mark.asyncio
    async def test_process_successful_deposit_credits_user_wallet(
        self, db_session, pending_deposit, system_accounts
    ):
        transaction, user, wallet = pending_deposit
        initial_balance = wallet.balance
        
        processed_tx, credited_amount = await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_TXN_12345"
        )
        await db_session.commit()
        await db_session.refresh(wallet)
        
        assert processed_tx.status == TransactionStatus.SUCCESS
        assert credited_amount == transaction.amount
        assert wallet.balance == initial_balance + transaction.amount

    @pytest.mark.asyncio
    async def test_process_successful_deposit_debits_settlement_account(
        self, db_session, pending_deposit, system_accounts
    ):
        transaction, user, wallet = pending_deposit
        
        settlement_account = next(
            a for a in system_accounts 
            if a.type == AccountType.SYSTEM_BANK_SETTLEMENT
        )
        initial_settlement_balance = settlement_account.balance
        
        await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_TXN_12345"
        )
        await db_session.commit()
        
        await db_session.refresh(settlement_account)
        
        expected_balance = initial_settlement_balance - transaction.amount
        assert settlement_account.balance == expected_balance

    @pytest.mark.asyncio
    async def test_process_successful_deposit_creates_ledger_entries(
        self, db_session, pending_deposit, system_accounts
    ):
        """I want to verify that exactly 2 ledger entries are created """
        transaction, user, wallet = pending_deposit
        
        await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_TXN_12345"
        )
        await db_session.commit()

        result = await db_session.execute(
            select(LedgerEntry).filter(
                LedgerEntry.transaction_id == transaction.id
            )
        )
        entries = result.scalars().all()
        
        assert len(entries) == 2

        directions = {entry.direction for entry in entries}
        assert EntryDirection.CREDIT in directions
        assert EntryDirection.DEBIT in directions

    @pytest.mark.asyncio
    async def test_process_successful_deposit_stores_external_reference(
        self, db_session, pending_deposit, system_accounts
    ):
        transaction, user, wallet = pending_deposit
        paystack_ref = "PAYSTACK_TXN_UNIQUE_123"
        
        processed_tx, _ = await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference=paystack_ref
        )
        await db_session.commit()
        
        assert processed_tx.external_reference == paystack_ref


class TestDoubleEntryIntegrity:
    """
    Total Debits = Total Credits for literally every transaction
    """
    
    @pytest.mark.asyncio
    async def test_debit_equals_credit_for_deposit(
        self, db_session, pending_deposit, system_accounts
    ):
        transaction, user, wallet = pending_deposit
        
        await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_12345"
        )
        await db_session.commit()

        result = await db_session.execute(
            select(LedgerEntry).filter(
                LedgerEntry.transaction_id == transaction.id
            )
        )
        entries = result.scalars().all()
        
        total_debit = sum(
            e.amount for e in entries 
            if e.direction == EntryDirection.DEBIT
        )
        total_credit = sum(
            e.amount for e in entries 
            if e.direction == EntryDirection.CREDIT
        )
        
        assert total_debit == total_credit, \
            f"Double-entry violation! Debits: {total_debit}, Credits: {total_credit}"

    @pytest.mark.asyncio
    async def test_balance_after_matches_actual_balance(
        self, db_session, pending_deposit, system_accounts
    ):
        transaction, user, wallet = pending_deposit
        
        await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_12345"
        )
        await db_session.commit()

        result = await db_session.execute(
            select(LedgerEntry).filter(
                LedgerEntry.transaction_id == transaction.id,
                LedgerEntry.account_id == wallet.id
            )
        )
        credit_entry = result.scalar_one()
        
        await db_session.refresh(wallet)
        
        assert credit_entry.balance_after == wallet.balance

    @pytest.mark.asyncio
    async def test_system_wide_balance_zero_sum(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet

        for i in range(3):
            reference = f"balance_test_{i}_{uuid.uuid4().hex[:8]}"
            tx = await LedgerService.create_pending_deposit(
                db=db_session,
                user_id=user.id,
                amount_kobo=1000000 * (i + 1),  # ₦10k, ₦20k, ₦30k
                reference=reference
            )
            await db_session.commit()

            await LedgerService.process_successful_deposit(
                db=db_session,
                reference=reference,
                paystack_reference=f"PAYSTACK_{i}"
            )
            await db_session.commit()

        credit_result = await db_session.execute(
            select(func.sum(LedgerEntry.amount)).filter(
                LedgerEntry.direction == EntryDirection.CREDIT
            )
        )
        total_credits = credit_result.scalar() or Decimal("0")

        debit_result = await db_session.execute(
            select(func.sum(LedgerEntry.amount)).filter(
                LedgerEntry.direction == EntryDirection.DEBIT
            )
        )
        total_debits = debit_result.scalar() or Decimal("0")

        assert total_credits == total_debits, \
            f"System imbalance detected: Credits={total_credits}, Debits={total_debits}"


class TestTransactionStateMachine:
    @pytest.mark.asyncio
    async def test_pending_to_success_transition(
        self, db_session, pending_deposit, system_accounts
    ):
        """Valid transition: PENDING to SUCCESS."""
        transaction, user, wallet = pending_deposit
        assert transaction.status == TransactionStatus.PENDING
        
        processed, _ = await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_123"
        )
        await db_session.commit()
        
        assert processed.status == TransactionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_pending_to_failed_transition(
        self, db_session, pending_deposit, system_accounts
    ):
        """Valid transition: PENDING to FAILED."""
        transaction, user, wallet = pending_deposit
        
        failed_tx = await LedgerService.process_failed_deposit(
            db=db_session,
            reference=transaction.reference_id,
            reason="Card declined by bank"
        )
        await db_session.commit()
        
        assert failed_tx.status == TransactionStatus.FAILED
        assert "Card declined" in failed_tx.description

    @pytest.mark.asyncio
    async def test_success_cannot_transition_again(
        self, db_session, pending_deposit, system_accounts
    ):
        transaction, user, wallet = pending_deposit

        # First processing succeeds
        await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_123"
        )
        await db_session.commit()
        await db_session.refresh(wallet)

        balance_after_first = wallet.balance
        _, credited = await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_DUPLICATE"
        )
        await db_session.commit()
        await db_session.refresh(wallet)

        assert credited == Decimal("0")
        assert wallet.balance == balance_after_first

    @pytest.mark.asyncio
    async def test_failed_cannot_become_success(
        self, db_session, pending_deposit, system_accounts
    ):
        transaction, user, wallet = pending_deposit
        await LedgerService.process_failed_deposit(
            db=db_session,
            reference=transaction.reference_id,
            reason="Insufficient funds"
        )
        await db_session.commit()
        with pytest.raises(es.InvalidTransactionStateError):
            await LedgerService.process_successful_deposit(
                db=db_session,
                reference=transaction.reference_id,
                paystack_reference="PAYSTACK_LATE"
            )

class TestIdempotency:
    @pytest.mark.asyncio
    async def test_duplicate_webhook_does_not_double_credit(
        self, db_session, pending_deposit, system_accounts
    ):
        transaction, user, wallet = pending_deposit
        
        # First webhook
        _, first_credit = await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_123"
        )
        await db_session.commit()
        
        await db_session.refresh(wallet)
        balance_after_first = wallet.balance

        _, second_credit = await LedgerService.process_successful_deposit(
            db=db_session,
            reference=transaction.reference_id,
            paystack_reference="PAYSTACK_123"
        )
        await db_session.commit()
        
        await db_session.refresh(wallet)
        
        assert second_credit == Decimal("0")  # No additionall credit
        assert wallet.balance == balance_after_first  # Balance unchanged

    @pytest.mark.asyncio
    async def test_ledger_entries_not_duplicated(
        self, db_session, pending_deposit, system_accounts
    ):
        transaction, user, wallet = pending_deposit
        
        # Process multiple times
        for i in range(5):
            await LedgerService.process_successful_deposit(
                db=db_session,
                reference=transaction.reference_id,
                paystack_reference=f"PAYSTACK_{i}"
            )
            await db_session.commit()

        result = await db_session.execute(
            select(func.count(LedgerEntry.id)).filter(
                LedgerEntry.transaction_id == transaction.id
            )
        )
        entry_count = result.scalar()
        # I am hoping this will still be just two entries
        assert entry_count == 2

class TestConcurrencyAndRaceConditions:

    @pytest.mark.asyncio
    async def test_concurrent_deposit_processing_same_reference(
        self, db_session, pending_deposit, system_accounts
    ):
        """
        Trying to simulate a race condition
        """
        transaction, user, wallet = pending_deposit
        async def process_deposit():
            try:
                return await LedgerService.process_successful_deposit(
                    db=db_session,
                    reference=transaction.reference_id,
                    paystack_reference="CONCURRENT_REF"
                )
            except Exception as e:
                return None, Decimal("0")

        results = await asyncio.gather(
            process_deposit(),
            process_deposit(),
            return_exceptions=True
        )
        
        await db_session.commit()
        await db_session.refresh(wallet)
        assert wallet.balance == transaction.amount

    @pytest.mark.asyncio
    async def test_concurrent_pending_deposit_different_references(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet
        
        async def create_and_process(index: int):
            reference = f"concurrent_{index}_{uuid.uuid4().hex[:8]}"
            
            tx = await LedgerService.create_pending_deposit(
                db=db_session,
                user_id=user.id,
                amount_kobo=1000000,  # ₦10,000 each
                reference=reference
            )
            await db_session.flush()
            
            await LedgerService.process_successful_deposit(
                db=db_session,
                reference=reference,
                paystack_reference=f"PAYSTACK_CONC_{index}"
            )
            return tx.amount
        results = []
        for i in range(5):
            amount = await create_and_process(i)
            results.append(amount)
            await db_session.commit()
        
        await db_session.refresh(wallet)

        expected_total = sum(results)
        assert wallet.balance == expected_total


class TestPerformanceFeeCharging:
    @pytest.mark.asyncio
    async def test_charge_performance_fee_success(
        self, db_session, user_with_funded_wallet, system_accounts
    ):
        user, wallet = user_with_funded_wallet
        initial_balance = wallet.balance
        fee_amount = Decimal("5000.00")
        
        transaction = await LedgerService.charge_performance_fee(
            db=db_session,
            user_id=user.id,
            amount=fee_amount,
            trade_reference="TRADE_123",
            description="20% performance fee on profit"
        )
        await db_session.commit()
        
        await db_session.refresh(wallet)
        
        assert transaction.type == TransactionType.PERFORMANCE_FEE
        assert transaction.status == TransactionStatus.SUCCESS
        assert wallet.balance == initial_balance - fee_amount

    @pytest.mark.asyncio
    async def test_charge_performance_fee_credits_revenue_account(
        self, db_session, user_with_funded_wallet, system_accounts
    ):
        user, wallet = user_with_funded_wallet
        fee_amount = Decimal("2500.00")
        
        revenue_account = next(
            a for a in system_accounts 
            if a.type == AccountType.SYSTEM_FEE_WALLET
        )
        initial_revenue = revenue_account.balance
        
        await LedgerService.charge_performance_fee(
            db=db_session,
            user_id=user.id,
            amount=fee_amount,
            trade_reference="TRADE_456"
        )
        await db_session.commit()
        
        await db_session.refresh(revenue_account)
        
        assert revenue_account.balance == initial_revenue + fee_amount

    @pytest.mark.asyncio
    async def test_charge_performance_fee_insufficient_balance_fails(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet  # A Zero balance wallet
        
        with pytest.raises(es.InsufficientFundsError):
            await LedgerService.charge_performance_fee(
                db=db_session,
                user_id=user.id,
                amount=Decimal("1000.00"),
                trade_reference="TRADE_FAIL"
            )

    @pytest.mark.asyncio
    async def test_charge_performance_fee_exact_balance(
        self, db_session, user_with_funded_wallet, system_accounts
    ):
        user, wallet = user_with_funded_wallet
        exact_balance = wallet.balance
        
        transaction = await LedgerService.charge_performance_fee(
            db=db_session,
            user_id=user.id,
            amount=exact_balance,
            trade_reference="TRADE_EXACT"
        )
        await db_session.commit()
        
        await db_session.refresh(wallet)
        
        assert wallet.balance == Decimal("0")
        assert transaction.status == TransactionStatus.SUCCESS


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_process_nonexistent_transaction_fails(
        self, db_session, system_accounts
    ):
        fake_reference = f"NONEXISTENT_{uuid.uuid4().hex}"
        
        with pytest.raises(es.TransactionNotFoundError):
            await LedgerService.process_successful_deposit(
                db=db_session,
                reference=fake_reference,
                paystack_reference="PAYSTACK_123"
            )

    @pytest.mark.asyncio
    async def test_process_deposit_no_wallet_fails(
        self, db_session, test_user, system_accounts
    ):
        reference = f"no_wallet_{uuid.uuid4().hex[:12]}"

        await LedgerService.create_pending_deposit(
            db=db_session,
            user_id=test_user.id,
            amount_kobo=1000000,
            reference=reference
        )
        await db_session.commit()

        with pytest.raises(es.AccountNotFoundError):
            await LedgerService.process_successful_deposit(
                db=db_session,
                reference=reference,
                paystack_reference="PAYSTACK_123"
            )

    @pytest.mark.asyncio
    async def test_get_user_wallet_inactive_wallet_not_returned(
        self, db_session, test_user, system_accounts
    ):

        inactive_wallet = LedgerAccount(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            type=AccountType.USER_LIVE_WALLET,
            name="Inactive Wallet",
            currency="NGN",
            balance=Decimal("10000"),
            is_active=False,
            is_system=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(inactive_wallet)
        await db_session.commit()
        
        wallet = await LedgerService.get_user_wallet(db_session, test_user.id)
        
        assert wallet is None


class TestBalanceCalculations:
    @pytest.mark.asyncio
    async def test_get_user_balance_no_wallet_returns_zero(
        self, db_session, test_user
    ):
        balance = await LedgerService.get_user_balance(db_session, test_user.id)
        
        assert balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_user_balance_with_wallet(
        self, db_session, user_with_funded_wallet
    ):
        user, wallet = user_with_funded_wallet
        
        balance = await LedgerService.get_user_balance(db_session, user.id)
        
        assert balance == wallet.balance

    @pytest.mark.asyncio
    async def test_calculate_balance_from_entries(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet

        for i in range(3):
            reference = f"calc_test_{i}_{uuid.uuid4().hex[:8]}"
            await LedgerService.create_pending_deposit(
                db=db_session,
                user_id=user.id,
                amount_kobo=1000000 * (i + 1),
                reference=reference
            )
            await db_session.commit()

            await LedgerService.process_successful_deposit(
                db=db_session,
                reference=reference,
                paystack_reference=f"PAYSTACK_{i}"
            )
            await db_session.commit()
        await db_session.refresh(wallet)
        actual_balance = wallet.balance
        result = await db_session.execute(
            select(LedgerEntry).filter(LedgerEntry.account_id == wallet.id)
        )
        entries = result.scalars().all()

        calculated = sum(
            e.amount if e.direction == EntryDirection.CREDIT else -e.amount
            for e in entries
        )

        assert calculated == actual_balance


    @pytest.mark.asyncio
    async def test_wallet_summary_includes_all_metrics(
        self, db_session, user_with_funded_wallet, system_accounts
    ):
        user, wallet = user_with_funded_wallet
        
        summary = await LedgerService.get_wallet_summary(db_session, user.id)
        
        assert "balance" in summary
        assert "currency" in summary
        assert "total_deposits" in summary
        assert "total_fees_paid" in summary
        assert "pending_transactions" in summary


class TestTransactionHistory:
    @pytest.mark.asyncio
    async def test_get_transaction_history_empty_wallet(
        self, db_session, test_user
    ):
        entries, total = await LedgerService.get_transaction_history(
            db_session, test_user.id
        )
        
        assert entries == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_transaction_history_pagination(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet

        for i in range(10):
            reference = f"history_test_{i}_{uuid.uuid4().hex[:8]}"
            await LedgerService.create_pending_deposit(
                db=db_session,
                user_id=user.id,
                amount_kobo=1000000,
                reference=reference
            )
            await db_session.commit()
            
            await LedgerService.process_successful_deposit(
                db=db_session,
                reference=reference,
                paystack_reference=f"PAYSTACK_{i}"
            )
            await db_session.commit()

        page1, total = await LedgerService.get_transaction_history(
            db_session, user.id, limit=5, offset=0
        )

        page2, _ = await LedgerService.get_transaction_history(
            db_session, user.id, limit=5, offset=5
        )
        
        assert len(page1) == 5
        assert len(page2) == 5
        assert total == 10


class TestDecimalPrecision:
    @pytest.mark.asyncio
    async def test_kobo_to_naira_conversion_precision(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet
        
        # 12345 kobo = ₦123.45
        reference = f"precision_{uuid.uuid4().hex[:12]}"
        
        transaction = await LedgerService.create_pending_deposit(
            db=db_session,
            user_id=user.id,
            amount_kobo=12345,
            reference=reference
        )
        await db_session.commit()
        
        assert transaction.amount == Decimal("123.45")

    @pytest.mark.asyncio
    async def test_balance_precision_after_multiple_operations(
        self, db_session, user_with_live_wallet, system_accounts
    ):
        user, wallet = user_with_live_wallet
        
        amounts_kobo = [12345, 67890, 11111, 22222, 33333]
        expected_total = Decimal("0")
        
        for i, amount in enumerate(amounts_kobo):
            reference = f"multi_precision_{i}_{uuid.uuid4().hex[:8]}"
            
            tx = await LedgerService.create_pending_deposit(
                db=db_session,
                user_id=user.id,
                amount_kobo=amount,
                reference=reference
            )
            await db_session.commit()
            
            await LedgerService.process_successful_deposit(
                db=db_session,
                reference=reference,
                paystack_reference=f"PAYSTACK_{i}"
            )
            await db_session.commit()
            
            expected_total += Decimal(amount) / Decimal("100")
        
        await db_session.refresh(wallet)
        
        assert wallet.balance == expected_total
