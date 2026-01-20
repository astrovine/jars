import datetime
import uuid
import ccxt
from typing import Optional, Union, List, Any, Dict
from datetime import datetime, timezone
from application.utilities.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from application.models import keys, account
from application.utilities.audit import setup_logger
from application.schemas import keys as K
from application.utilities import exceptions as es
from application.utilities.oauth2 import encrypt_api_secret, decrypt_api_secret

logger = setup_logger(__name__)


class ExchangeKeysService:
    SUPPORTED_EXCHANGES = settings.SUPPORTED_EXCHANGES
    MAX_KEYS_PER_EXCHANGE = settings.MAX_KEYS_PER_EXCHANGE
    MAX_TOTAL_KEYS_PER_USER = settings.MAX_TOTAL_KEYS_PER_USER

    @staticmethod
    def _verify_exchange_connectivity(
            exchange_name: str,
            api_key: str,
            api_secret: str
    ) -> Dict[str, bool]:
        try:
            if exchange_name not in ExchangeKeysService.SUPPORTED_EXCHANGES:
                raise es.InvalidRequestError(f"Exchange {exchange_name} not supported")

            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'},
                'timeout': 10000
            })

            balance = exchange.fetch_balance()

            permissions = exchange.check_required_credentials() if hasattr(exchange,
                                                                           'check_required_credentials') else {}

            can_trade = True
            can_withdraw = False

            try:
                account_info = exchange.fetch_accounts() if hasattr(exchange, 'fetch_accounts') else None
                if account_info or balance:
                    can_trade = True
            except:
                can_trade = False

            logger.info(f"Successfully verified {exchange_name} API key")

            return {
                'is_valid': True,
                'can_trade': can_trade,
                'can_withdraw': can_withdraw
            }

        except ccxt.PermissionDenied as e:
            logger.warning(f"Permission denied for {exchange_name}: {str(e)}")
            raise es.APIKeyInvalidError()
        except ccxt.AuthenticationError as e:
            logger.warning(f"Authentication failed for {exchange_name}: {str(e)}")
            raise es.APIKeyInvalidError()
        except ccxt.NetworkError as e:
            logger.error(f"Network error verifying {exchange_name}: {str(e)}")
            raise es.ExchangeConnectionError(f"Failed to connect to {exchange_name}")
        except Exception as e:
            logger.error(f"Unexpected error verifying {exchange_name}: {e}", exc_info=True)
            raise es.ExchangeVerificationError(f"Verification failed: {str(e)}")

    @staticmethod
    async def _check_duplicate_key(db: AsyncSession, user_id: uuid.UUID, exchange_name: str, api_key: str) -> bool:
        result = await db.execute(
            select(keys.ExchangeKey).filter(
                keys.ExchangeKey.user_id == user_id,
                keys.ExchangeKey.exchange_name == exchange_name,
                keys.ExchangeKey.api_key == api_key
            )
        )
        existing = result.scalar_one_or_none()
        return existing is not None

    @staticmethod
    async def create_exchange_key(db: AsyncSession, key: K.ExchangeKeyCreate, user_id: uuid.UUID) -> keys.ExchangeKey:
        result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise es.UserNotFoundError("User not found")

        count_result = await db.execute(
            select(keys.ExchangeKey).filter(
                keys.ExchangeKey.user_id == user_id,
                keys.ExchangeKey.exchange_name == key.exchange_name
            )
        )
        existing_count = len(count_result.scalars().all())

        if existing_count >= 3:
            raise es.APIKeyCreationError("User already has 3 API keys")
        if await ExchangeKeysService._check_duplicate_key(db, user_id, key.exchange_name, key.api_key):
            raise es.DuplicateAPIKeyError("This API key is already registered")
        ExchangeKeysService._verify_exchange_connectivity(
            key.exchange_name,
            key.api_key,
            key.api_secret
        )

        encrypted_secret = encrypt_api_secret(key.api_secret)
        new_key = keys.ExchangeKey(
            user_id=user.id,
            exchange_name=key.exchange_name,
            api_key=key.api_key,
            api_secret_encrypted=encrypted_secret,
            label=key.label,
            is_valid=True,
            created_at=datetime.now(timezone.utc),
            last_verified_at=datetime.now(timezone.utc)
        )

        db.add(new_key)
        await db.flush()
        await db.refresh(new_key)
        return new_key

    @staticmethod
    async def get_exchange_keys(
        db: AsyncSession,
        user_id: uuid.UUID,
        key_id: Optional[uuid.UUID] = None,
        exchange: Optional[str] = None
    ) -> Union[keys.ExchangeKey, List[keys.ExchangeKey]]:

        query = select(keys.ExchangeKey).filter(keys.ExchangeKey.user_id == user_id)

        if key_id:
            query = query.filter(keys.ExchangeKey.id == key_id)
            result = await db.execute(query)
            key = result.scalar_one_or_none()
            if not key:
                raise es.APIKeyNotFoundError()
            return key

        if exchange:
            query = query.filter(keys.ExchangeKey.exchange_name == exchange)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_exchange_key(db: AsyncSession, key_id: uuid.UUID, update_data: K.ExchangeKeyUpdate, user_id: uuid.UUID) -> keys.ExchangeKey:
        result = await db.execute(
            select(keys.ExchangeKey).filter(
                keys.ExchangeKey.id == key_id,
                keys.ExchangeKey.user_id == user_id
            )
        )
        exchange_key = result.scalar_one_or_none()

        if not exchange_key:
            raise es.APIKeyNotFoundError()

        update_dict = update_data.model_dump(exclude_unset=True)

        if "api_key" in update_dict or "api_secret" in update_dict:
            new_key = update_dict.get("api_key", exchange_key.api_key)
            new_secret = update_dict.get("api_secret")

            if not new_secret:
                new_secret = decrypt_api_secret(exchange_key.api_secret_encrypted)

            ExchangeKeysService._verify_exchange_connectivity(
                exchange_key.exchange_name,
                new_key,
                new_secret
            )

            if "api_secret" in update_dict:
                 update_dict["api_secret_encrypted"] = encrypt_api_secret(update_dict.pop("api_secret"))

        for key, value in update_dict.items():
            setattr(exchange_key, key, value)

        await db.flush()
        await db.refresh(exchange_key)
        return exchange_key

    @staticmethod
    async def delete_exchange_key(db: AsyncSession, key_id: uuid.UUID, user_id: uuid.UUID) -> None:
        result = await db.execute(
            select(keys.ExchangeKey).filter(
                keys.ExchangeKey.id == key_id,
                keys.ExchangeKey.user_id == user_id
            )
        )
        exchange_key = result.scalar_one_or_none()

        if not exchange_key:
            raise es.APIKeyNotFoundError()

        await db.delete(exchange_key)

    @staticmethod
    async def test_exchange_key(db: AsyncSession, key_id: uuid.UUID, user_id: uuid.UUID) -> Any:
        result = await db.execute(
            select(keys.ExchangeKey).filter(
                keys.ExchangeKey.id == key_id,
                keys.ExchangeKey.user_id == user_id
            )
        )
        key = result.scalar_one_or_none()

        if not key:
            raise es.APIKeyNotFoundError()

        try:
            decrypted_secret = decrypt_api_secret(key.api_secret_encrypted)

            ExchangeKeysService._verify_exchange_connectivity(
                key.exchange_name,
                key.api_key,
                decrypted_secret
            )

            key.is_valid = True
            await db.flush()

            return K.ExchangeKeyTestResult(
                is_valid=True,
                can_trade=True,
                can_withdraw=False,
                message="Connection successful"
            )

        except es.APIKeyInvalidError:
            key.is_valid = False
            await db.flush()

            return K.ExchangeKeyTestResult(
                is_valid=False,
                can_trade=False,
                can_withdraw=False,
                message="Invalid API credentials"
            )
        except Exception as e:
            key.is_valid = False
            await db.flush()
            logger.error(f"Failed to test exchange key: {e}", exc_info=True)

            return K.ExchangeKeyTestResult(
                is_valid=False,
                can_trade=False,
                can_withdraw=False,
                message=f"Test failed: {str(e)}"
            )
