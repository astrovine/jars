import uuid
import secrets
import pyotp
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from application.models import account
from application.services.account_service import AccountService
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger
from application.utilities import oauth2 as o2
from application.core.tasks import task_send_password_reset_email as task_send_reset_email

logger = setup_logger(__name__)


class AuthService:
    @staticmethod
    async def login_user(db: AsyncSession, email: str, password: str) -> Dict[str, Any]:
        logger.info(f"[AUTH] Login attempt for email: {email}")

        result = await db.execute(
            select(account.User).filter(account.User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.warning(f"[AUTH FAILED] Login attempt for non-existent account: {email}")
            raise es.UserNotFoundError()

        if not o2.verify_password(password, user.password):
            logger.warning(f"[AUTH FAILED] Invalid password for user {user.id} ({email}) - possible brute force attempt")
            raise es.InvalidCredentialsError()

        if user.status == "PENDING":
            logger.warning(f"[AUTH BLOCKED] User {user.id} ({email}) tried to login before email verification")
            raise es.EmailNotVerifiedError("Please verify your email before logging in")

        if not user.is_active:
            logger.warning(f"[AUTH BLOCKED] Disabled account login attempt | User: {user.id} ({email})")
            raise es.PermissionDeniedError("Account is disabled")

        if getattr(user, "is_2fa_enabled", False):
            logger.info(f"[AUTH 2FA] User {user.id} requires 2FA verification - issuing pre-auth token")
            pre_auth_tk = o2.create_pre_auth_token(user.id)
            return {
                "require_2fa": True,
                "pre_auth_token": pre_auth_tk,
                "message": "2FA verification required"
            }

        try:
            access_token = o2.create_access_token(user.id)
            refresh_token = await o2.create_refresh_token(user.id, db)

            logger.info(f"[AUTH SUCCESS] User {user.id} ({email}) logged in successfully")
            return {
                "require_2fa": False,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
        except Exception as e:
            logger.error(f"[AUTH ERROR] Token creation failed for user {user.id} | Error: {e}")
            raise es.AuthenticationError("Failed to create authentication tokens")

    @staticmethod
    async def confirm_2fa(db: AsyncSession, code: str, secret: str, user_id: uuid.UUID) -> bool:
        logger.info(f"[2FA SETUP] User {user_id} is confirming 2FA setup")

        totp = pyotp.TOTP(secret)
        if not totp.verify(code):
            logger.warning(f"[2FA SETUP FAILED] Invalid code provided by user {user_id}")
            raise es.InvalidCredentialsError("Invalid 2FA code")

        user = await AccountService.get_user_basic(db, user_id)

        from cryptography.fernet import Fernet
        from application.utilities.config import settings
        cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        encrypted_secret = cipher.encrypt(secret.encode()).decode()

        user.two_factor_secret = encrypted_secret
        user.is_2fa_enabled = True
        await db.flush()
        await db.refresh(user)

        logger.info(f"[2FA ENABLED] User {user.id} ({user.email}) successfully enabled two-factor authentication")
        return True

    @staticmethod
    async def verify_2fa_login(db: AsyncSession, user_id: uuid.UUID, code: str) -> Dict[str, str]:
        logger.info(f"[2FA VERIFY] Verifying 2FA code for user {user_id}")

        user = await AccountService.get_user_basic(db, user_id)

        if not user.is_2fa_enabled or not user.two_factor_secret:
            logger.error(f"[2FA ERROR] User {user_id} attempted 2FA verify but 2FA is not enabled")
            raise es.InvalidRequestError("2FA is not enabled for this account")

        from cryptography.fernet import Fernet
        from application.utilities.config import settings
        cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        decrypted_secret = cipher.decrypt(user.two_factor_secret.encode()).decode()

        totp = pyotp.TOTP(decrypted_secret)

        if not totp.verify(code, valid_window=1):
            logger.warning(f"[2FA FAILED] Invalid 2FA code for user {user_id} ({user.email}) - possible unauthorized access attempt")
            raise es.InvalidCredentialsError("Invalid 2FA code")

        logger.info(f"[2FA SUCCESS] User {user_id} ({user.email}) passed 2FA verification")
        access_token = o2.create_access_token(user.id)
        refresh_token = await o2.create_refresh_token(user.id, db)

        logger.info(f"[AUTH COMPLETE] User {user_id} fully authenticated with 2FA")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    async def initiate_password_reset(db: AsyncSession, email: str):
        logger.info(f"[PASSWORD RESET] Reset requested for email: {email}")

        result = await db.execute(
            select(account.User).filter(account.User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.info(f"[PASSWORD RESET] No account found for {email} - no email will be sent (security measure)")
            return

        reset_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()

        user.password_reset_token = token_hash
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.commit()

        task_send_reset_email.delay(user.email, reset_token)
        logger.info(f"[PASSWORD RESET] Reset token generated and email queued for user {user.id} ({email}) - expires in 15 minutes")

    @staticmethod
    async def confirm_password_reset(db: AsyncSession, token: str, new_password: str):
        logger.info("[PASSWORD RESET] Attempting to confirm password reset with token")

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        result = await db.execute(
            select(account.User).filter(
                account.User.password_reset_token == token_hash,
                account.User.password_reset_expires > datetime.now(timezone.utc)
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("[PASSWORD RESET FAILED] Invalid or expired reset token used")
            raise es.InvalidResetTokenError()

        user.password = o2.get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None

        await o2.revoke_all_user_tokens(user.id, db)

        await db.commit()
        logger.info(f"[PASSWORD RESET SUCCESS] User {user.id} ({user.email}) reset their password - all existing sessions revoked for security")
        return True