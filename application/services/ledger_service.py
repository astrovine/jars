import uuid
import json
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from application.models.ledger import Account, LedgerTransaction, LedgerEntry
from application.models.enums import AccountType, TransactionType, EntryDirection, TransactionStatus
from application.utilities.audit import setup_logger
from application.utilities import exceptions as es

logger = setup_logger(__name__)


class LedgerService:

    @staticmethod
    async def get_system_account_by_type(db: AsyncSession, account_type: AccountType) -> Account:
        logger.debug(f"[LEDGER] Looking up system account of type: {account_type.value}")
        result = await db.execute(
            select(Account).filter(
                Account.is_system == True,
                Account.type == account_type
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            logger.error(f"[CRITICAL] System account '{account_type.value}' not found - deposits will fail until this is created")
            raise es.SystemAccountNotFoundError(f"System account of type '{account_type.value}' not found.")

        logger.debug(f"[LEDGER] Found system account {account.id} for type {account_type.value}")
        return account

    @staticmethod
    async def get_paystack_settlement_account(db: AsyncSession) -> Account:
        return await LedgerService.get_system_account_by_type(db, AccountType.SYSTEM_BANK_SETTLEMENT)

    @staticmethod
    async def get_jars_revenue_account(db: AsyncSession) -> Account:
        return await LedgerService.get_system_account_by_type(db, AccountType.SYSTEM_FEE_WALLET)

    @staticmethod
    async def get_user_wallet(db: AsyncSession, user_id: uuid.UUID) -> Optional[Account]:
        logger.debug(f"[LEDGER] Looking up wallet for user {user_id}")
        result = await db.execute(
            select(Account).filter(
                Account.owner_id == user_id,
                Account.type == AccountType.USER_LIVE_WALLET,
                Account.is_active == True
            )
        )
        wallet = result.scalar_one_or_none()

        if wallet:
            logger.debug(f"[LEDGER] Found active wallet {wallet.id} for user {user_id}, balance: {wallet.balance} {wallet.currency}")
        else:
            logger.warning(f"[LEDGER] No active wallet found for user {user_id}")

        return wallet

    @staticmethod
    async def calculate_balance(db: AsyncSession, account_id: uuid.UUID) -> Decimal:
        result = await db.execute(
            select(
                func.sum(
                    func.case(
                        (LedgerEntry.direction == EntryDirection.CREDIT, LedgerEntry.amount),
                        else_=-LedgerEntry.amount
                    )
                )
            ).filter(LedgerEntry.account_id == account_id)
        )
        balance = result.scalar()

        return balance or Decimal("0")

    @staticmethod
    async def create_pending_deposit(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount_kobo: int,
        reference: str,
        description: Optional[str] = None
    ) -> LedgerTransaction:
        amount_naira = Decimal(amount_kobo) / Decimal("100")
        logger.info(f"[DEPOSIT INIT] Creating pending deposit for user {user_id} | Amount: ₦{amount_naira:,.2f} | Ref: {reference}")

        result = await db.execute(
            select(LedgerTransaction).filter(
                LedgerTransaction.reference_id == reference
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.error(f"[DUPLICATE BLOCKED] Deposit reference {reference} already exists with status {existing.status}")
            raise es.DuplicateTransactionError(f"Transaction {reference} already exists")

        transaction = LedgerTransaction(
            reference_id=reference,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            amount=amount_naira,
            currency="NGN",
            description=description or "Paystack deposit",
            tx_metadata=json.dumps({"user_id": str(user_id), "amount_kobo": amount_kobo})
        )
        db.add(transaction)
        await db.flush()

        logger.info(f"[DEPOSIT PENDING] Transaction {transaction.id} created | User: {user_id} | Amount: ₦{amount_naira:,.2f} | Ref: {reference}")
        return transaction

    @staticmethod
    async def process_successful_deposit(
        db: AsyncSession,
        reference: str,
        paystack_reference: str
    ) -> Tuple[LedgerTransaction, Decimal]:
        logger.info(f"[DEPOSIT PROCESSING] Starting to process deposit | Ref: {reference} | Paystack ID: {paystack_reference}")

        result = await db.execute(
            select(LedgerTransaction).filter(
                LedgerTransaction.reference_id == reference
            )
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            logger.error(f"[DEPOSIT FAILED] Transaction not found in database | Ref: {reference}")
            raise es.TransactionNotFoundError(f"Transaction {reference} not found")

        if transaction.status == TransactionStatus.SUCCESS:
            logger.warning(f"[DUPLICATE WEBHOOK] Transaction {reference} was already processed - ignoring duplicate")
            return transaction, Decimal("0")

        if transaction.status != TransactionStatus.PENDING:
            logger.error(f"[INVALID STATE] Cannot process transaction {reference} - current status is {transaction.status.value}")
            raise es.InvalidTransactionStateError(f"Transaction {reference} is in invalid state: {transaction.status}")

        tx_meta = json.loads(transaction.tx_metadata) if transaction.tx_metadata else {}
        user_id = uuid.UUID(tx_meta.get("user_id"))
        logger.info(f"[DEPOSIT] Crediting user {user_id} with ₦{transaction.amount:,.2f}")

        user_wallet = await LedgerService.get_user_wallet(db, user_id)
        if not user_wallet:
            logger.error(f"[DEPOSIT FAILED] User {user_id} has no active wallet - cannot credit funds")
            raise es.AccountNotFoundError(f"Wallet not found for user {user_id}")

        paystack_account = await LedgerService.get_paystack_settlement_account(db)

        old_user_balance = user_wallet.balance
        old_paystack_balance = paystack_account.balance

        credit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=user_wallet.id,
            direction=EntryDirection.CREDIT,
            amount=transaction.amount,
            balance_after=user_wallet.balance + transaction.amount
        )

        debit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=paystack_account.id,
            direction=EntryDirection.DEBIT,
            amount=transaction.amount,
            balance_after=paystack_account.balance - transaction.amount
        )

        user_wallet.balance = user_wallet.balance + transaction.amount
        paystack_account.balance = paystack_account.balance - transaction.amount

        transaction.status = TransactionStatus.SUCCESS
        transaction.external_reference = paystack_reference

        db.add(credit_entry)
        db.add(debit_entry)
        await db.flush()

        logger.info(
            f"[DEPOSIT SUCCESS] ₦{transaction.amount:,.2f} credited to user {user_id} | "
            f"Ref: {reference} | User balance: ₦{old_user_balance:,.2f} → ₦{user_wallet.balance:,.2f}"
        )
        logger.info(
            f"[DOUBLE-ENTRY] Debit Paystack settlement account | "
            f"Balance: ₦{old_paystack_balance:,.2f} → ₦{paystack_account.balance:,.2f}"
        )

        return transaction, transaction.amount

    @staticmethod
    async def process_failed_deposit(db: AsyncSession, reference: str, reason: str) -> LedgerTransaction:
        logger.warning(f"[DEPOSIT FAILED] Processing failed deposit | Ref: {reference} | Reason: {reason}")

        result = await db.execute(
            select(LedgerTransaction).filter(
                LedgerTransaction.reference_id == reference
            )
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            logger.error(f"[DEPOSIT FAILED] Transaction not found | Ref: {reference}")
            raise es.TransactionNotFoundError(f"Transaction {reference} not found")

        if transaction.status != TransactionStatus.PENDING:
            logger.warning(f"[DEPOSIT] Cannot mark as failed - transaction {reference} is already {transaction.status.value}")
            return transaction

        transaction.status = TransactionStatus.FAILED
        transaction.description = f"{transaction.description} | Failed: {reason}"
        await db.flush()

        tx_meta = json.loads(transaction.tx_metadata) if transaction.tx_metadata else {}
        user_id = tx_meta.get("user_id", "unknown")

        logger.warning(
            f"[DEPOSIT MARKED FAILED] User: {user_id} | Amount: ₦{transaction.amount:,.2f} | "
            f"Ref: {reference} | Reason: {reason}"
        )
        return transaction

    @staticmethod
    async def charge_performance_fee(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: Decimal,
        trade_reference: str,
        description: Optional[str] = None
    ) -> LedgerTransaction:
        reference = f"fee_{trade_reference}_{uuid.uuid4().hex[:8]}"

        result = await db.execute(
            select(LedgerTransaction).filter(
                LedgerTransaction.reference_id == reference
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise es.DuplicateTransactionError(f"Fee transaction {reference} already exists")

        user_wallet = await LedgerService.get_user_wallet(db, user_id)
        if not user_wallet:
            raise es.AccountNotFoundError(f"Wallet not found for user {user_id}")

        if user_wallet.balance < amount:
            raise es.InsufficientFundsError(f"Insufficient balance: {user_wallet.balance} < {amount}")

        jars_revenue = await LedgerService.get_jars_revenue_account(db)

        transaction = LedgerTransaction(
            reference_id=reference,
            type=TransactionType.PERFORMANCE_FEE,
            status=TransactionStatus.SUCCESS,
            amount=amount,
            currency="NGN",
            description=description or f"Performance fee for trade {trade_reference}"
        )
        db.add(transaction)
        await db.flush()

        debit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=user_wallet.id,
            direction=EntryDirection.DEBIT,
            amount=amount,
            balance_after=user_wallet.balance - amount
        )

        credit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=jars_revenue.id,
            direction=EntryDirection.CREDIT,
            amount=amount,
            balance_after=jars_revenue.balance + amount
        )

        user_wallet.balance = user_wallet.balance - amount
        jars_revenue.balance = jars_revenue.balance + amount

        db.add(debit_entry)
        db.add(credit_entry)
        await db.flush()

        logger.info(f"Charged performance fee {amount} NGN from user {user_id}")
        return transaction

    @staticmethod
    async def get_user_balance(db: AsyncSession, user_id: uuid.UUID) -> Decimal:
        wallet = await LedgerService.get_user_wallet(db, user_id)
        if not wallet:
            return Decimal("0")
        return wallet.balance

    @staticmethod
    async def get_wallet_info(db: AsyncSession, user_id: uuid.UUID) -> Optional[dict]:
        wallet = await LedgerService.get_user_wallet(db, user_id)
        if not wallet:
            return None
        return {
            "balance": wallet.balance,
            "currency": wallet.currency,
            "account_id": wallet.id,
            "is_active": wallet.is_active
        }

    @staticmethod
    async def get_wallet_summary(db: AsyncSession, user_id: uuid.UUID) -> dict:
        wallet = await LedgerService.get_user_wallet(db, user_id)
        if not wallet:
            return {
                "balance": Decimal("0"),
                "currency": "NGN",
                "total_deposits": Decimal("0"),
                "total_fees_paid": Decimal("0"),
                "pending_transactions": 0
            }

        deposits_result = await db.execute(
            select(func.sum(LedgerEntry.amount)).filter(
                LedgerEntry.account_id == wallet.id,
                LedgerEntry.direction == EntryDirection.CREDIT
            )
        )
        total_deposits = deposits_result.scalar() or Decimal("0")

        fees_result = await db.execute(
            select(func.sum(LedgerEntry.amount)).filter(
                LedgerEntry.account_id == wallet.id,
                LedgerEntry.direction == EntryDirection.DEBIT
            )
        )
        total_fees = fees_result.scalar() or Decimal("0")

        pending_result = await db.execute(
            select(func.count(LedgerTransaction.id)).filter(
                LedgerTransaction.status == TransactionStatus.PENDING,
                LedgerTransaction.tx_metadata.contains(str(user_id))
            )
        )
        pending_count = pending_result.scalar() or 0

        return {
            "balance": wallet.balance,
            "currency": wallet.currency,
            "total_deposits": total_deposits,
            "total_fees_paid": total_fees,
            "pending_transactions": pending_count
        }

    @staticmethod
    async def get_transaction_history(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[list, int]:
        wallet = await LedgerService.get_user_wallet(db, user_id)
        if not wallet:
            return [], 0

        count_result = await db.execute(
            select(func.count(LedgerEntry.id)).filter(
                LedgerEntry.account_id == wallet.id
            )
        )
        total = count_result.scalar() or 0

        entries_result = await db.execute(
            select(LedgerEntry).filter(
                LedgerEntry.account_id == wallet.id
            ).order_by(LedgerEntry.created_at.desc()).offset(offset).limit(limit)
        )
        entries = entries_result.scalars().all()

        return entries, total

    @staticmethod
    async def get_transaction_by_reference(db: AsyncSession, reference: str) -> Optional[LedgerTransaction]:
        result = await db.execute(
            select(LedgerTransaction).filter(
                LedgerTransaction.reference_id == reference
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def fund_demo_wallet(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: Decimal
    ) -> LedgerTransaction:
        logger.info(f"[DEMO FUNDING] Funding demo wallet for user {user_id} | Amount: ₦{amount:,.2f}")

        user_demo_wallet = await db.execute(
            select(Account).filter(
                Account.owner_id == user_id,
                Account.type == AccountType.USER_DEMO_WALLET,
                Account.is_active == True
            )
        )
        wallet = user_demo_wallet.scalar_one_or_none()

        if not wallet:
            logger.error(f"[DEMO FUNDING FAILED] No active demo wallet found for user {user_id}")
            raise es.AccountNotFoundError(f"Demo wallet not found for user {user_id}")
        
        system_bank_account = await LedgerService.get_system_account_by_type(db, AccountType.SYSTEM_BANK_BALANCE)

        reference = f"demo_fund_{uuid.uuid4().hex[:12]}"

        transaction = LedgerTransaction(
            reference_id=reference,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.SUCCESS,
            amount=amount,
            currency="NGN",
            description="Wallet funding for demo account"
        )
        db.add(transaction)
        await db.flush()

        debit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=system_bank_account.id,
            direction=EntryDirection.DEBIT,
            amount=amount,
            balance_after=system_bank_account.balance - amount
        )
        system_bank_account.balance = system_bank_account.balance - amount

        credit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=wallet.id,
            direction=EntryDirection.CREDIT,
            amount=amount,
            balance_after=wallet.balance + amount
        )

        wallet.balance = wallet.balance + amount

        db.add(credit_entry)
        db.add(debit_entry)
        await db.flush()

        logger.info(f"[DEMO FUNDING SUCCESS] ₦{amount:,.2f} credited to demo wallet of user {user_id} | New balance: ₦{wallet.balance:,.2f}")
        return transaction

    @staticmethod
    async def issue_virtual_balance(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: Decimal = Decimal("10000")
    ) -> LedgerTransaction:
        from application.models.account import User
        
        logger.info(f"[VIRTUAL ISSUANCE] Issuing {amount} V-USDT to user {user_id}")

        wallet_result = await db.execute(
            select(Account).filter(
                Account.owner_id == user_id,
                Account.type == AccountType.USER_DEMO_WALLET,
                Account.is_active == True
            )
        )
        wallet = wallet_result.scalar_one_or_none()

        if not wallet:
            raise es.AccountNotFoundError(f"Demo wallet not found for user {user_id}")

        system_treasury = await LedgerService.get_system_account_by_type(db, AccountType.SYSTEM_BANK_BALANCE)

        reference = f"virtual_issue_{user_id.hex[:8]}_{uuid.uuid4().hex[:8]}"

        transaction = LedgerTransaction(
            reference_id=reference,
            type=TransactionType.VIRTUAL_ISSUANCE,
            status=TransactionStatus.SUCCESS,
            amount=amount,
            currency="USD",
            description="Initial virtual balance issuance"
        )
        db.add(transaction)
        await db.flush()

        debit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=system_treasury.id,
            direction=EntryDirection.DEBIT,
            amount=amount,
            balance_after=system_treasury.balance - amount
        )
        system_treasury.balance = system_treasury.balance - amount

        credit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=wallet.id,
            direction=EntryDirection.CREDIT,
            amount=amount,
            balance_after=wallet.balance + amount
        )
        wallet.balance = wallet.balance + amount

        db.add(debit_entry)
        db.add(credit_entry)
        await db.flush()

        logger.info(f"[VIRTUAL ISSUANCE SUCCESS] {amount} V-USDT issued to user {user_id} | New balance: {wallet.balance}")
        return transaction

    @staticmethod
    async def check_reset_eligibility(db: AsyncSession, user_id: uuid.UUID) -> dict:
        from application.models.account import User
        from datetime import datetime, timezone, timedelta

        user_result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise es.UserNotFoundError(f"User {user_id} not found")

        wallet_result = await db.execute(
            select(Account).filter(
                Account.owner_id == user_id,
                Account.type == AccountType.USER_DEMO_WALLET
            )
        )
        wallet = wallet_result.scalar_one_or_none()
        
        current_balance = wallet.balance if wallet else Decimal("0")
        is_blown = current_balance <= Decimal("0")
        
        last_reset = user.virtual_balance_reset_at
        days_since_reset = None
        free_reset_available = False
        free_reset_date = None
        
        if last_reset:
            days_since_reset = (datetime.now(timezone.utc) - last_reset).days
            free_reset_available = days_since_reset >= 30
            if not free_reset_available:
                free_reset_date = last_reset + timedelta(days=30)
        else:
            free_reset_available = True

        return {
            "current_balance": current_balance,
            "is_blown": is_blown,
            "free_reset_available": free_reset_available,
            "free_reset_date": free_reset_date,
            "days_since_last_reset": days_since_reset,
            "paid_reset_cost_usd": Decimal("5.00")
        }

    @staticmethod
    async def reset_virtual_balance(
        db: AsyncSession,
        user_id: uuid.UUID,
        is_paid: bool = False,
        reset_amount: Decimal = Decimal("10000")
    ) -> LedgerTransaction:
        from application.models.account import User
        from datetime import datetime, timezone

        eligibility = await LedgerService.check_reset_eligibility(db, user_id)
        
        if not is_paid and not eligibility["free_reset_available"]:
            raise es.InvalidRequestError(
                f"Free reset not available. Next free reset: {eligibility['free_reset_date']}"
            )

        wallet_result = await db.execute(
            select(Account).filter(
                Account.owner_id == user_id,
                Account.type == AccountType.USER_DEMO_WALLET,
                Account.is_active == True
            )
        )
        wallet = wallet_result.scalar_one_or_none()

        if not wallet:
            raise es.AccountNotFoundError(f"Demo wallet not found for user {user_id}")

        system_treasury = await LedgerService.get_system_account_by_type(db, AccountType.SYSTEM_BANK_BALANCE)

        tx_type = TransactionType.VIRTUAL_RESET if is_paid else TransactionType.VIRTUAL_RESET_FREE
        reference = f"virtual_reset_{user_id.hex[:8]}_{uuid.uuid4().hex[:8]}"

        current_balance = wallet.balance
        adjustment = reset_amount - current_balance

        transaction = LedgerTransaction(
            reference_id=reference,
            type=tx_type,
            status=TransactionStatus.SUCCESS,
            amount=abs(adjustment),
            currency="USD",
            description=f"Virtual balance reset ({'paid' if is_paid else 'free'})"
        )
        db.add(transaction)
        await db.flush()

        if adjustment > 0:
            debit_entry = LedgerEntry(
                transaction_id=transaction.id,
                account_id=system_treasury.id,
                direction=EntryDirection.DEBIT,
                amount=adjustment,
                balance_after=system_treasury.balance - adjustment
            )
            system_treasury.balance = system_treasury.balance - adjustment

            credit_entry = LedgerEntry(
                transaction_id=transaction.id,
                account_id=wallet.id,
                direction=EntryDirection.CREDIT,
                amount=adjustment,
                balance_after=reset_amount
            )
            wallet.balance = reset_amount

            db.add(debit_entry)
            db.add(credit_entry)
        elif adjustment < 0:
            credit_entry = LedgerEntry(
                transaction_id=transaction.id,
                account_id=system_treasury.id,
                direction=EntryDirection.CREDIT,
                amount=abs(adjustment),
                balance_after=system_treasury.balance + abs(adjustment)
            )
            system_treasury.balance = system_treasury.balance + abs(adjustment)

            debit_entry = LedgerEntry(
                transaction_id=transaction.id,
                account_id=wallet.id,
                direction=EntryDirection.DEBIT,
                amount=abs(adjustment),
                balance_after=reset_amount
            )
            wallet.balance = reset_amount

            db.add(debit_entry)
            db.add(credit_entry)

        user_result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        user.virtual_balance_reset_at = datetime.now(timezone.utc)
        user.virtual_balance_blown_at = None

        await db.flush()

        logger.info(f"[VIRTUAL RESET] User {user_id} balance reset to {reset_amount} V-USDT ({'paid' if is_paid else 'free'})")
        return transaction

    @staticmethod
    def process_successful_deposit_sync(db, reference: str, paystack_reference: str) -> Tuple[LedgerTransaction, Decimal]:
        logger.info(f"[SYNC DEPOSIT] Processing | Ref: {reference}")

        result = db.execute(
            select(LedgerTransaction).filter(LedgerTransaction.reference_id == reference)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise es.TransactionNotFoundError(f"Transaction {reference} not found")

        if transaction.status == TransactionStatus.SUCCESS:
            logger.warning(f"[DUPLICATE WEBHOOK] Transaction {reference} already processed")
            return transaction, Decimal("0")

        if transaction.status != TransactionStatus.PENDING:
            raise es.InvalidTransactionStateError(f"Transaction {reference} is {transaction.status}")

        tx_meta = json.loads(transaction.tx_metadata) if transaction.tx_metadata else {}
        user_id = uuid.UUID(tx_meta.get("user_id"))

        wallet_result = db.execute(
            select(Account).filter(
                Account.owner_id == user_id,
                Account.type == AccountType.USER_LIVE_WALLET,
                Account.is_active == True
            )
        )
        user_wallet = wallet_result.scalar_one_or_none()
        if not user_wallet:
            raise es.AccountNotFoundError(f"Wallet not found for user {user_id}")

        settlement_result = db.execute(
            select(Account).filter(
                Account.is_system == True,
                Account.type == AccountType.SYSTEM_BANK_SETTLEMENT
            )
        )
        paystack_account = settlement_result.scalar_one_or_none()
        if not paystack_account:
            raise es.SystemAccountNotFoundError("SYSTEM_BANK_SETTLEMENT")

        credit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=user_wallet.id,
            direction=EntryDirection.CREDIT,
            amount=transaction.amount,
            balance_after=user_wallet.balance + transaction.amount
        )

        debit_entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=paystack_account.id,
            direction=EntryDirection.DEBIT,
            amount=transaction.amount,
            balance_after=paystack_account.balance - transaction.amount
        )

        user_wallet.balance = user_wallet.balance + transaction.amount
        paystack_account.balance = paystack_account.balance - transaction.amount
        transaction.status = TransactionStatus.SUCCESS
        transaction.external_reference = paystack_reference

        db.add(credit_entry)
        db.add(debit_entry)
        db.flush()

        logger.info(f"[SYNC DEPOSIT SUCCESS] ₦{transaction.amount:,.2f} credited | User: {user_id} | Ref: {reference}")
        return transaction, transaction.amount

    @staticmethod
    def process_failed_deposit_sync(db, reference: str, reason: str) -> LedgerTransaction:
        logger.warning(f"[SYNC DEPOSIT FAILED] Ref: {reference} | Reason: {reason}")

        result = db.execute(
            select(LedgerTransaction).filter(LedgerTransaction.reference_id == reference)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise es.TransactionNotFoundError(f"Transaction {reference} not found")

        if transaction.status != TransactionStatus.PENDING:
            return transaction

        transaction.status = TransactionStatus.FAILED
        transaction.description = f"{transaction.description} | Failed: {reason}"
        db.flush()

        logger.warning(f"[SYNC DEPOSIT MARKED FAILED] Ref: {reference}")
        return transaction
