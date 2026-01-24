from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.base import get_db
from application.models import account
from application.schemas import ledger as l
from application.services.admin_service import AdminService
from application.utilities import oauth2 as o2
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger, log_user_action

logger = setup_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.post("/accounts/system", response_model=l.NewAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_system_account(
    account_data: l.CreatNewAccount,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: account.User = Depends(o2.get_current_admin)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[ADMIN] System account creation | Admin: {current_admin.id} | Type: {account_data.type} | IP: {ip_address}")

    try:
        new_account = await AdminService.create_new_systems_account(db, account_data, current_admin.id)

        await log_user_action(
            db=db,
            user_id=current_admin.id,
            action="SYSTEM_ACCOUNT_CREATED",
            resource_type="ACCOUNT",
            resource_id=str(new_account.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "account_type": account_data.type,
                "currency": account_data.currency,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        await db.commit()

        logger.info(f"[ADMIN] System account created | ID: {new_account.id} | Type: {account_data.type} | Admin: {current_admin.id}")
        return new_account

    except es.InvalidRequestError as e:
        logger.warning(f"[ADMIN] Invalid request | Admin: {current_admin.id} | Error: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.AccountAlreadyExistsError as e:
        logger.warning(f"[ADMIN] Duplicate account | Admin: {current_admin.id} | Type: {account_data.type}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.detail))
