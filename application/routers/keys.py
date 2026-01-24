from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from application.models.base import get_db
from application.models import account
from application.schemas import keys as K
from application.services.ek_service import ExchangeKeysService
from application.utilities import oauth2 as o2
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger, log_user_action

logger = setup_logger(__name__)

router = APIRouter(prefix="/keys", tags=["Exchange Keys"])


@router.post("", response_model=K.ExchangeKeyResponse, status_code=status.HTTP_201_CREATED)
async def add_exchange_key(
    key_data: K.ExchangeKeyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[KEY] Add request | User: {current_user.id} | Exchange: {key_data.exchange_name} | IP: {ip_address}")

    try:
        new_key = await ExchangeKeysService.create_exchange_key(db, key_data, current_user.id)

        trader_profile_id = current_user.trader_profile.id if hasattr(current_user, 'trader_profile') and current_user.trader_profile else None

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="EXCHANGE_KEY_ADDED",
            resource_type="EXCHANGE_KEY",
            resource_id=str(new_key.id),
            trader_profile_id=str(trader_profile_id) if trader_profile_id else None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={
                "exchange": key_data.exchange_name,
                "label": key_data.label,
                "added_at": datetime.now(timezone.utc).isoformat()
            }
        )
        await db.commit()
        await db.refresh(new_key)

        logger.info(f"[KEY] Added successfully | ID: {new_key.id} | User: {current_user.id} | Exchange: {key_data.exchange_name}")
        return new_key

    except es.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except es.APIKeyCreationError as e:
        logger.warning(f"[KEY] Add failed | User: {current_user.id} | Error: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.DuplicateAPIKeyError as e:
        logger.warning(f"[KEY] Duplicate key | User: {current_user.id} | Exchange: {key_data.exchange_name}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.detail))
    except es.APIKeyInvalidError:
        logger.warning(f"[KEY] Invalid credentials | User: {current_user.id} | Exchange: {key_data.exchange_name}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid API credentials")
    except es.ExchangeConnectionError as e:
        logger.error(f"[KEY] Exchange connection failed | User: {current_user.id} | Exchange: {key_data.exchange_name}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e.detail))
    except es.ExchangeVerificationError as e:
        logger.error(f"[KEY] Verification failed | User: {current_user.id} | Error: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))


@router.get("", response_model=List[K.ExchangeKeyResponse])
async def get_exchange_keys(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user),
    exchange: Optional[str] = None
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"[KEY] List request | User: {current_user.id} | Exchange filter: {exchange} | IP: {ip_address}")

    keys = await ExchangeKeysService.get_exchange_keys(db, current_user.id, exchange=exchange)
    logger.info(f"[KEY] Returned {len(keys)} keys for user {current_user.id}")
    return keys


@router.get("/{key_id}", response_model=K.ExchangeKeyResponse)
async def get_exchange_key(
    key_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.debug(f"[KEY] Detail request | Key: {key_id} | User: {current_user.id} | IP: {ip_address}")

    try:
        key = await ExchangeKeysService.get_exchange_keys(db, current_user.id, key_id=key_id)
        return key
    except es.APIKeyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")


@router.put("/{key_id}", response_model=K.ExchangeKeyResponse)
async def update_exchange_key(
    key_id: uuid.UUID,
    update_data: K.ExchangeKeyUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[KEY] Update request | Key: {key_id} | User: {current_user.id} | IP: {ip_address}")

    try:
        updated_key = await ExchangeKeysService.update_exchange_key(db, key_id, update_data, current_user.id)

        trader_profile_id = current_user.trader_profile.id if hasattr(current_user, 'trader_profile') and current_user.trader_profile else None

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="EXCHANGE_KEY_UPDATED",
            resource_type="EXCHANGE_KEY",
            resource_id=str(key_id),
            trader_profile_id=str(trader_profile_id) if trader_profile_id else None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            changes=update_data.model_dump(exclude_unset=True, exclude={"api_secret"}),
            extra_data={"updated_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()
        await db.refresh(updated_key)

        logger.info(f"[KEY] Updated | Key: {key_id} | User: {current_user.id}")
        return updated_key

    except es.APIKeyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    except es.APIKeyInvalidError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid API credentials")
    except es.ExchangeConnectionError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e.detail))


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange_key(
    key_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[KEY] Delete request | Key: {key_id} | User: {current_user.id} | IP: {ip_address}")

    try:
        trader_profile_id = current_user.trader_profile.id if hasattr(current_user, 'trader_profile') and current_user.trader_profile else None

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="EXCHANGE_KEY_DELETED",
            resource_type="EXCHANGE_KEY",
            resource_id=str(key_id),
            trader_profile_id=str(trader_profile_id) if trader_profile_id else None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"deleted_at": datetime.now(timezone.utc).isoformat()}
        )

        await ExchangeKeysService.delete_exchange_key(db, key_id, current_user.id)
        await db.commit()

        logger.info(f"[KEY] Deleted | Key: {key_id} | User: {current_user.id}")
        return None

    except es.APIKeyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")


@router.post("/{key_id}/test", response_model=K.ExchangeKeyTestResult)
async def test_exchange_key(
    key_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[KEY] Test request | Key: {key_id} | User: {current_user.id} | IP: {ip_address}")

    try:
        result = await ExchangeKeysService.test_exchange_key(db, key_id, current_user.id)
        await db.commit()

        logger.info(f"[KEY] Test result | Key: {key_id} | Valid: {result.is_valid} | User: {current_user.id}")
        return result

    except es.APIKeyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
