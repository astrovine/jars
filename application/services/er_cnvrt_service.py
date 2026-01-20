from decimal import Decimal
from typing import Tuple

import httpx
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.ledger import ExchangeRate
from application.utilities.config import settings
from application.utilities.audit import setup_logger

logger = setup_logger(__name__)
API_KEY = settings.OPEN_EXCHANGE_RATES_API_KEY


class ExchangeRateConverter:
    @staticmethod
    async def get_current_rate(db: AsyncSession) -> Decimal:
        result = await db.execute(
            select(ExchangeRate)
            .order_by(desc(ExchangeRate.created_at))
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        
        if latest:
            logger.debug(f"[RATE] Using DB rate: {latest.rate} from {latest.created_at}")
            return Decimal(str(latest.rate))
        
        logger.warning("[RATE] No rate in DB, using fallback")
        return Decimal(str(settings.FALLBACK_EXCHANGE_RATE))

    @staticmethod
    async def convert_usd_to_ngn(db: AsyncSession, amount_usd: Decimal) -> Tuple[Decimal, Decimal]:
        rate = await ExchangeRateConverter.get_current_rate(db)
        amount_ngn = amount_usd * rate
        logger.info(f"[CONVERT] ${amount_usd} → ₦{amount_ngn:.2f} @ rate {rate}")
        return (amount_ngn, rate)

    @staticmethod
    async def fetch_rate_from_api(base: str = "USD", quote: str = "NGN") -> Decimal:
        url = "https://openexchangerates.org/api/latest.json"
        params = {
            "app_id": API_KEY,
            "symbols": f"{base},{quote}"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                rates = response.json().get("rates", {})
                
                usd_to_base = rates.get(base, 1.0)
                usd_to_quote = rates.get(quote, 0.0)

                if not usd_to_quote:
                    logger.error(f"[RATE API] Missing rate for {quote}")
                    return Decimal("0")

                cross_rate = usd_to_quote / usd_to_base
                rate_with_spread = Decimal(str(cross_rate)) * Decimal("1.03")
                
                logger.info(f"[RATE API] Fetched {base}/{quote}: {cross_rate:.4f} (with spread: {rate_with_spread:.4f})")
                return rate_with_spread
                
            except httpx.HTTPStatusError as e:
                logger.error(f"[RATE API ERROR] HTTP {e.response.status_code}: {e.response.text}")
                return Decimal("0")
            except httpx.RequestError as e:
                logger.error(f"[RATE API ERROR] Request failed: {e}")
                return Decimal("0")
