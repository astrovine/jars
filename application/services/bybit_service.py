import uuid
import asyncio
from decimal import Decimal
from typing import Optional, Tuple, Dict
import ccxt
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from application.models.keys import ExchangeKey
from application.utilities.audit import setup_logger
from application.utilities import exceptions as es
from application.utilities.oauth2 import decrypt_api_secret
from application.utilities.config import settings

logger = setup_logger(__name__)

BYBIT_MIN_ORDER_SIZE = Decimal("5.00")
BALANCE_CACHE_TTL = 10


class BybitService:
    _redis_client: Optional[redis.Redis] = None
    
    @classmethod
    async def _get_redis(cls) -> redis.Redis:
        if cls._redis_client is None:
            cls._redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return cls._redis_client
    
    @staticmethod
    def _get_bybit_client(api_key: str, api_secret: str, testnet: bool = False) -> ccxt.bybit:
        return ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'adjustForTimeDifference': True,
            },
            'sandbox': testnet,
            'timeout': 15000,
        })
    
    @staticmethod
    async def get_user_exchange_key(
        db: AsyncSession, 
        user_id: uuid.UUID,
        exchange_name: str = "bybit"
    ) -> Optional[ExchangeKey]:
        result = await db.execute(
            select(ExchangeKey).filter(
                ExchangeKey.user_id == user_id,
                ExchangeKey.exchange_name == exchange_name,
                ExchangeKey.is_valid == True
            ).limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    def _sync_get_wallet_balance(api_key: str, api_secret: str, testnet: bool = False) -> Dict[str, Decimal]:
        try:
            client = BybitService._get_bybit_client(api_key, api_secret, testnet)
            balance = client.fetch_balance()
            result = {}
            for currency in ['USDT', 'BTC', 'ETH']:
                if currency in balance:
                    free = balance[currency].get('free', 0)
                    result[currency] = Decimal(str(free)) if free else Decimal('0')
            
            logger.info(f"Fetched Bybit balance: USDT={result.get('USDT', 0)}")
            return result
            
        except ccxt.AuthenticationError as e:
            logger.warning(f"Bybit auth failed: {e}")
            raise es.APIKeyInvalidError()
        except ccxt.NetworkError as e:
            logger.error(f"Bybit network error: {e}")
            raise es.ExchangeConnectionError("Failed to connect to Bybit")
        except Exception as e:
            logger.error(f"Bybit balance fetch error: {e}", exc_info=True)
            raise es.ExchangeConnectionError(f"Bybit error: {str(e)}")
    
    @staticmethod
    def _sync_verify_permissions(api_key: str, api_secret: str, testnet: bool = False) -> Dict[str, bool]:
        try:
            client = BybitService._get_bybit_client(api_key, api_secret, testnet)
            can_read = False
            try:
                client.fetch_balance()
                can_read = True
            except:
                pass
            return {
                'can_read': can_read,
                'can_trade': can_read,
                'can_withdraw': False,
            }
        except Exception as e:
            logger.error(f"Failed to verify Bybit permissions: {e}")
            return {'can_read': False, 'can_trade': False, 'can_withdraw': False}
    
    @staticmethod
    async def get_wallet_balance_async(api_key: str, api_secret: str, testnet: bool = False) -> Dict[str, Decimal]:
        return await asyncio.to_thread(
            BybitService._sync_get_wallet_balance, api_key, api_secret, testnet
        )
    
    @staticmethod
    async def verify_api_permissions_async(api_key: str, api_secret: str, testnet: bool = False) -> Dict[str, bool]:
        return await asyncio.to_thread(
            BybitService._sync_verify_permissions, api_key, api_secret, testnet
        )
    
    @staticmethod
    async def get_cached_usdt_balance(
        db: AsyncSession,
        user_id: uuid.UUID,
        testnet: bool = False,
        ttl: int = BALANCE_CACHE_TTL
    ) -> Decimal:
        cache_key = f"bybit:balance:{user_id}:{'testnet' if testnet else 'mainnet'}"
        
        try:
            redis_client = await BybitService._get_redis()
            cached = await redis_client.get(cache_key)
            
            if cached is not None:
                logger.debug(f"Cache HIT for user {user_id} balance: ${cached}")
                return Decimal(cached)
        except Exception as e:
            logger.warning(f"Redis cache error (continuing without cache): {e}")
        
        key = await BybitService.get_user_exchange_key(db, user_id)
        if not key:
            logger.warning(f"No valid Bybit key found for user {user_id}")
            raise es.APIKeyNotFoundError()
        
        decrypted_secret = decrypt_api_secret(key.api_secret_encrypted)
        balances = await BybitService.get_wallet_balance_async(key.api_key, decrypted_secret, testnet)
        usdt_balance = balances.get('USDT', Decimal('0'))
        
        try:
            redis_client = await BybitService._get_redis()
            await redis_client.setex(cache_key, ttl, str(usdt_balance))
            logger.debug(f"Cached balance for user {user_id}: ${usdt_balance} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Failed to cache balance: {e}")
        
        return usdt_balance
    
    @staticmethod
    async def invalidate_balance_cache(user_id: uuid.UUID, testnet: bool = False) -> None:
        cache_key = f"bybit:balance:{user_id}:{'testnet' if testnet else 'mainnet'}"
        try:
            redis_client = await BybitService._get_redis()
            await redis_client.delete(cache_key)
            logger.debug(f"Invalidated balance cache for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
    
    @staticmethod
    async def validate_trading_capital(
        db: AsyncSession,
        user_id: uuid.UUID,
        allocation_percent: Decimal,
        min_capital_required: Decimal,
        testnet: bool = False
    ) -> Tuple[bool, Decimal, str]:
        try:
            usdt_balance = await BybitService.get_cached_usdt_balance(db, user_id, testnet)
            allocated_amount = (usdt_balance * allocation_percent) / Decimal('100')
            
            if allocated_amount < min_capital_required:
                reason = f"Allocated ${allocated_amount:.2f} is below trader's minimum ${min_capital_required:.2f}"
                logger.warning(f"User {user_id} failed capital check: {reason}")
                return False, allocated_amount, reason
                
            if allocated_amount < BYBIT_MIN_ORDER_SIZE:
                reason = f"Allocated ${allocated_amount:.2f} is below Bybit minimum order size ${BYBIT_MIN_ORDER_SIZE}"
                logger.warning(f"User {user_id} failed capital check: {reason}")
                return False, allocated_amount, reason
            
            logger.info(f"User {user_id} passed capital validation: ${allocated_amount:.2f} allocated")
            return True, allocated_amount, "Capital validation passed"
            
        except es.APIKeyNotFoundError:
            return False, Decimal('0'), "No valid Bybit API key connected"
        except es.APIKeyInvalidError:
            return False, Decimal('0'), "Bybit API key is invalid or expired"
        except es.ExchangeConnectionError as e:
            return False, Decimal('0'), f"Could not connect to Bybit: {str(e)}"
    
    @staticmethod
    def get_wallet_balance(api_key: str, api_secret: str, testnet: bool = False) -> Dict[str, Decimal]:
        return BybitService._sync_get_wallet_balance(api_key, api_secret, testnet)
    
    @staticmethod
    def get_usdt_balance(api_key: str, api_secret: str, testnet: bool = False) -> Decimal:
        balances = BybitService._sync_get_wallet_balance(api_key, api_secret, testnet)
        return balances.get('USDT', Decimal('0'))
    
    @staticmethod
    async def get_user_usdt_balance(
        db: AsyncSession, 
        user_id: uuid.UUID,
        testnet: bool = False
    ) -> Decimal:
        return await BybitService.get_cached_usdt_balance(db, user_id, testnet)
    
    @staticmethod
    def verify_api_permissions(api_key: str, api_secret: str, testnet: bool = False) -> Dict[str, bool]:
        return BybitService._sync_verify_permissions(api_key, api_secret, testnet)
