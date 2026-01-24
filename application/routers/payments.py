from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.base import get_db
from application.models.account import User
from application.schemas.payment import TierPricingResponse, TierUpgradeResponse, PaymentVerifyResponse, BanksListResponse
from application.services.paystack_service import PaystackService
from application.utilities.oauth2 import get_current_user
from application.utilities.audit import setup_logger, log_user_action
from application.utilities import exceptions as es

logger = setup_logger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/pricing", response_model=TierPricingResponse)
async def get_tier_pricing(db: AsyncSession = Depends(get_db)):
    pricing = await PaystackService.get_tier_pricing(db)
    return TierPricingResponse(**pricing)


@router.post("/upgrade/{tier}", response_model=TierUpgradeResponse)
async def initiate_tier_upgrade(
    tier: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    
    if tier not in ["plus", "business"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tier must be 'plus' or 'business'"
        )

    if current_user.tier.value == tier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are already on the {tier} tier"
        )

    logger.info(f"[UPGRADE] User {current_user.id} initiating upgrade to {tier} | IP: {ip_address}")

    try:
        pricing = await PaystackService.get_tier_pricing(db)
        tier_pricing = pricing[tier]

        result = await PaystackService.initialize_tier_payment(
            db=db,
            user_id=current_user.id,
            email=current_user.email,
            tier=tier
        )

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action=f"TIER_UPGRADE_INITIATED_{tier.upper()}",
            resource_type="PAYMENT",
            resource_id=result["reference"],
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={
                "tier": tier,
                "amount_usd": tier_pricing["price_usd"],
                "amount_ngn": tier_pricing["price_ngn"],
                "exchange_rate": pricing["exchange_rate"]
            }
        )
        await db.commit()

        logger.info(f"[UPGRADE] Payment initialized | User: {current_user.id} | Ref: {result['reference']} | ₦{tier_pricing['price_ngn']:,.2f}")

        return TierUpgradeResponse(
            reference=result["reference"],
            authorization_url=result["authorization_url"],
            access_code=result.get("access_code"),
            amount_ngn=tier_pricing["price_ngn"],
            amount_usd=tier_pricing["price_usd"],
            exchange_rate=pricing["exchange_rate"]
        )

    except es.InvalidRequestError as e:
        logger.warning(f"[UPGRADE FAILED] User {current_user.id} | Error: {e.detail} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.ServiceUnavailableError as e:
        logger.error(f"[UPGRADE FAILED] Service unavailable | User: {current_user.id} | Error: {e.detail}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e.detail))


@router.get("/verify/{reference}", response_model=PaymentVerifyResponse)
async def verify_payment(
    reference: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[VERIFY] User {current_user.id} verifying payment | Ref: {reference} | IP: {ip_address}")
    
    try:
        result = await PaystackService.verify_transaction(reference)
        
        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="PAYMENT_VERIFIED",
            resource_type="PAYMENT",
            resource_id=reference,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "status": result.get("status"),
                "amount": result.get("amount", 0) / 100,
                "gateway_response": result.get("gateway_response")
            }
        )
        await db.commit()
        
        return PaymentVerifyResponse(
            status=result.get("status", "unknown"),
            amount=result.get("amount", 0) / 100,
            reference=reference,
            gateway_response=result.get("gateway_response")
        )
    except es.DepositError as e:
        logger.warning(f"[VERIFY FAILED] Ref: {reference} | Error: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))


@router.get("/banks", response_model=BanksListResponse)
async def get_banks():
    banks = await PaystackService.get_banks()
    return BanksListResponse(banks=banks)
