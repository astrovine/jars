import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import AsyncAdaptedQueuePool

from application.utilities.config import settings

SYNC_DATABASE_URL = f"postgresql+psycopg2://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=sync_engine, class_=Session)

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    echo=settings.DB_ECHO,
    connect_args={
        "command_timeout": 5,
        "server_settings": {
            "jit": "off",
            "statement_timeout": "10000",
        }
    }
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = sqlalchemy.orm.declarative_base()

read_engine = None
AsyncReadSessionLocal = None

if settings.DATABASE_READ_HOST:
    READ_DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_READ_HOST}:{settings.DATABASE_READ_PORT or settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

    read_engine = create_async_engine(
        READ_DATABASE_URL,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=settings.DB_ECHO,
        connect_args={
            "command_timeout": 5,
            "server_settings": {
                "jit": "off",
                "statement_timeout": "10000",
            }
        }
    )

    AsyncReadSessionLocal = sessionmaker(
        read_engine, class_=AsyncSession, expire_on_commit=False
    )


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_read_db():
    if AsyncReadSessionLocal:
        async with AsyncReadSessionLocal() as session:
            yield session
    else:
        async with AsyncSessionLocal() as session:
            yield session