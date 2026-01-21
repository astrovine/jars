import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from application.main import app
from application.models.base import Base, get_db
from application.models import account
from application.models.ledger import Account as LedgerAccount
from application.models.enums import AccountType, UserTier, VerificationStatus
from application.utilities import oauth2

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://jars_user:MOgyWKeMICWSqTARY1TF_eMUJJM4BMEw@db:5432/jars_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        async_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def system_accounts(db_session: AsyncSession):
    accounts = [
        LedgerAccount(
            id=uuid.uuid4(),
            owner_id=None,
            type=AccountType.SYSTEM_BANK_BALANCE,
            name="Virtual Currency Treasury",
            currency="USD",
            balance=Decimal("0"),
            is_active=True,
            is_system=True,
            created_at=datetime.now(timezone.utc)
        ),
        LedgerAccount(
            id=uuid.uuid4(),
            owner_id=None,
            type=AccountType.SYSTEM_FEE_WALLET,
            name="Platform Fee Wallet",
            currency="USD",
            balance=Decimal("0"),
            is_active=True,
            is_system=True,
            created_at=datetime.now(timezone.utc)
        ),
        LedgerAccount(
            id=uuid.uuid4(),
            owner_id=None,
            type=AccountType.SYSTEM_BANK_SETTLEMENT,
            name="Settlement Account",
            currency="NGN",
            balance=Decimal("0"),
            is_active=True,
            is_system=True,
            created_at=datetime.now(timezone.utc)
        )
    ]
    
    for acc in accounts:
        db_session.add(acc)
    
    await db_session.commit()
    return accounts


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    hashed_password = oauth2.get_password_hash("MorningCoffeeYeahhh42!")
    user = account.User(
        id=uuid.uuid4(),
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
        status="VERIFIED",
        password=hashed_password,
        country="NG",
        tier=UserTier.FREE,
        is_active=True,
        is_admin=False,
        is_2fa_enabled=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_with_demo_wallet(db_session: AsyncSession, test_user, system_accounts):
    demo_wallet = LedgerAccount(
        id=uuid.uuid4(),
        owner_id=test_user.id,
        type=AccountType.USER_DEMO_WALLET,
        name=f"{test_user.first_name} {test_user.last_name} Demo",
        currency="USD",
        balance=Decimal("10000"),
        is_active=True,
        is_system=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(demo_wallet)
    await db_session.commit()
    return test_user, demo_wallet


@pytest_asyncio.fixture
async def plus_user(db_session: AsyncSession):
    hashed_password = oauth2.get_password_hash("PlusUserSecret77!")
    user = account.User(
        id=uuid.uuid4(),
        first_name="Plus",
        last_name="User",
        email="plususer@example.com",
        status="VERIFIED",
        password=hashed_password,
        country="NG",
        tier=UserTier.PLUS,
        is_active=True,
        is_admin=False,
        is_2fa_enabled=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    hashed_password = oauth2.get_password_hash("AdminAccess2025!")
    user = account.User(
        id=uuid.uuid4(),
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        status="VERIFIED",
        password=hashed_password,
        country="NG",
        tier=UserTier.FREE,
        is_active=True,
        is_admin=True,
        is_2fa_enabled=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = oauth2.create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(admin_user):
    token = oauth2.create_access_token(str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def valid_user_data():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": f"john.doe{uuid.uuid4().hex[:6]}@example.com",
        "country": "NG",
        "password": "SunnyDay2026!"
    }


@pytest.fixture
def mock_send_email():
    with patch("application.tasks.task_send_verification_email.delay") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_send_welcome_email():
    with patch("application.tasks.task_send_welcome_email.delay") as mock:
        mock.return_value = None
        yield mock
