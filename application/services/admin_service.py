from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from application.schemas import ledger as l
from application.utilities import exceptions as es, audit
from application.models.ledger import Account
from application.models.enums import AccountType

logger = audit.setup_logger(__name__)


class AdminService:
    @staticmethod
    async def create_new_systems_account(db: AsyncSession, account: l.CreatNewAccount, admin_id: UUID) -> Account:
        logger.info(f"[ADMIN ACTION] Admin {admin_id} is attempting to create system account of type '{account.type}'")

        try:
            account_type = AccountType(account.type.lower()) if isinstance(account.type, str) else account.type
        except ValueError:
            logger.error(f"[VALIDATION ERROR] Invalid account type '{account.type}' provided by admin {admin_id}")
            raise es.InvalidRequestError(f"Invalid account type: {account.type}")

        result = await db.execute(
            select(Account).filter(
                Account.type == account_type,
                Account.is_system == True
            )
        )
        existing_account = result.scalar_one_or_none()

        if existing_account:
            logger.warning(
                f"[DUPLICATE BLOCKED] Admin {admin_id} tried to create duplicate system account. "
                f"Type '{account_type.value}' already exists with ID {existing_account.id}"
            )
            raise es.AccountAlreadyExistsError(f"System account of type {account.type} already exists")

        new_account = Account(
            owner_id=None,
            type=account_type,
            name=f'System {account_type.value}',
            currency=account.currency,
            balance=0,
            is_active=True,
            is_system=True
        )
        db.add(new_account)
        await db.flush()

        logger.info(
            f"[SYSTEM ACCOUNT CREATED] Admin {admin_id} successfully created system account. "
            f"Type: {account_type.value}, ID: {new_account.id}, Currency: {account.currency}"
        )

        return new_account
