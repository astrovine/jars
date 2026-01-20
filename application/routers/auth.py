from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Response, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pyotp
import uuid

from application.models.base import get_db
from application.models import account
from application.schemas import account as account_schema
from application.schemas import token as token_schema
from application.schemas import ledger as ledger_schema
from application.services.auth_service import AuthService
from application.services.account_service import AccountService
from application.services.registration_service import RegistrationService
from application.utilities import oauth2 as o2
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger, log_user_action
from application.utilities.rate_limit import limiter

logger = setup_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=account_schema.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: account_schema.UserCreate, db: AsyncSession = Depends(get_db)):
    ip_address = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.info(f"[REGISTRATION] Free tier signup | Email: {user_data.email} | Country: {user_data.country} | IP: {ip_address}")

    try:
        new_user = await RegistrationService.register_free_user(db, user_data)

        await log_user_action(
            db=db,
            user_id=new_user.id,
            action="USER_REGISTERED",
            resource_type="USER",
            resource_id=str(new_user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={"email": new_user.email, "country": new_user.country, "tier": "free"}
        )
        await db.commit()
        await db.refresh(new_user)

        logger.info(
            f"[REGISTRATION SUCCESS] Free tier user created | ID: {new_user.id} | "
            f"Email: {new_user.email} | 10k V-USDT issued | IP: {ip_address}"
        )
        return new_user

    except es.EmailAlreadyExistsError:
        logger.warning(f"[REGISTRATION BLOCKED] Email already registered: {user_data.email} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    except es.UserCreationError as e:
        logger.error(f"[REGISTRATION FAILED] Error creating user {user_data.email} | IP: {ip_address} | Error: {e.detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.SystemAccountNotFoundError as e:
        logger.error(f"[REGISTRATION FAILED] System account missing | Error: {e.detail}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="System configuration error")


@router.post("/register/plus", response_model=account_schema.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_plus(request: Request, user_data: account_schema.PlusUserCreate, db: AsyncSession = Depends(get_db)):
    ip_address = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.info(f"[REGISTRATION] Plus tier signup | Email: {user_data.email} | IP: {ip_address}")

    try:
        new_user = await RegistrationService.register_plus_user(db, user_data)

        await log_user_action(
            db=db,
            user_id=new_user.id,
            action="USER_REGISTERED",
            resource_type="USER",
            resource_id=str(new_user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={"email": new_user.email, "country": new_user.country, "tier": "plus"}
        )
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"[REGISTRATION SUCCESS] Plus tier user created | ID: {new_user.id} | Email: {new_user.email}")
        return new_user

    except es.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    except es.UserCreationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.SystemAccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="System configuration error")


@router.post("/register/business", response_model=account_schema.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_business(request: Request, user_data: account_schema.BusinessUserCreate, db: AsyncSession = Depends(get_db)):
    ip_address = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.info(f"[REGISTRATION] Business tier signup | Email: {user_data.email} | IP: {ip_address}")

    try:
        new_user = await RegistrationService.register_business_user(db, user_data)

        await log_user_action(
            db=db,
            user_id=new_user.id,
            action="USER_REGISTERED",
            resource_type="USER",
            resource_id=str(new_user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={"email": new_user.email, "country": new_user.country, "tier": "business"}
        )
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"[REGISTRATION SUCCESS] Business tier user created | ID: {new_user.id} | Email: {new_user.email}")
        return new_user

    except es.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    except es.UserCreationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except es.SystemAccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="System configuration error")


@router.post("/login", response_model=account_schema.LoginResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    ip_address = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.info(f"[LOGIN] Login attempt | Email: {form_data.username} | IP: {ip_address}")

    try:
        result = await AuthService.login_user(db, form_data.username, form_data.password)
        user_result = await db.execute(
            select(account.User).filter(account.User.email == form_data.username.lower())
        )
        user = user_result.scalar_one_or_none()

        if not result.get("require_2fa"):
            response.set_cookie(
                key="access_token",
                value=f"Bearer {result['access_token']}",
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=1800
            )
            response.set_cookie(
                key="refresh_token",
                value=result['refresh_token'],
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=604800
            )

            await log_user_action(
                db=db,
                user_id=user.id,
                action="USER_LOGIN",
                resource_type="USER",
                resource_id=str(user.id),
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data={"login_at": datetime.now(timezone.utc).isoformat()}
            )
            await db.commit()

            logger.info(f"[LOGIN SUCCESS] User authenticated | ID: {user.id} | Email: {user.email} | IP: {ip_address}")
        else:
            logger.info(f"[LOGIN 2FA REQUIRED] User needs to complete 2FA | ID: {user.id} | Email: {user.email} | IP: {ip_address}")

        return result

    except es.UserNotFoundError:
        logger.warning(f"[LOGIN FAILED] User not found | Email: {form_data.username} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except es.InvalidCredentialsError:
        logger.warning(f"[LOGIN FAILED] Wrong password | Email: {form_data.username} | IP: {ip_address} - Possible brute force")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except es.EmailNotVerifiedError as e:
        logger.warning(f"[LOGIN BLOCKED] Email not verified | Email: {form_data.username} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e.detail))
    except es.PermissionDeniedError as e:
        logger.warning(f"[LOGIN BLOCKED] Account disabled | Email: {form_data.username} | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e.detail))


@router.post("/2fa/verify", response_model=token_schema.Token)
async def verify_2fa(
    response: Response,
    request: Request,
    data: token_schema.TwoFactorRequest,
    db: AsyncSession = Depends(get_db)
):
    ip_address = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid pre-auth token"
    )

    token_data = o2.verify_pre_auth_token(data.pre_auth_token, credentials_exception)
    logger.info(f"[2FA VERIFY] Verification attempt | User ID: {token_data.id} | IP: {ip_address}")

    try:
        result = await AuthService.verify_2fa_login(db, uuid.UUID(token_data.id), data.code)

        response.set_cookie(
            key="access_token",
            value=f"Bearer {result['access_token']}",
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=1800
        )
        response.set_cookie(
            key="refresh_token",
            value=result['refresh_token'],
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=604800
        )

        await log_user_action(
            db=db,
            user_id=uuid.UUID(token_data.id),
            action="2FA_VERIFIED",
            resource_type="USER",
            resource_id=token_data.id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"verified_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()

        logger.info(f"User {token_data.id} completed 2FA successfully from {ip_address}")
        return result
    except es.InvalidCredentialsError:
        logger.warning(f"2FA failed - invalid code for user {token_data.id} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")
    except es.InvalidRequestError as e:
        logger.error(f"2FA failed - {e.detail} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))


@router.post("/2fa/setup", response_model=token_schema.TwoFactorSetupResponse)
async def setup_2fa(
    request: Request,
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"2FA setup requested by user {current_user.id} from {ip_address}")

    if current_user.is_2fa_enabled:
        logger.warning(f"2FA already enabled for user {current_user.id} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is already enabled")

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=current_user.email, issuer_name="JARS")

    logger.info(f"2FA secret generated for user {current_user.id} from {ip_address}")
    return token_schema.TwoFactorSetupResponse(secret=secret, qr_code_uri=provisioning_uri)


@router.post("/2fa/confirm", status_code=status.HTTP_200_OK)
async def confirm_2fa(
    data: token_schema.TwoFactorConfirmRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"2FA confirmation attempt by user {current_user.id} from {ip_address}")

    try:
        totp = pyotp.TOTP(data.secret)
        if not totp.verify(data.code):
            logger.warning(f"2FA confirmation failed - invalid code for user {current_user.id} from {ip_address}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")

        await AuthService.confirm_2fa(db, data.code, data.secret, current_user.id)

        await log_user_action(
            db=db,
            user_id=current_user.id,
            action="2FA_ENABLED",
            resource_type="USER",
            resource_id=str(current_user.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"enabled_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()

        logger.info(f"2FA enabled successfully for user {current_user.id} from {ip_address}")
        return {"message": "2FA enabled successfully"}
    except es.InvalidCredentialsError:
        logger.warning(f"2FA confirmation failed for user {current_user.id} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")


@router.post("/refresh", response_model=token_schema.Token)
async def refresh_token(
    response: Response,
    request: Request,
    token_data: token_schema.RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    ip_address = request.client.host if request and request.client else "unknown"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )

    refresh_token = token_data.refresh_token or request.cookies.get("refresh_token")
    if not refresh_token:
        logger.warning(f"Token refresh failed - no token provided from {ip_address}")
        raise credentials_exception

    token_payload = await o2.verify_refresh_token(refresh_token, db, credentials_exception)
    logger.info(f"Token refresh for user {token_payload.id} from {ip_address}")

    await o2.revoke_refresh_token(refresh_token, db)

    new_access_token = o2.create_access_token(token_payload.id)
    new_refresh_token = await o2.create_refresh_token(token_payload.id, db)

    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_access_token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800
    )

    logger.info(f"Token refreshed successfully for user {token_payload.id} from {ip_address}")

    return token_schema.Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Logout request from user {current_user.id} from {ip_address}")

    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await o2.revoke_refresh_token(refresh_token, db)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="USER_LOGOUT",
        resource_type="USER",
        resource_id=str(current_user.id),
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent"),
        extra_data={"logout_at": datetime.now(timezone.utc).isoformat()}
    )
    await db.commit()

    logger.info(f"User {current_user.id} logged out successfully from {ip_address}")
    return {"message": "Logged out successfully"}


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all_sessions(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: account.User = Depends(o2.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Logout all sessions request from user {current_user.id} from {ip_address}")

    await o2.revoke_all_user_tokens(current_user.id, db)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="USER_LOGOUT_ALL",
        resource_type="USER",
        resource_id=str(current_user.id),
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent"),
        extra_data={"logout_all_at": datetime.now(timezone.utc).isoformat()}
    )
    await db.commit()

    logger.info(f"User {current_user.id} logged out from all sessions from {ip_address}")
    return {"message": "Logged out from all sessions"}


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def request_password_reset(
    request: Request,
    data: token_schema.PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Password reset requested for email: {data.email} from {ip_address}")

    await AuthService.initiate_password_reset(db, data.email)

    logger.info(f"Password reset email sent (if account exists) for {data.email} from {ip_address}")
    return {"message": "If an account with that email exists, a reset link has been sent"}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    data: token_schema.PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Password reset confirmation attempt from {ip_address}")

    try:
        await AuthService.confirm_password_reset(db, data.token, data.new_password)
        logger.info(f"Password reset successful from {ip_address}")
        return {"message": "Password reset successful"}
    except es.InvalidResetTokenError:
        logger.warning(f"Password reset failed - invalid token from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Email verification attempt from {ip_address}")

    try:
        user = await AccountService.verify_email(db, token)

        await log_user_action(
            db=db,
            user_id=user.id,
            action="EMAIL_VERIFIED",
            resource_type="USER",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"verified_at": datetime.now(timezone.utc).isoformat()}
        )
        await db.commit()

        logger.info(f"Email verified successfully for user {user.id} from {ip_address}")
        return {"message": "Email verified successfully", "user_id": str(user.id)}
    except es.InvalidVerificationTokenError:
        logger.warning(f"Email verification failed - invalid token from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")
    except es.ExpiredVerificationTokenError:
        logger.warning(f"Email verification failed - expired token from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token has expired")
    except es.UserAlreadyVerifiedError:
        logger.warning(f"Email verification failed - already verified from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")
    except es.VerificationError as e:
        logger.error(f"Email verification failed: {e.detail} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def resend_verification(request: Request, email: str, db: AsyncSession = Depends(get_db)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Resend verification requested for email: {email} from {ip_address}")

    try:
        await AccountService.resend_verification_email(db, email)
        await db.commit()
        logger.info(f"Verification email resent (if account exists) for {email} from {ip_address}")
        return {"message": "If an unverified account exists, a verification email has been sent"}
    except es.UserAlreadyVerifiedError:
        logger.warning(f"Resend verification failed - already verified: {email} from {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")
