import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from application.models.ledger import Account
from application.models.enums import AccountType
from application.utilities.config import settings


DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

SYSTEM_ACCOUNTS = [
    {
        "type": AccountType.SYSTEM_BANK_BALANCE,
        "name": "Virtual Currency Treasury",
        "currency": "USD",
        "balance": Decimal("0"),
        "description": "Literally central bank for the virtual currency issuance lmao"
    },
    {
        "type": AccountType.SYSTEM_FEE_WALLET,
        "name": "Platform Fee Wallet",
        "currency": "USD",
        "balance": Decimal("0"),
        "description": "Collects performance fees and platform charges"
    },
    {
        "type": AccountType.SYSTEM_BANK_SETTLEMENT,
        "name": "Paystack Settlement Account",
        "currency": "NGN",
        "balance": Decimal("0"),
        "description": "Settlement account for Paystack deposits/withdrawals"
    }
]


async def seed_system_accounts():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        for account_config in SYSTEM_ACCOUNTS:
            result = await db.execute(
                select(Account).filter(
                    Account.type == account_config["type"],
                    Account.is_system == True
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"System account seems to'{account_config['name']}' already exists (ID: {existing.id})")
                continue
            
            new_account = Account(
                id=uuid.uuid4(),
                owner_id=None,
                type=account_config["type"],
                name=account_config["name"],
                currency=account_config["currency"],
                balance=account_config["balance"],
                is_active=True,
                is_system=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_account)
            print(f" Created system account '{account_config['name']}' (ID: {new_account.id})")
        
        await db.commit()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_system_accounts())
