import uuid
import httpx
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.ledger_service import LedgerService
from application.services.er_cnvrt_service import ExchangeRateConverter
from application.utilities.config import settings
from application.utilities.audit import setup_logger
from application.utilities import exceptions as es

logger = setup_logger(__name__)

PAYSTACK_BASE_URL = "https://api.paystack.co"


class PaystackService:

    @staticmethod
    def _get_headers():
        return {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

    @staticmethod
    async def initialize_transaction(
        db: AsyncSession,
        user_id: uuid.UUID,
        email: str,
        amount_naira: Decimal,
        callback_url: Optional[str] = None,
        description: Optional[str] = None
    ) -> dict:
        amount_kobo = int(amount_naira * 100)
        logger.info(f"[PAYSTACK] Initializing transaction for user {user_id} | Amount: ₦{amount_naira:,.2f} ({amount_kobo} kobo)")

        if amount_kobo < 10000:
            logger.warning(f"[PAYSTACK] Deposit rejected - amount ₦{amount_naira:,.2f} below minimum ₦100 | User: {user_id}")
            raise es.InvalidAmountError("Minimum deposit is ₦100")

        reference = f"dep_{user_id.hex[:8]}_{uuid.uuid4().hex[:12]}"
        logger.info(f"[PAYSTACK] Generated reference: {reference} for user {user_id}")

        await LedgerService.create_pending_deposit(
            db,
            user_id,
            amount_kobo,
            reference,
            description or f"Deposit of ₦{amount_naira}"
        )

        payload = {
            "email": email,
            "amount": amount_kobo,
            "reference": reference,
            "callback_url": callback_url or f"{settings.FRONTEND_URL}/wallet/deposit/callback"
        }

        try:
            logger.info(f"[PAYSTACK API] Calling Paystack to initialize payment | Ref: {reference}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{PAYSTACK_BASE_URL}/transaction/initialize",
                    json=payload,
                    headers=PaystackService._get_headers(),
                    timeout=30.0
                )

            response_data = response.json()

            if not response_data.get("status"):
                message = response_data.get("message", "Unknown error")
                logger.error(f"[PAYSTACK ERROR] Initialization failed | Ref: {reference} | Error: {message}")
                raise es.DepositError(message)

            data = response_data.get("data", {})
            await db.commit()

            logger.info(
                f"[PAYSTACK SUCCESS] Transaction initialized | Ref: {reference} | "
                f"User: {user_id} | Amount: ₦{amount_naira:,.2f}"
            )

            return {
                "reference": reference,
                "authorization_url": data.get("authorization_url"),
                "access_code": data.get("access_code")
            }

        except httpx.RequestError as e:
            await db.rollback()
            logger.error(f"[PAYSTACK NETWORK ERROR] Failed to reach Paystack API | Ref: {reference} | Error: {e}")
            raise es.ServiceUnavailableError("Payment service")

    @staticmethod
    async def initialize_tier_payment(
        db: AsyncSession,
        user_id: uuid.UUID,
        email: str,
        tier: str,
        callback_url: Optional[str] = None
    ) -> dict:
        if tier == "plus":
            price_usd = Decimal(str(settings.PLUS_TIER_PRICE_USD))
        elif tier == "business":
            price_usd = Decimal(str(settings.BUSINESS_TIER_PRICE_USD))
        else:
            raise es.InvalidRequestError(f"Unknown tier: {tier}")

        amount_ngn, rate = await ExchangeRateConverter.convert_usd_to_ngn(db, price_usd)
        amount_kobo = int(amount_ngn * 100)

        reference = f"tier_{tier}_{user_id.hex[:8]}_{uuid.uuid4().hex[:8]}"

        logger.info(
            f"[TIER PAYMENT] {tier.upper()} tier | User: {user_id} | "
            f"${price_usd} → ₦{amount_ngn:,.2f} @ rate {rate} | Ref: {reference}"
        )

        await LedgerService.create_pending_deposit(
            db,
            user_id,
            amount_kobo,
            reference,
            f"{tier.capitalize()} Tier Upgrade - ${price_usd}"
        )

        payload = {
            "email": email,
            "amount": amount_kobo,
            "reference": reference,
            "callback_url": callback_url or f"{settings.FRONTEND_URL}/upgrade/{tier}/callback",
            "metadata": {
                "payment_type": "tier_upgrade",
                "tier": tier,
                "user_id": str(user_id),
                "price_usd": str(price_usd),
                "exchange_rate": str(rate)
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{PAYSTACK_BASE_URL}/transaction/initialize",
                    json=payload,
                    headers=PaystackService._get_headers(),
                    timeout=30.0
                )

            response_data = response.json()

            if not response_data.get("status"):
                message = response_data.get("message", "Unknown error")
                logger.error(f"[TIER PAYMENT ERROR] Init failed | Ref: {reference} | Error: {message}")
                raise es.DepositError(message)

            data = response_data.get("data", {})
            await db.commit()

            logger.info(f"[TIER PAYMENT SUCCESS] Initialized | Ref: {reference} | User: {user_id}")

            return {
                "reference": reference,
                "authorization_url": data.get("authorization_url"),
                "access_code": data.get("access_code")
            }

        except httpx.RequestError as e:
            await db.rollback()
            logger.error(f"[TIER PAYMENT ERROR] Network failure | Ref: {reference} | Error: {e}")
            raise es.ServiceUnavailableError("Payment service")

    @staticmethod
    async def get_tier_pricing(db: AsyncSession) -> dict:
        rate = await ExchangeRateConverter.get_current_rate(db)
        
        plus_usd = Decimal(str(settings.PLUS_TIER_PRICE_USD))
        business_usd = Decimal(str(settings.BUSINESS_TIER_PRICE_USD))

        return {
            "exchange_rate": float(rate),
            "plus": {
                "price_usd": float(plus_usd),
                "price_ngn": float(plus_usd * rate)
            },
            "business": {
                "price_usd": float(business_usd),
                "price_ngn": float(business_usd * rate)
            }
        }

    @staticmethod
    async def verify_transaction(reference: str) -> dict:
        logger.info(f"[PAYSTACK] Verifying transaction | Ref: {reference}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                    headers=PaystackService._get_headers(),
                    timeout=30.0
                )

            response_data = response.json()

            if not response_data.get("status"):
                message = response_data.get("message", "Unknown error")
                logger.error(f"[PAYSTACK VERIFY FAILED] Ref: {reference} | Error: {message}")
                raise es.DepositError(message)

            data = response_data.get("data", {})
            status = data.get("status", "unknown")
            amount = data.get("amount", 0) / 100

            logger.info(
                f"[PAYSTACK VERIFY] Ref: {reference} | Status: {status} | "
                f"Amount: ₦{amount:,.2f} | Gateway: {data.get('gateway_response', 'N/A')}"
            )

            return data

        except httpx.RequestError as e:
            logger.error(f"[PAYSTACK NETWORK ERROR] Verification failed | Ref: {reference} | Error: {e}")
            raise es.ServiceUnavailableError("Payment service")

    @staticmethod
    async def get_banks() -> list:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{PAYSTACK_BASE_URL}/bank",
                    headers=PaystackService._get_headers(),
                    params={"country": "nigeria"},
                    timeout=30.0
                )

            response_data = response.json()

            if not response_data.get("status"):
                logger.warning("[PAYSTACK] Failed to fetch banks list")
                return []

            banks = response_data.get("data", [])
            logger.info(f"[PAYSTACK] Retrieved {len(banks)} Nigerian banks")
            return banks

        except httpx.RequestError as e:
            logger.error(f"[PAYSTACK NETWORK ERROR] Failed to fetch banks | Error: {e}")
            return []
