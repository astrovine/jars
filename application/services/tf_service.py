import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from application.models import account
from application.models.enums import TraderProfileStatus, VerificationStatus, UserTier
from application.models.trader_profile import TraderProfile
from application.models.kyc import UserKYC
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger
from application.utilities.config import settings
from application.schemas import trader_profile as tp
from application.schemas import kyc as kyc_schema
from datetime import datetime, timezone
from typing import List, Optional
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import UploadFile

logger = setup_logger(__name__)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


class TraderProfileService:
    @staticmethod
    async def apply_to_become_trader(db: AsyncSession, user_id: uuid.UUID, trader_data: tp.TraderProfileCreate) -> TraderProfile:
        result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise es.UserNotFoundError()

        if user.trader_profile:
            raise es.TraderProfileCreationError('User already has a trader profile')

        if not user.is_2fa_enabled:
            raise es.TraderProfileCreationError('2FA must be enabled to apply as a trader')

        alias = trader_data.alias if trader_data.alias else f"trader_{user.email.split('@')[0]}"

        alias_result = await db.execute(
            select(TraderProfile).filter(TraderProfile.alias == alias)
        )
        existing_alias = alias_result.scalar_one_or_none()
        if existing_alias:
            raise es.TraderProfileCreationError('Alias already taken')

        try:
            new_trader = TraderProfile(
                user_id=user_id,
                alias=alias,
                bio=trader_data.bio,
                avatar_url=trader_data.avatar_url,
                performance_fee_percentage=trader_data.performance_fee_percentage,
                min_allocation_amount=trader_data.min_allocation_amount,
                status=TraderProfileStatus.DRAFT
            )

            db.add(new_trader)
            await db.flush()
            await db.refresh(new_trader)

            logger.info(f"Trader profile application created for user {user_id} with alias {alias} - Status: DRAFT")
            return new_trader

        except IntegrityError as e:
            logger.error(f"Integrity error creating trader profile: {e}", exc_info=True)
            raise es.TraderProfileCreationError("Database constraint violated")
        except Exception as e:
            logger.error(f"Failed to create trader profile for user {user_id}: {e}", exc_info=True)
            raise es.TraderProfileCreationError("Failed to create trader profile")

    @staticmethod
    async def upload_kyc_document(user_id: uuid.UUID, file: UploadFile) -> str:
        try:
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
            if file.content_type not in allowed_types:
                raise es.KYCError(f"Invalid file type. Allowed: JPEG, PNG, PDF")

            max_size = 10 * 1024 * 1024
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

            if file_size > max_size:
                raise es.KYCError("File size exceeds 10MB limit")

            file_content = await asyncio.to_thread(file.file.read)
            file.file.seek(0)

            def _do_upload():
                return cloudinary.uploader.upload(
                    file_content,
                    folder=f"kyc_documents/{user_id}",
                    resource_type="auto",
                    public_id=f"kyc_doc_{datetime.now(timezone.utc).timestamp()}",
                    overwrite=False,
                    transformation=[
                        {'quality': 'auto'},
                        {'fetch_format': 'auto'}
                    ]
                )

            upload_result = await asyncio.to_thread(_do_upload)

            document_url = upload_result.get('secure_url')
            logger.info(f"KYC document uploaded to Cloudinary for user {user_id} - URL: {document_url}")
            return document_url

        except CloudinaryError as e:
            logger.error(f"Cloudinary upload failed for user {user_id}: {e}", exc_info=True)
            raise es.KYCError(f"Failed to upload document: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error uploading KYC document for user {user_id}: {e}", exc_info=True)
            raise es.KYCError("Failed to upload KYC document")

    @staticmethod
    async def submit_kyc(
        db: AsyncSession,
        user_id: uuid.UUID,
        kyc_data: kyc_schema.KYCCreate,
        id_document: Optional[UploadFile] = None
    ) -> UserKYC:
        result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise es.UserNotFoundError()

        if not user.trader_profile:
            raise es.TraderProfileNotFoundError("Must apply as trader first")

        if user.trader_profile.status not in [TraderProfileStatus.DRAFT, TraderProfileStatus.PENDING_KYC]:
            raise es.KYCError("KYC already submitted or profile is active")

        document_url = None
        if id_document:
            document_url = await TraderProfileService.upload_kyc_document(user_id, id_document)
        elif kyc_data.id_document_url:
            document_url = kyc_data.id_document_url

        if not document_url:
            raise es.KYCError("ID document is required for KYC submission")

        kyc_result = await db.execute(
            select(UserKYC).filter(UserKYC.user_id == user_id)
        )
        existing_kyc = kyc_result.scalar_one_or_none()

        if existing_kyc:
            if existing_kyc.status == VerificationStatus.APPROVED:
                raise es.KYCError("KYC already approved")

            for field, value in kyc_data.model_dump(exclude_unset=True, exclude={'id_document_url'}).items():
                setattr(existing_kyc, field, value)
            existing_kyc.status = VerificationStatus.PENDING
            existing_kyc.rejection_reason = None
            existing_kyc.id_document_url = document_url

            await db.flush()
            await db.refresh(existing_kyc)

            user.trader_profile.status = TraderProfileStatus.PENDING_KYC
            await db.flush()

            logger.info(f"KYC resubmitted for user {user_id}")
            return existing_kyc

        try:
            new_kyc = UserKYC(
                user_id=user_id,
                first_name=kyc_data.first_name,
                last_name=kyc_data.last_name,
                country=kyc_data.country,
                date_of_birth=kyc_data.date_of_birth,
                id_document_url=document_url,
                past_trades=kyc_data.past_trades,
                status=VerificationStatus.PENDING
            )

            db.add(new_kyc)
            await db.flush()
            await db.refresh(new_kyc)

            user.trader_profile.status = TraderProfileStatus.PENDING_KYC
            await db.flush()

            logger.info(f"KYC submitted for user {user_id}")
            return new_kyc

        except IntegrityError as e:
            logger.error(f"Integrity error submitting KYC: {e}", exc_info=True)
            raise es.KYCError("Failed to submit KYC")
        except Exception as e:
            logger.error(f"Unexpected error submitting KYC for user {user_id}: {e}", exc_info=True)
            raise es.KYCError("Failed to submit KYC")

    @staticmethod
    async def approve_kyc(db: AsyncSession, user_id: uuid.UUID, admin_notes: Optional[str] = None) -> TraderProfile:
        result = await db.execute(
            select(UserKYC).filter(UserKYC.user_id == user_id)
        )
        kyc = result.scalar_one_or_none()

        if not kyc:
            raise es.KYCNotFoundError()

        user_result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user.trader_profile:
            raise es.TraderProfileNotFoundError()

        kyc.status = VerificationStatus.APPROVED
        kyc.rejection_reason = None

        trader_profile = user.trader_profile
        trader_profile.status = TraderProfileStatus.INCUBATION
        trader_profile.probation_start_date = datetime.now(timezone.utc)
        trader_profile.probation_trades_count = 0

        if user.tier in [UserTier.PLUS, UserTier.BUSINESS]:
            from application.services.registration_service import RegistrationService
            await RegistrationService.activate_live_wallet(db, user_id)
            logger.info(f"Live wallet activated for {user.tier.value} user {user_id}")

        await db.flush()
        await db.refresh(trader_profile)

        logger.info(f"KYC approved for user {user_id} - Trader profile moved to INCUBATION")
        return trader_profile

    @staticmethod
    async def reject_kyc(db: AsyncSession, user_id: uuid.UUID, rejection_reason: str) -> UserKYC:
        result = await db.execute(
            select(UserKYC).filter(UserKYC.user_id == user_id)
        )
        kyc = result.scalar_one_or_none()

        if not kyc:
            raise es.KYCNotFoundError()

        user_result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        kyc.status = VerificationStatus.REJECTED
        kyc.rejection_reason = rejection_reason

        if user.trader_profile:
            user.trader_profile.status = TraderProfileStatus.DRAFT

        await db.flush()
        await db.refresh(kyc)

        logger.info(f"KYC rejected for user {user_id} - Reason: {rejection_reason}")
        return kyc

    @staticmethod
    async def get_trader_profile(db: AsyncSession, trader_id: uuid.UUID) -> TraderProfile:
        result = await db.execute(
            select(TraderProfile).filter(TraderProfile.id == trader_id)
        )
        trader = result.scalar_one_or_none()

        if not trader:
            raise es.TraderProfileNotFoundError()

        return trader

    @staticmethod
    async def get_trader_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[TraderProfile]:
        result = await db.execute(
            select(account.User).filter(account.User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise es.UserNotFoundError()

        return user.trader_profile

    @staticmethod
    async def list_active_traders(db: AsyncSession, skip: int = 0, limit: int = 50) -> List[TraderProfile]:
        result = await db.execute(
            select(TraderProfile).filter(
                TraderProfile.status == TraderProfileStatus.ACTIVE,
                TraderProfile.is_active == True
            ).offset(skip).limit(limit)
        )
        traders = result.scalars().all()

        return traders

    @staticmethod
    async def graduate_trader(db: AsyncSession, trader_id: uuid.UUID) -> TraderProfile:
        result = await db.execute(
            select(TraderProfile).filter(TraderProfile.id == trader_id)
        )
        trader = result.scalar_one_or_none()

        if not trader:
            raise es.TraderProfileNotFoundError()

        if trader.status != TraderProfileStatus.INCUBATION:
            raise es.TraderProfileError(f"Trader must be in INCUBATION status, current: {trader.status}")

        if trader.probation_trades_count < 10:
            raise es.TraderProfileError(f"Trader needs at least 10 trades, current: {trader.probation_trades_count}")

        if trader.win_rate < 60.0:
            raise es.TraderProfileError(f"Trader needs at least 60% win rate, current: {trader.win_rate}%")

        trader.status = TraderProfileStatus.ACTIVE

        await db.flush()
        await db.refresh(trader)

        logger.info(f"Trader {trader_id} graduated to ACTIVE status - Trades: {trader.probation_trades_count}, Win Rate: {trader.win_rate}%")
        return trader

    @staticmethod
    async def update_trader_profile(db: AsyncSession, trader_id: uuid.UUID, user_id: uuid.UUID, update_data: tp.TraderProfileUpdate) -> TraderProfile:
        result = await db.execute(
            select(TraderProfile).filter(
                TraderProfile.id == trader_id,
                TraderProfile.user_id == user_id
            )
        )
        trader = result.scalar_one_or_none()

        if not trader:
            raise es.TraderProfileNotFoundError()

        try:
            update_dict = update_data.model_dump(exclude_unset=True)

            for field, value in update_dict.items():
                setattr(trader, field, value)

            await db.flush()
            await db.refresh(trader)

            logger.info(f"Trader profile {trader_id} updated by user {user_id}")
            return trader

        except IntegrityError as e:
            logger.error(f"Integrity error updating trader profile: {e}", exc_info=True)
            raise es.TraderProfileError("Failed to update trader profile")
        except Exception as e:
            logger.error(f"Unexpected error updating trader profile {trader_id}: {e}", exc_info=True)
            raise es.TraderProfileError("Failed to update trader profile")

    @staticmethod
    async def delete_trader_profile(db: AsyncSession, trader_id: uuid.UUID, user_id: uuid.UUID) -> None:
        result = await db.execute(
            select(TraderProfile).filter(
                TraderProfile.id == trader_id,
                TraderProfile.user_id == user_id
            )
        )
        trader = result.scalar_one_or_none()

        if not trader:
            raise es.TraderProfileNotFoundError()

        if trader.status == TraderProfileStatus.ACTIVE:
            raise es.TraderProfileError("Cannot delete active trader profile. Please deactivate first.")

        try:
            await db.delete(trader)
            await db.flush()

            logger.info(f"Trader profile {trader_id} deleted by user {user_id}")

        except Exception as e:
            logger.error(f"Failed to delete trader profile {trader_id}: {e}", exc_info=True)
            raise es.TraderProfileError("Failed to delete trader profile")

    @staticmethod
    async def deactivate_trader_profile(db: AsyncSession, trader_id: uuid.UUID, user_id: uuid.UUID) -> TraderProfile:
        result = await db.execute(
            select(TraderProfile).filter(
                TraderProfile.id == trader_id,
                TraderProfile.user_id == user_id
            )
        )
        trader = result.scalar_one_or_none()

        if not trader:
            raise es.TraderProfileNotFoundError()

        trader.is_active = False

        await db.flush()
        await db.refresh(trader)

        logger.info(f"Trader profile {trader_id} deactivated by user {user_id}")
        return trader

    @staticmethod
    async def reactivate_trader_profile(db: AsyncSession, trader_id: uuid.UUID, user_id: uuid.UUID) -> TraderProfile:
        result = await db.execute(
            select(TraderProfile).filter(
                TraderProfile.id == trader_id,
                TraderProfile.user_id == user_id
            )
        )
        trader = result.scalar_one_or_none()

        if not trader:
            raise es.TraderProfileNotFoundError()

        if trader.status != TraderProfileStatus.ACTIVE:
            raise es.TraderProfileError("Can only reactivate profiles that are in ACTIVE status")

        trader.is_active = True

        await db.flush()
        await db.refresh(trader)

        logger.info(f"Trader profile {trader_id} reactivated by user {user_id}")
        return trader

    @staticmethod
    async def suspend_trader_profile(db: AsyncSession, trader_id: uuid.UUID, admin_notes: Optional[str] = None) -> TraderProfile:
        result = await db.execute(
            select(TraderProfile).filter(TraderProfile.id == trader_id)
        )
        trader = result.scalar_one_or_none()

        if not trader:
            raise es.TraderProfileNotFoundError()

        trader.status = TraderProfileStatus.SUSPENDED
        trader.is_active = False

        await db.flush()
        await db.refresh(trader)

        logger.info(f"Trader profile {trader_id} suspended - Notes: {admin_notes}")
        return trader

    @staticmethod
    async def update_trader_stats(
        db: AsyncSession,
        trader_id: uuid.UUID,
        win_rate: Optional[float] = None,
        total_roi: Optional[float] = None,
        risk_score: Optional[float] = None,
        increment_trades: bool = False
    ) -> TraderProfile:
        result = await db.execute(
            select(TraderProfile).filter(TraderProfile.id == trader_id)
        )
        trader = result.scalar_one_or_none()

        if not trader:
            raise es.TraderProfileNotFoundError()

        if win_rate is not None:
            trader.win_rate = win_rate

        if total_roi is not None:
            trader.total_roi = total_roi

        if risk_score is not None:
            trader.risk_score = risk_score

        if increment_trades and trader.status == TraderProfileStatus.INCUBATION:
            trader.probation_trades_count += 1

        await db.flush()
        await db.refresh(trader)

        logger.info(f"Stats updated for trader {trader_id} - Win Rate: {trader.win_rate}%, ROI: {trader.total_roi}%, Trades: {trader.probation_trades_count}")
        return trader
