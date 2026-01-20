from datetime import date, datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from application.models.base import get_db, get_read_db
from application.models import account
from application.schemas import trader_profile as tp
from application.schemas import kyc as kyc_schema
from application.services.tf_service import TraderProfileService
from application.utilities import oauth2 as o2
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger, log_user_action

logger = setup_logger(__name__)

router = APIRouter(prefix="/traders", tags=["Trader Profiles"])


@router.post("/apply", response_model=tp.TraderProfileResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_become_trader(
    trader_data: tp.TraderProfileCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Trader application from user {current_user.id} from {ip_address}")

    try:
        trader_profile = await TraderProfileService.apply_to_become_trader(db, current_user.id, trader_data)

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="TRADER_APPLICATION_SUBMITTED",
            resource_type="TRADER_PROFILE",
            resource_id=str(trader_profile.id),
            trader_profile_id=str(trader_profile.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"alias": trader_profile.alias, "submitted_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()
        await db.refresh(trader_profile)

        logger.info(f"Trader profile created for user {current_user.id} with alias {trader_profile.alias} from {ip_address}")
        return trader_profile
    except es.TraderProfileCreationError as e:
        logger.warning(f"Trader application failed for user {current_user.id} from {ip_address}: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.UserNotFoundError:
        logger.error(f"User not found during trader application from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post("/kyc/submit", response_model=kyc_schema.KYCResponse, status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    first_name: str = Form(...),
    last_name: str = Form(...),
    country: str = Form(...),
    date_of_birth: Optional[date] = Form(None),
    past_trades: Optional[str] = Form(None),
    id_document: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"KYC submission from user {current_user.id} from {ip_address}")

    kyc_data = kyc_schema.KYCCreate(
        first_name=first_name,
        last_name=last_name,
        country=country,
        date_of_birth=date_of_birth,
        past_trades=past_trades
    )

    try:
        kyc_record = await TraderProfileService.submit_kyc(db, current_user.id, kyc_data, id_document)

        trader_profile_id = current_user.trader_profile.id if hasattr(current_user, 'trader_profile') and current_user.trader_profile else None

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="KYC_SUBMITTED",
            resource_type="KYC",
            resource_id=str(kyc_record.id),
            trader_profile_id=str(trader_profile_id) if trader_profile_id else None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "country": country,
                "document_uploaded": True,
                "submitted_at": datetime.now(timezone.utc).isoformat()
            }
        )
        await db.commit()

        logger.info(f"KYC submitted successfully for user {current_user.id} from {ip_address}")
        return kyc_record
    except es.KYCError as e:
        logger.warning(f"KYC submission failed for user {current_user.id} from {ip_address}: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.UserNotFoundError:
        logger.error(f"User not found during KYC submission from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except es.TraderProfileNotFoundError as e:
        logger.warning(f"No trader profile for KYC submission from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))


@router.get("/me", response_model=tp.TraderProfileResponse)
async def get_my_trader_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"Trader profile request from user {current_user.id} from {ip_address}")

    try:
        trader = await TraderProfileService.get_trader_by_user_id(db, current_user.id)
        if not trader:
            logger.info(f"No trader profile found for user {current_user.id} from {ip_address}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trader profile found")
        return trader
    except es.UserNotFoundError:
        logger.error(f"User not found during trader profile lookup from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/me/kyc", response_model=kyc_schema.KYCResponse)
async def get_my_kyc(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"KYC info request from user {current_user.id} from {ip_address}")

    if not current_user.kyc:
        logger.info(f"No KYC record found for user {current_user.id} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No KYC record found")
    return current_user.kyc


@router.get("/{trader_id}", response_model=tp.TraderProfileResponse)
async def get_trader_profile(
    trader_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"Trader profile request for {trader_id} from {ip_address}")

    try:
        trader = await TraderProfileService.get_trader_profile(db, trader_id)
        return trader
    except es.TraderProfileNotFoundError:
        logger.info(f"Trader profile not found: {trader_id} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")


@router.get("", response_model=List[tp.TraderProfileResponse])
async def list_active_traders(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    read_db: AsyncSession = Depends(get_read_db)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"Active traders list request from {ip_address}")

    traders = await TraderProfileService.list_active_traders(read_db, skip, limit)
    logger.info(f"Returned {len(traders)} active traders from {ip_address}")
    return traders


@router.put("/me", response_model=tp.TraderProfileResponse)
async def update_my_trader_profile(
    update_data: tp.TraderProfileUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Trader profile update from user {current_user.id} from {ip_address}")

    if not current_user.trader_profile:
        logger.warning(f"User {current_user.id} attempted to update non-existent trader profile from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trader profile found")

    try:
        trader = await TraderProfileService.update_trader_profile(
            db, current_user.trader_profile.id, current_user.id, update_data
        )

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="TRADER_PROFILE_UPDATED",
            resource_type="TRADER_PROFILE",
            resource_id=str(trader.id),
            trader_profile_id=str(trader.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            changes=update_data.model_dump(exclude_unset=True),
            extra_data={"updated_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()
        await db.refresh(trader)

        logger.info(f"Trader profile updated for user {current_user.id} from {ip_address}")
        return trader
    except es.TraderProfileNotFoundError:
        logger.error(f"Trader profile not found during update from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
    except es.TraderProfileError as e:
        logger.warning(f"Trader profile update failed for user {current_user.id} from {ip_address}: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_trader_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Trader profile deletion request from user {current_user.id} from {ip_address}")

    if not current_user.trader_profile:
        logger.warning(f"User {current_user.id} attempted to delete non-existent trader profile from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trader profile found")

    try:
        trader_id = current_user.trader_profile.id
        trader_alias = current_user.trader_profile.alias

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="TRADER_PROFILE_DELETED",
            resource_type="TRADER_PROFILE",
            resource_id=str(trader_id),
            trader_profile_id=str(trader_id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"alias": trader_alias, "deleted_at": datetime.now(timezone.utc).isoformat()}
        )

        await TraderProfileService.delete_trader_profile(db, trader_id, current_user.id)
        await db.commit()

        logger.info(f"Trader profile {trader_id} deleted for user {current_user.id} from {ip_address}")
        return None
    except es.TraderProfileNotFoundError:
        logger.error(f"Trader profile not found during deletion from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
    except es.TraderProfileError as e:
        logger.warning(f"Trader profile deletion failed for user {current_user.id} from {ip_address}: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))


@router.post("/me/deactivate", response_model=tp.TraderProfileResponse)
async def deactivate_my_trader_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Trader profile deactivation from user {current_user.id} from {ip_address}")

    if not current_user.trader_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trader profile found")

    try:
        trader = await TraderProfileService.deactivate_trader_profile(
            db, current_user.trader_profile.id, current_user.id
        )

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="TRADER_PROFILE_DEACTIVATED",
            resource_type="TRADER_PROFILE",
            resource_id=str(trader.id),
            trader_profile_id=str(trader.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"deactivated_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()
        await db.refresh(trader)

        logger.info(f"Trader profile deactivated for user {current_user.id} from {ip_address}")
        return trader
    except es.TraderProfileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")


@router.post("/me/reactivate", response_model=tp.TraderProfileResponse)
async def reactivate_my_trader_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Trader profile reactivation from user {current_user.id} from {ip_address}")

    if not current_user.trader_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trader profile found")

    try:
        trader = await TraderProfileService.reactivate_trader_profile(
            db, current_user.trader_profile.id, current_user.id
        )

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="TRADER_PROFILE_REACTIVATED",
            resource_type="TRADER_PROFILE",
            resource_id=str(trader.id),
            trader_profile_id=str(trader.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"reactivated_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()
        await db.refresh(trader)

        logger.info(f"Trader profile reactivated for user {current_user.id} from {ip_address}")
        return trader
    except es.TraderProfileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
    except es.TraderProfileError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))


@router.post("/{trader_id}/kyc/approve", response_model=tp.TraderProfileResponse)
async def approve_kyc(
    trader_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: account.User = Depends(o2.get_current_admin)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"KYC approval by admin {current_admin.id} for trader {trader_id} from {ip_address}")

    try:
        trader = await TraderProfileService.get_trader_profile(db, trader_id)

        approved_profile = await TraderProfileService.approve_kyc(db, trader.user_id)

        await log_user_action(
            db=db,
            user_id=current_admin.id,
            action="KYC_APPROVED",
            resource_type="KYC",
            resource_id=str(trader.user_id),
            trader_profile_id=str(trader_id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "approved_by": str(current_admin.id),
                "approved_at": datetime.now(timezone.utc).isoformat()
            }
        )
        await db.commit()
        await db.refresh(approved_profile)

        logger.info(f"KYC approved for trader {trader_id} by admin {current_admin.id} from {ip_address}")
        return approved_profile
    except es.TraderProfileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
    except es.KYCNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC record not found")


@router.post("/{trader_id}/kyc/reject", response_model=kyc_schema.KYCResponse)
async def reject_kyc(
    trader_id: uuid.UUID,
    rejection_data: kyc_schema.KYCRejection,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: account.User = Depends(o2.get_current_admin)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"KYC rejection by admin {current_admin.id} for trader {trader_id} from {ip_address}")

    try:
        trader = await TraderProfileService.get_trader_profile(db, trader_id)

        rejected_kyc = await TraderProfileService.reject_kyc(db, trader.user_id, rejection_data.reason)

        await log_user_action(
            db=db,
            user_id=current_admin.id,
            action="KYC_REJECTED",
            resource_type="KYC",
            resource_id=str(trader.user_id),
            trader_profile_id=str(trader_id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "rejected_by": str(current_admin.id),
                "reason": rejection_data.reason,
                "rejected_at": datetime.now(timezone.utc).isoformat()
            }
        )
        await db.commit()
        await db.refresh(rejected_kyc)

        logger.info(f"KYC rejected for trader {trader_id} by admin {current_admin.id} from {ip_address}")
        return rejected_kyc
    except es.TraderProfileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
    except es.KYCNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC record not found")


@router.post("/{trader_id}/graduate", response_model=tp.TraderProfileResponse)
async def graduate_trader(
    trader_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: account.User = Depends(o2.get_current_admin)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Trader graduation by admin {current_admin.id} for trader {trader_id} from {ip_address}")

    try:
        graduated_trader = await TraderProfileService.graduate_trader(db, trader_id)

        await log_user_action(
            db=db,
            user_id=current_admin.id,
            action="TRADER_GRADUATED",
            resource_type="TRADER_PROFILE",
            resource_id=str(trader_id),
            trader_profile_id=str(trader_id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "graduated_by": str(current_admin.id),
                "graduated_at": datetime.now(timezone.utc).isoformat(),
                "win_rate": graduated_trader.win_rate,
                "trades_count": graduated_trader.probation_trades_count
            }
        )
        await db.commit()
        await db.refresh(graduated_trader)

        logger.info(f"Trader {trader_id} graduated by admin {current_admin.id} from {ip_address}")
        return graduated_trader
    except es.TraderProfileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
    except es.TraderProfileError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))


@router.post("/{trader_id}/suspend", response_model=tp.TraderProfileResponse)
async def suspend_trader(
    trader_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: account.User = Depends(o2.get_current_admin)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Trader suspension by admin {current_admin.id} for trader {trader_id} from {ip_address}")

    try:
        suspended_trader = await TraderProfileService.suspend_trader_profile(db, trader_id)

        await log_user_action(
            db=db,
            user_id=current_admin.id,
            action="TRADER_SUSPENDED",
            resource_type="TRADER_PROFILE",
            resource_id=str(trader_id),
            trader_profile_id=str(trader_id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "suspended_by": str(current_admin.id),
                "suspended_at": datetime.now(timezone.utc).isoformat()
            }
        )
        await db.commit()
        await db.refresh(suspended_trader)

        logger.info(f"Trader {trader_id} suspended by admin {current_admin.id} from {ip_address}")
        return suspended_trader
    except es.TraderProfileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trader profile not found")
