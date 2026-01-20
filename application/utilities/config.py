import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.sql.coercions import expect


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    PRE_AUTH_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    PRIVATE_KEY_PATH: str = "application/certs/private_key.pem"
    PUBLIC_KEY_PATH: str = "application/certs/public_key.pem"
    RESEND_API_KEY: str = ""
    FRONTEND_URL: str = ""
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
    PRIVATE_KEY: str = ""
    PUBLIC_KEY: str = ""
    SUPPORTED_EXCHANGES: list[str]
    MAX_KEYS_PER_EXCHANGE: int
    MAX_TOTAL_KEYS_PER_USER: int
    REDIS_URL: str | None = None
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    PAYSTACK_SECRET_KEY: str = ""
    ENVIRONMENT: str = "development"
    ENCRYPTION_KEY: str = ""
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 10
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True
    DB_ECHO: bool = False
    DATABASE_READ_HOST: str | None = None
    DATABASE_READ_PORT: str | None = None
    VIRTUAL_BALANCE_AMOUNT: int = 10000
    OPEN_EXCHANGE_RATES_API_KEY: str = ""
    BASE_CURRENCY: str = "USD"
    QUOTE_CURRENCY: str = "NGN"
    PLUS_TIER_PRICE_USD: float = 15.00
    BUSINESS_TIER_PRICE_USD: float = 49.00
    FALLBACK_EXCHANGE_RATE: float = 1750.00

    @field_validator('ENCRYPTION_KEY', mode='before')
    @classmethod
    def ensure_encryption_key(cls, value: str) -> str:
        if value and isinstance(value, str) and value.strip():
            return value
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()

    @field_validator('SECRET_KEY', mode='before')
    @classmethod
    def ensure_secret_key(cls, value: str) -> str:
        if value and isinstance(value, str) and value.strip():
            return value
        return os.urandom(32).hex()

    @field_validator('PRIVATE_KEY', mode='before')
    @classmethod
    def load_pk(cls, value: str, info) -> str:
        if value:
            return value
        path = info.data.get("PRIVATE_KEY_PATH", "application/certs/private_key.pem")
        try:
            with open(path, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f"Private Key not found at {path}")

    @field_validator("PUBLIC_KEY", mode="before")
    @classmethod
    def load_public_key(cls, v: str, info) -> str:
        if v:
            return v
        path = info.data.get("PUBLIC_KEY_PATH", "application/certs/public_key.pem")
        try:
            with open(path, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise ValueError(f"Public Key not found at {path}")

settings = Config()