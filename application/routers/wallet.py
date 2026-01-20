from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.base import get_db, get_read_db
from application.models import account
from application.schemas import ledger as ledger_schema
from application.services.ledger_service import LedgerService
from application.services.paystack_service import PaystackService
from application.utilities import oauth2 as o2
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger, log_user_action

logger = setup_logger(__name__)

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/balance", response_model=ledger_schema.WalletInfo)
async def get_wallet_balance(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"[WALLET] Balance request | User: {current_user.id} | IP: {ip_address}")

    wallet_info = await LedgerService.get_wallet_info(db, current_user.id)

    if not wallet_info:
        logger.warning(f"[WALLET] No wallet found | User: {current_user.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    logger.info(f"[WALLET] Balance returned | User: {current_user.id} | Balance: {wallet_info['currency']} {wallet_info['balance']}")
    return wallet_info


@router.get("/summary", response_model=ledger_schema.WalletSummary)
async def get_wallet_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"[WALLET] Summary request | User: {current_user.id} | IP: {ip_address}")

    summary = await LedgerService.get_wallet_summary(db, current_user.id)

    logger.info(f"[WALLET] Summary returned | User: {current_user.id} | Balance: {summary['currency']} {summary['balance']}")
    return summary


@router.post("/deposit/initialize", response_model=ledger_schema.DepositInitResponse)
async def initialize_deposit(
    deposit_data: ledger_schema.DepositRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[DEPOSIT] Init request | User: {current_user.id} | Amount: ₦{deposit_data.amount:,.2f} | IP: {ip_address}")

    try:
        result = await PaystackService.initialize_transaction(
            db,
            current_user.id,
            current_user.email,
            deposit_data.amount,
            deposit_data.callback_url
        )

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="DEPOSIT_INITIATED",
            resource_type="TRANSACTION",
            resource_id=result["reference"],
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "amount": str(deposit_data.amount),
                "currency": "NGN",
                "initiated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        await db.commit()

        logger.info(f"[DEPOSIT] Initialized | Ref: {result['reference']} | User: {current_user.id} | Amount: ₦{deposit_data.amount:,.2f}")
        return result

    except es.InvalidAmountError as e:
        logger.warning(f"[DEPOSIT] Invalid amount | User: {current_user.id} | Amount: {deposit_data.amount}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.DepositError as e:
        logger.error(f"[DEPOSIT] Failed | User: {current_user.id} | Error: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.ServiceUnavailableError as e:
        logger.error(f"[DEPOSIT] Service unavailable | User: {current_user.id}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e.detail))


@router.get("/deposit/verify/{reference}")
async def verify_deposit(
    reference: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[DEPOSIT] Verify request | Ref: {reference} | User: {current_user.id} | IP: {ip_address}")

    try:
        paystack_data = await PaystackService.verify_transaction(reference)

        if paystack_data.get("status") == "success":
            transaction, amount = await LedgerService.process_successful_deposit(
                db,
                reference,
                paystack_data.get("id", "")
            )

            await log_user_action(
                db=db,
                user_id=current_user.id,
                action="DEPOSIT_VERIFIED",
                resource_type="TRANSACTION",
                resource_id=reference,
                ip_address=ip_address,
                user_agent=request.headers.get("user-agent"),
                extra_data={
                    "amount": str(amount),
                    "paystack_status": "success",
                    "verified_at": datetime.now(timezone.utc).isoformat()
                }
            )
            await db.commit()

            logger.info(f"[DEPOSIT] Verified and credited | Ref: {reference} | User: {current_user.id} | Amount: ₦{amount:,.2f}")
            return {
                "status": "success",
                "message": "Deposit verified and credited",
                "amount": str(amount),
                "reference": reference
            }
        else:
            await LedgerService.process_failed_deposit(
                db,
                reference,
                paystack_data.get("gateway_response", "Unknown failure")
            )
            await db.commit()

            logger.warning(f"[DEPOSIT] Failed verification | Ref: {reference} | Status: {paystack_data.get('status')}")
            return {
                "status": "failed",
                "message": paystack_data.get("gateway_response", "Payment not successful"),
                "reference": reference
            }

    except es.TransactionNotFoundError:
        logger.error(f"[DEPOSIT] Transaction not found | Ref: {reference}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    except es.DepositError as e:
        logger.error(f"[DEPOSIT] Verification error | Ref: {reference} | Error: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.ServiceUnavailableError:
        logger.error(f"[DEPOSIT] Service unavailable during verification | Ref: {reference}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Payment service unavailable")


@router.get("/transactions", response_model=ledger_schema.TransactionHistoryResponse)
async def get_transaction_history(
    request: Request,
    read_db: AsyncSession = Depends(get_read_db),
    current_user: account.User = Depends(o2.get_current_user),
    limit: int = 50,
    offset: int = 0
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"[WALLET] Transaction history | User: {current_user.id} | Limit: {limit} | Offset: {offset}")

    entries, total = await LedgerService.get_transaction_history(read_db, current_user.id, limit, offset)

    logger.info(f"[WALLET] Returned {len(entries)} of {total} transactions | User: {current_user.id}")
    return {
        "entries": entries,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/banks")
async def get_banks(request: Request):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"[WALLET] Banks list request | IP: {ip_address}")

    banks = await PaystackService.get_banks()
    return {"banks": banks}
