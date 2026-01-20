import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc
from ..models import account, audit_logs
from ..models import ledger as ledger_models
from ..models.enums import AccountType
from ..utilities import exceptions as es
from ..utilities import audit, oauth2
from ..schemas import account as at
from ..schemas import ledger as ledger_schemas
from application.models.enums import AccountType
from application.tasks import task_send_verification_email, task_send_welcome_email

logger = audit.setup_logger(__name__)


class AccountService:
    @staticmethod
    async def create_new_user(db: AsyncSession, user: at.UserCreate, wallet: ledger_schemas.CreatNewAccount) -> account.User:
        """
        DEPRECATED: This method is no longer used.
        """
        logger.info(f"[USER REGISTRATION] Starting registration for email: {user.email}")

        try:
            result = await db.execute(
                select(account.User).filter(account.User.email == user.email)
            )
            existing_account = result.scalar_one_or_none()
            if existing_account:
                logger.warning(f"[REGISTRATION BLOCKED] Email already registered: {user.email}")
                raise es.EmailAlreadyExistsError(f"Email {user.email} already exists")

            password = oauth2.get_password_hash(user.password)
            new_user = account.User(
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                status='PENDING',
                password=password,
                country=user.country,
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_user)
            await db.flush()
            logger.info(f"[USER CREATED] User record created | ID: {new_user.id} | Email: {user.email}")

            wallet_type_str = wallet.type.upper() if isinstance(wallet.type, str) else ""
            
            if wallet_type_str == "USER_WALLET":
                account_type = AccountType.USER_LIVE_WALLET
            else:
                account_type = getattr(AccountType, wallet.type.upper()) if isinstance(wallet.type, str) else wallet.type

            new_account = ledger_models.Account(
                owner_id=new_user.id,
                currency=wallet.currency,
                name=f'{new_user.first_name} {new_user.last_name}',
                type=account_type,
                is_active=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_account)
            await db.flush()
            logger.info(f"[WALLET CREATED] Wallet created for user {new_user.id} | Wallet ID: {new_account.id} | Status: Inactive")

            verification_token = secrets.token_urlsafe(32)
            verification_token_hash = hashlib.sha256(verification_token.encode()).hexdigest()
            new_user.email_verification_token = verification_token_hash
            new_user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
            await db.flush()

            task_send_verification_email.delay(new_user.email, verification_token)
            logger.info(f"[EMAIL QUEUED] Verification email queued for user {new_user.id} ({user.email})")

            return new_user

        except es.EmailAlreadyExistsError:
            raise
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"[DATABASE ERROR] Integrity error during registration for {user.email} | Error: {str(e)}")
            raise es.UserCreationError("Database constraint violated")
        except Exception as e:
            logger.error(f"[REGISTRATION FAILED] Unexpected error for {user.email} | Error: {e}")
            await db.rollback()
            raise es.UserCreationError(f"Failed to create user: {str(e)}")

    @staticmethod
    async def find_or_create_oauth(db: AsyncSession, user_info: dict) -> account.User:
        email = user_info.get("email")
        if not email:
            logger.error("[OAUTH ERROR] No email provided in OAuth response")
            raise es.InvalidRequestError("Email not found in Oauth2 provider response")

        logger.info(f"[OAUTH] Processing OAuth login for email: {email}")

        result = await db.execute(
            select(account.User).filter(account.User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            logger.info(f"[OAUTH] Existing user found | ID: {existing_user.id} | Email: {email}")
            return existing_user

        logger.info(f"[OAUTH] No existing user found - creating new account for {email}")
        random_password = oauth2.generate_random_password()
        first_name = user_info.get("given_name", "")
        last_name = user_info.get("family_name", "")

        try:
            from application.services.registration_service import RegistrationService
            new_user = await RegistrationService.register_free_user(
                db,
                at.UserCreate(
                    email=email,
                    password=random_password,
                    first_name=first_name,
                    last_name=last_name,
                    country=user_info.get("locale", "Nigeria"),
                    phone_number=None
                )
            )
            logger.info(f"[OAUTH SUCCESS] Created new OAuth user | ID: {new_user.id} | Email: {email}")
            return new_user
        except Exception as e:
            logger.error(f"[OAUTH FAILED] Could not create OAuth user for {email} | Error: {e}")
            raise es.UserCreationError(detail="Could not create user account.")

    @staticmethod
    async def get_user_basic(db: AsyncSession, user_id: uuid.UUID) -> account.User:
        logger.debug(f"[USER LOOKUP] Fetching user by ID: {user_id}")
        try:
            result = await db.execute(
                select(account.User).filter(account.User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                logger.warning(f"[USER NOT FOUND] No user exists with ID: {user_id}")
                raise es.UserNotFoundError(f"User with id: {user_id} not found")
            return user
        except Exception as e:
            logger.error(f"[USER LOOKUP FAILED] Error fetching user {user_id} | Error: {e}")
            raise

    @staticmethod
    async def update_user_account(db: AsyncSession, update_data: at.UserUpdate, user_id: uuid.UUID) -> account.User:
        try:
            result = await db.execute(
                select(account.User).filter(account.User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise es.UserNotFoundError(f"User with id: {user_id} not found")

            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(user, key, value)

            await db.flush()
            await db.refresh(user)

            return user

        except es.UserNotFoundError:
            raise
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error updating user {user_id}: {e}", exc_info=True)
            raise es.UserUpdateError("Database constraint violated during update")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update user: {e}", exc_info=True)
            raise es.UserUpdateError("Unexpected error updating user")

    @staticmethod
    async def delete_user_account(db: AsyncSession, user_id: uuid.UUID) -> None:
        try:
            result = await db.execute(
                select(account.User).filter(account.User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise es.UserNotFoundError(f"User with id: {user_id} not found")

            await db.delete(user)
            await db.flush()

        except es.UserNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete user: {e}", exc_info=True)
            raise es.DatabaseError("Failed to delete user")


    @staticmethod
    async def change_user_password(db: AsyncSession, user_id: uuid.UUID, old_password: str, new_password: str, confirm_password: str) -> None:
        try:
            result = await db.execute(
                select(account.User).filter(account.User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise es.UserNotFoundError(f"User with id: {user_id} not found")

            verify_password = oauth2.verify_password(old_password, user.password)
            if not verify_password:
                raise es.InvalidCredentialsError("Invalid credentials")

            if not new_password == confirm_password:
                raise es.PasswordMismatchError()

            user.password = oauth2.get_password_hash(new_password)
            await db.flush()
            await db.refresh(user)
            logger.debug(f"Password updated in DB for user {user.id}")

        except (es.UserNotFoundError, es.InvalidCredentialsError, es.PasswordMismatchError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Database error updating password for user {user_id}: {e}", exc_info=True)
            raise es.DatabaseError("Failed to update password")

    @staticmethod
    async def get_full_user_info(db: AsyncSession, user_id: uuid.UUID) -> Optional[account.User]:
        try:
            result = await db.execute(
                select(account.User)
                .options(
                    joinedload(account.User.kyc),
                    joinedload(account.User.trader_profile)
                )
                .filter(account.User.id == user_id)
            )
            user = result.unique().scalar_one_or_none()

            if user:
                logger.debug(
                    f"Retrieved user {user_id}, "
                    f"KYC present: {user.kyc is not None}, "
                    f"Trader profile present: {user.trader_profile is not None}"
                )
            else:
                logger.warning(f"User {user_id} not found")

            return user

        except Exception as e:
            logger.error(f"Failed to get full user info for {user_id}: {e}", exc_info=True)
            raise es.DatabaseError("Failed to retrieve user information")

    @staticmethod
    async def get_activity_logs(db: AsyncSession, user: account.User) -> Sequence[audit_logs.AuditLog]:
        try:
            query = select(audit_logs.AuditLog).where(
                audit_logs.AuditLog.user_id == user.id
            )

            if user.trader_profile and user.trader_profile.id:
                query = select(audit_logs.AuditLog).where(
                    (audit_logs.AuditLog.user_id == user.id) |
                    (audit_logs.AuditLog.trader_profile_id == user.trader_profile.id)
                )

            query = query.order_by(desc(audit_logs.AuditLog.created_at))

            result = await db.execute(query)
            logs = result.scalars().all()

            logger.debug(f"Retrieved {len(logs)} activity logs for user {user.id}")
            return logs

        except Exception as e:
            logger.error(f"Error getting activity logs for user {user.id}: {str(e)}", exc_info=True)
            raise es.DatabaseError("Failed to retrieve activity logs")

    @staticmethod
    async def verify_email(db: AsyncSession, token: str) -> account.User:
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            result = await db.execute(
                select(account.User).filter(
                    account.User.email_verification_token == token_hash
                )
            )
            user = result.scalar_one_or_none()

            if not user:
                raise es.InvalidVerificationTokenError("Invalid verification token")

            if user.email_verification_expires and user.email_verification_expires < datetime.now(timezone.utc):
                raise es.ExpiredVerificationTokenError("Verification token has expired")

            if user.status == "VERIFIED":
                raise es.UserAlreadyVerifiedError()

            user.status = "VERIFIED"
            user.is_active = True
            user.email_verification_token = None
            user.email_verification_expires = None

            accounts_result = await db.execute(
                select(ledger_models.Account).filter(
                    ledger_models.Account.owner_id == user.id
                )
            )
            user_accounts = accounts_result.scalars().all()
            for acc in user_accounts:
                acc.is_active = True

            await db.flush()
            await db.refresh(user)

            task_send_welcome_email.delay(user.email, user.first_name)

            logger.info(f"Email verified for user {user.id}, account activated")
            return user

        except (es.InvalidVerificationTokenError, es.ExpiredVerificationTokenError, es.UserAlreadyVerifiedError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to verify email: {e}", exc_info=True)
            raise es.VerificationError("Email verification failed")

    @staticmethod
    async def resend_verification_email(db: AsyncSession, email: str) -> None:
        try:
            result = await db.execute(
                select(account.User).filter(account.User.email == email)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.info(f"Verification resend requested for non-existent email: {email}")
                return

            if user.status == "VERIFIED":
                raise es.UserAlreadyVerifiedError()

            verification_token = secrets.token_urlsafe(32)
            verification_token_hash = hashlib.sha256(verification_token.encode()).hexdigest()
            user.email_verification_token = verification_token_hash
            user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)

            await db.flush()
            await db.refresh(user)

            task_send_verification_email.delay(user.email, verification_token)
            logger.info(f"Verification email resent to {email}")

        except es.UserAlreadyVerifiedError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to resend verification email to {email}: {e}", exc_info=True)
            raise es.DatabaseError("Failed to resend verification email")
