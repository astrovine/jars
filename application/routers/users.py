from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from application.models.base import get_db, get_read_db
from application.models import account
from application.schemas import account as account_schema
from application.schemas import audit_logs as audit_schema
from application.services.account_service import AccountService
from application.services.registration_service import RegistrationService
from application.services.ledger_service import LedgerService
from application.utilities import oauth2 as o2
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger, log_user_action

logger = setup_logger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=account_schema.UserResponse)
async def get_current_user_info(
    request: Request,
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} requesting basic profile from {ip_address}")
    return current_user


@router.get("/me/full", response_model=account_schema.UserFullResponse)
async def get_current_user_full_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[USER] Full profile requested | User: {current_user.id} ({current_user.email}) | IP: {ip_address}")

    try:
        user = await AccountService.get_full_user_info(db, current_user.id)
        if user is None:
            logger.error(f"[USER ERROR] User {current_user.id} not found in database | IP: {ip_address}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        wallet_info = await LedgerService.get_wallet_info(db, current_user.id)

        has_kyc = user.kyc is not None
        has_trader_profile = user.trader_profile is not None
        wallet_balance = wallet_info.get("balance") if wallet_info else None
        wallet_currency = wallet_info.get("currency") if wallet_info else None
        wallet_active = wallet_info.get("is_active") if wallet_info else None

        logger.info(
            f"[USER] Full profile returned | User: {current_user.id} | "
            f"Balance: {wallet_currency} {wallet_balance} | KYC: {has_kyc} | Trader: {has_trader_profile} | IP: {ip_address}"
        )

        return account_schema.UserFullResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            status=user.status,
            country=user.country,
            is_active=user.is_active,
            is_2fa_enabled=user.is_2fa_enabled,
            tier=user.tier,
            created_at=user.created_at,
            updated_at=user.updated_at,
            kyc=user.kyc,
            trader_profile=user.trader_profile,
            wallet_balance=wallet_balance,
            wallet_currency=wallet_currency,
            wallet_active=wallet_active
        )
    except es.DatabaseError as e:
        logger.error(f"[USER ERROR] Database error for user {current_user.id} | Error: {e.detail} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e.detail))


@router.get("/me/refresh", status_code=status.HTTP_200_OK)
async def refresh_user_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[USER] Data refresh requested | User: {current_user.id} ({current_user.email}) | IP: {ip_address}")

    try:
        user = await AccountService.get_full_user_info(db, current_user.id)

        if user is None:
            logger.error(f"[USER ERROR] User {current_user.id} not found during refresh | IP: {ip_address}")
            raise es.UserNotFoundError("User not found")

        wallet_info = await LedgerService.get_wallet_info(db, current_user.id)

        has_kyc = user.kyc is not None
        has_trader_profile = user.trader_profile is not None

        user_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "country": user.country,
            "status": user.status,
            "is_active": user.is_active,
            "is_2fa_enabled": user.is_2fa_enabled,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "has_kyc": has_kyc,
            "has_trader_profile": has_trader_profile,
            "kyc": user.kyc,
            "trader_profile": user.trader_profile,
            "wallet_balance": str(wallet_info.get("balance")) if wallet_info else None,
            "wallet_currency": wallet_info.get("currency") if wallet_info else None,
            "wallet_active": wallet_info.get("is_active") if wallet_info else None
        }

        logger.info(
            f"[USER] Data refreshed | User: {current_user.id} | "
            f"Balance: {wallet_info.get('currency') if wallet_info else 'N/A'} {wallet_info.get('balance') if wallet_info else 0} | "
            f"KYC: {has_kyc} | Trader: {has_trader_profile} | IP: {ip_address}"
        )
        return user_data
    except es.UserNotFoundError as e:
        logger.error(f"[USER ERROR] User not found during refresh | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"[USER ERROR] Unexpected error refreshing user {current_user.id} | Error: {e} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to refresh user data")


@router.put("/me", response_model=account_schema.UserResponse)
async def update_current_user(
    update_data: account_schema.UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} updating profile from {ip_address}")

    try:
        updated_user = await AccountService.update_user_account(db, update_data, current_user.id)

        trader_profile_id = current_user.trader_profile.id if hasattr(current_user, 'trader_profile') and current_user.trader_profile else None

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="PROFILE_UPDATED",
            resource_type="USER",
            resource_id=str(current_user.id),
            trader_profile_id=trader_profile_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            changes=update_data.model_dump(exclude_unset=True),
            extra_data={"updated_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()
        await db.refresh(updated_user)

        logger.info(f"User {current_user.id} profile updated successfully from {ip_address}")
        return updated_user
    except es.UserNotFoundError:
        logger.error(f"User {current_user.id} not found during update from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except es.UserUpdateError as e:
        logger.error(f"Update failed for user {current_user.id} from {ip_address}: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error updating user {current_user.id} from {ip_address}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile")


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: account_schema.PasswordChange,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Password change request for user {current_user.id} from {ip_address}")

    try:
        await AccountService.change_user_password(
            db,
            current_user.id,
            password_data.old_password,
            password_data.new_password,
            password_data.confirm_password
        )

        trader_profile_id = current_user.trader_profile.id if hasattr(current_user, 'trader_profile') and current_user.trader_profile else None

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="PASSWORD_CHANGED",
            resource_type="USER",
            resource_id=str(current_user.id),
            trader_profile_id=trader_profile_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"changed_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()

        logger.info(f"Password changed successfully for user {current_user.id} from {ip_address}")
        return {"message": "Password changed successfully"}
    except es.InvalidCredentialsError:
        logger.warning(f"Invalid old password provided for user {current_user.id} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")
    except es.PasswordMismatchError:
        logger.warning(f"New password mismatch for user {current_user.id} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New passwords do not match")
    except es.DatabaseError as e:
        await db.rollback()
        logger.error(f"Database error changing password for user {current_user.id} from {ip_address}: {e.detail}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e.detail))
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error changing password for user {current_user.id} from {ip_address}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not change password")


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.email}) requesting account deletion from {ip_address}")

    try:
        trader_profile_id = current_user.trader_profile.id if hasattr(current_user, 'trader_profile') and current_user.trader_profile else None
        user_email = current_user.email
        user_id = current_user.id

        await log_user_action(
            db=db,
            user_id=user_id,
            action="ACCOUNT_DELETED",
            resource_type="USER",
            resource_id=str(user_id),
            trader_profile_id=trader_profile_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"email": user_email, "deleted_at": datetime.now(timezone.utc).isoformat()}
        )

        await AccountService.delete_user_account(db, user_id)
        await db.commit()

        logger.info(f"User {user_id} ({user_email}) account deleted successfully from {ip_address}")
        return None
    except es.UserNotFoundError as e:
        await db.rollback()
        logger.error(f"User not found during deletion from {ip_address}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error deleting user {current_user.id} from {ip_address}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete account")


@router.get("/me/activity", response_model=List[audit_schema.AuditLogResponse])
async def get_user_activity_logs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    read_db: AsyncSession = Depends(get_read_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User activity request for user {current_user.id} from {ip_address}")

    try:
        logs = await AccountService.get_activity_logs(read_db, current_user)

        if not logs:
            logger.info(f"No activity logs found for user {current_user.id} from {ip_address}")
            return []

        trader_profile_id = current_user.trader_profile.id if hasattr(current_user, 'trader_profile') and current_user.trader_profile else None

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="ACTIVITY_LOGS_VIEWED",
            resource_type="USER",
            resource_id=str(current_user.id),
            trader_profile_id=trader_profile_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"viewed_at": datetime.now(timezone.utc).isoformat(), "log_count": len(logs)}
        )
        await db.commit()

        logger.info(f"Returned {len(logs)} activity logs for user {current_user.id} from {ip_address}")
        return logs
    except es.DatabaseError as e:
        logger.error(f"Database error getting activity logs for user {current_user.id} from {ip_address}: {e.detail}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e.detail))
    except Exception as e:
        logger.error(f"Unexpected error getting activity logs for user {current_user.id} from {ip_address}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve activity logs")


@router.post("/me/upgrade/plus", response_model=account_schema.UserResponse)
async def upgrade_to_plus(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[TIER UPGRADE] Plus upgrade request | User: {current_user.id} | IP: {ip_address}")

    try:
        user = await RegistrationService.upgrade_to_plus(db, current_user.id)
        
        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="TIER_UPGRADED",
            resource_type="USER",
            resource_id=str(current_user.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"new_tier": "plus", "upgraded_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()
        await db.refresh(user)

        logger.info(f"[TIER UPGRADE SUCCESS] User {current_user.id} upgraded to Plus | IP: {ip_address}")
        return user

    except es.InvalidRequestError as e:
        logger.warning(f"[TIER UPGRADE BLOCKED] {e.detail} | User: {current_user.id} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    except es.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        await db.rollback()
        logger.error(f"[TIER UPGRADE FAILED] User {current_user.id} | Error: {e} | IP: {ip_address}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upgrade tier")


@router.post("/me/upgrade/business", response_model=account_schema.UserResponse)
async def upgrade_to_business(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[TIER UPGRADE] Business upgrade request | User: {current_user.id} | IP: {ip_address}")

    try:
        user = await RegistrationService.upgrade_to_business(db, current_user.id)
        
        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="TIER_UPGRADED",
            resource_type="USER",
            resource_id=str(current_user.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"new_tier": "business", "upgraded_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()
        await db.refresh(user)

        logger.info(f"[TIER UPGRADE SUCCESS] User {current_user.id} upgraded to Business | IP: {ip_address}")
        return user

    except es.InvalidRequestError as e:
        logger.warning(f"[TIER UPGRADE BLOCKED] {e.detail} | User: {current_user.id} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    except es.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        await db.rollback()
        logger.error(f"[TIER UPGRADE FAILED] User {current_user.id} | Error: {e} | IP: {ip_address}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upgrade tier")


@router.post("/me/downgrade/free", response_model=account_schema.UserResponse)
async def downgrade_to_free(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[TIER DOWNGRADE] Free downgrade request | User: {current_user.id} | IP: {ip_address}")

    try:
        user = await RegistrationService.downgrade_to_free(db, current_user.id)
        
        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="TIER_DOWNGRADED",
            resource_type="USER",
            resource_id=str(current_user.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"new_tier": "free", "downgraded_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()
        await db.refresh(user)

        logger.info(f"[TIER DOWNGRADE SUCCESS] User {current_user.id} downgraded to Free | IP: {ip_address}")
        return user

    except es.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        await db.rollback()
        logger.error(f"[TIER DOWNGRADE FAILED] User {current_user.id} | Error: {e} | IP: {ip_address}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to downgrade tier")


@router.post("/me/ensure-demo-wallet", status_code=status.HTTP_200_OK)
async def ensure_demo_wallet(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[DEMO WALLET] Ensure demo wallet request | User: {current_user.id} | IP: {ip_address}")

    try:
        wallet = await RegistrationService.ensure_demo_wallet(db, current_user.id)
        await db.commit()

        logger.info(f"[DEMO WALLET] Demo wallet ensured for user {current_user.id} | Wallet: {wallet.id} | IP: {ip_address}")
        return {
            "message": "Demo wallet ready",
            "wallet_id": str(wallet.id),
            "balance": str(wallet.balance),
            "currency": wallet.currency
        }

    except es.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except es.SystemAccountNotFoundError as e:
        logger.error(f"[DEMO WALLET FAILED] System account missing | User: {current_user.id} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="System configuration error")
    except Exception as e:
        await db.rollback()
        logger.error(f"[DEMO WALLET FAILED] User {current_user.id} | Error: {e} | IP: {ip_address}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to ensure demo wallet")
