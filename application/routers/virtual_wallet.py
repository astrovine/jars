from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.base import get_db
from application.models import account
from application.schemas.virtual_wallet import VirtualWalletStatusResponse, VirtualBalanceResetResponse
from application.services.ledger_service import LedgerService
from application.utilities import oauth2 as o2
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger, log_user_action

logger = setup_logger(__name__)

router = APIRouter(prefix="/wallet/virtual", tags=["Virtual Wallet"])


@router.get("/status", response_model=VirtualWalletStatusResponse)
async def get_virtual_wallet_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"[VIRTUAL WALLET] Status check for user {current_user.id} | IP: {ip_address}")

    eligibility = await LedgerService.check_reset_eligibility(db, current_user.id)
    
    return VirtualWalletStatusResponse(
        current_balance=eligibility["current_balance"],
        is_blown=eligibility["is_blown"],
        free_reset_available=eligibility["free_reset_available"],
        free_reset_date=eligibility["free_reset_date"],
        days_since_last_reset=eligibility["days_since_last_reset"],
        paid_reset_cost_usd=eligibility["paid_reset_cost_usd"]
    )


@router.post("/reset/free", response_model=VirtualBalanceResetResponse)
async def request_free_reset(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[VIRTUAL RESET] Free reset request from user {current_user.id} | IP: {ip_address}")

    try:
        transaction = await LedgerService.reset_virtual_balance(
            db, current_user.id, is_paid=False
        )
        
        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="VIRTUAL_BALANCE_RESET_FREE",
            resource_type="VIRTUAL_WALLET",
            resource_id=str(current_user.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"reset_amount": str(transaction.amount)}
        )
        await db.commit()
        
        logger.info(f"[VIRTUAL RESET] Free reset completed for user {current_user.id}")
        return VirtualBalanceResetResponse(
            message="Virtual balance reset successfully",
            new_balance=Decimal("10000"),
            reset_type="free",
            transaction_reference=transaction.reference_id
        )
        
    except es.InvalidRequestError as e:
        logger.warning(f"[VIRTUAL RESET] Free reset denied for user {current_user.id}: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    except es.AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))


@router.post("/reset/paid", response_model=VirtualBalanceResetResponse)
async def request_paid_reset(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[VIRTUAL RESET] Paid reset request from user {current_user.id} | IP: {ip_address}")

    try:
        transaction = await LedgerService.reset_virtual_balance(
            db, current_user.id, is_paid=True
        )
        
        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="VIRTUAL_BALANCE_RESET_PAID",
            resource_type="VIRTUAL_WALLET",
            resource_id=str(current_user.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "reset_amount": str(transaction.amount),
                "payment_amount_usd": "5.00"
            }
        )
        await db.commit()
        
        logger.info(f"[VIRTUAL RESET] Paid reset completed for user {current_user.id}")
        return VirtualBalanceResetResponse(
            message="Virtual balance reset successfully (Paid)",
            new_balance=Decimal("10000"),
            reset_type="paid",
            transaction_reference=transaction.reference_id
        )
        
    except es.AccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
