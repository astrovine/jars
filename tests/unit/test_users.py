import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch, AsyncMock, MagicMock

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import account
from application.models.ledger import Account as LedgerAccount
from application.models.enums import AccountType, UserTier
from application.services.account_service import AccountService
from application.services.registration_service import RegistrationService
from application.schemas import account as account_schema
from application.utilities import oauth2
from application.utilities import exceptions as es


class TestGetUserInfo:
    
    @pytest.mark.asyncio
    async def test_get_full_user_info_success(self, db_session, test_user):
        user = await AccountService.get_full_user_info(db_session, test_user.id)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_full_user_info_nonexistent_returns_none(self, db_session):
        fake_id = uuid.uuid4()
        user = await AccountService.get_full_user_info(db_session, fake_id)
        assert user is None


class TestUpdateUser:
    
    @pytest.mark.asyncio
    async def test_update_user_first_name(self, db_session, test_user):
        update_data = account_schema.UserUpdate(first_name="UpdatedName")
        updated = await AccountService.update_user_account(db_session, update_data, test_user.id)
        assert updated.first_name == "UpdatedName"

    @pytest.mark.asyncio
    async def test_update_user_last_name(self, db_session, test_user):
        update_data = account_schema.UserUpdate(last_name="UpdatedLast")
        updated = await AccountService.update_user_account(db_session, update_data, test_user.id)
        assert updated.last_name == "UpdatedLast"

    @pytest.mark.asyncio
    async def test_update_user_country(self, db_session, test_user):
        update_data = account_schema.UserUpdate(country="GH")
        updated = await AccountService.update_user_account(db_session, update_data, test_user.id)
        assert updated.country == "GH"

    @pytest.mark.asyncio
    async def test_update_user_multiple_fields(self, db_session, test_user):
        update_data = account_schema.UserUpdate(first_name="NewFirst", last_name="NewLast", country="KE")
        updated = await AccountService.update_user_account(db_session, update_data, test_user.id)
        assert updated.first_name == "NewFirst"
        assert updated.last_name == "NewLast"

    @pytest.mark.asyncio
    async def test_update_nonexistent_user_fails(self, db_session):
        fake_id = uuid.uuid4()
        update_data = account_schema.UserUpdate(first_name="Test")
        with pytest.raises(es.UserNotFoundError):
            await AccountService.update_user_account(db_session, update_data, fake_id)

    @pytest.mark.asyncio
    async def test_update_with_empty_data_no_change(self, db_session, test_user):
        original_first = test_user.first_name
        update_data = account_schema.UserUpdate()
        updated = await AccountService.update_user_account(db_session, update_data, test_user.id)
        assert updated.first_name == original_first


class TestPasswordChange:
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, db_session, test_user):
        old_password = "MorningCoffee42!"
        new_password = "EveningTea2025#"
        await AccountService.change_user_password(db_session, test_user.id, old_password, new_password, new_password)
        await db_session.refresh(test_user)
        assert oauth2.verify_password(new_password, test_user.password)

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password_fails(self, db_session, test_user):
        with pytest.raises(es.InvalidCredentialsError):
            await AccountService.change_user_password(db_session, test_user.id, "TotallyWrongOld99!", "NewSecret2026!", "NewSecret2026!")

    @pytest.mark.asyncio
    async def test_change_password_mismatch_confirm_fails(self, db_session, test_user):
        with pytest.raises(es.PasswordMismatchError):
            await AccountService.change_user_password(db_session, test_user.id, "MorningCoffee42!", "FirstNew77!", "DifferentOne88!")

    @pytest.mark.asyncio
    async def test_change_password_nonexistent_user_fails(self, db_session):
        fake_id = uuid.uuid4()
        with pytest.raises(es.UserNotFoundError):
            await AccountService.change_user_password(db_session, fake_id, "OldSecret2024!", "NewSecret2025!", "NewSecret2025!")


class TestDeleteUser:
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, db_session, test_user):
        user_id = test_user.id
        await AccountService.delete_user_account(db_session, user_id)
        await db_session.commit()
        result = await db_session.execute(select(account.User).filter(account.User.id == user_id))
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_fails(self, db_session):
        fake_id = uuid.uuid4()
        with pytest.raises(es.UserNotFoundError):
            await AccountService.delete_user_account(db_session, fake_id)

    @pytest.mark.asyncio
    async def test_delete_user_cascades_wallets(self, db_session, test_user, system_accounts):
        demo_wallet = LedgerAccount(id=uuid.uuid4(), owner_id=test_user.id, type=AccountType.USER_DEMO_WALLET, name="User Demo", currency="USD", balance=Decimal("10000"), is_active=True, is_system=False, created_at=datetime.now(timezone.utc))
        db_session.add(demo_wallet)
        await db_session.commit()
        wallet_id = demo_wallet.id
        user_id = test_user.id
        await AccountService.delete_user_account(db_session, user_id)
        await db_session.commit()
        result = await db_session.execute(select(LedgerAccount).filter(LedgerAccount.id == wallet_id))
        wallet = result.scalar_one_or_none()
        assert wallet is None or wallet.owner_id != user_id


class TestUserUpdateSchema:
    
    def test_user_update_empty_is_valid(self):
        update = account_schema.UserUpdate()
        assert update.first_name is None

    def test_user_update_valid_names(self):
        update = account_schema.UserUpdate(first_name="Valid", last_name="Name")
        assert update.first_name == "Valid"


class TestPasswordChangeSchema:
    
    def test_password_change_valid(self):
        change = account_schema.PasswordChange(old_password="OldSunrise2024!", new_password="NewMoonlight2025!", confirm_password="NewMoonlight2025!")
        assert change.new_password == "NewMoonlight2025!"

    def test_password_change_new_password_validation(self):
        with pytest.raises(ValueError, match="uppercase"):
            account_schema.PasswordChange(old_password="OldSecret2024!", new_password="newpassnoupper123!", confirm_password="newpassnoupper123!")

    def test_password_change_short_password_fails(self):
        with pytest.raises(ValueError):
            account_schema.PasswordChange(old_password="Old123!", new_password="New1!", confirm_password="New1!")


class TestUserResponseSchema:
    
    def test_user_response_has_tier(self):
        response = account_schema.UserResponse(id=uuid.uuid4(), first_name="Test", last_name="User", email="test@example.com", status="VERIFIED", country="NG", is_active=True, is_2fa_enabled=False, tier=UserTier.FREE, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        assert response.tier == UserTier.FREE

    def test_user_response_plus_tier(self):
        response = account_schema.UserResponse(id=uuid.uuid4(), first_name="Plus", last_name="User", email="plus@example.com", status="VERIFIED", country="NG", is_active=True, is_2fa_enabled=False, tier=UserTier.PLUS, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        assert response.tier == UserTier.PLUS


class TestPlusBusinessSchemas:
    
    def test_plus_user_create_with_kyc_fields(self):
        user = account_schema.PlusUserCreate(first_name="Plus", last_name="User", email="plus@example.com", country="NG", password="GoldenSunset2025!", date_of_birth=datetime(1990, 1, 15), id_document_url="https://cloudinary.com/doc.pdf", skip_kyc=False)
        assert user.skip_kyc == False

    def test_plus_user_create_skip_kyc_default_true(self):
        user = account_schema.PlusUserCreate(first_name="Plus", last_name="User", email="plus@example.com", country="NG", password="SilverDawn2026!")
        assert user.skip_kyc == True

    def test_business_user_create_with_company(self):
        user = account_schema.BusinessUserCreate(first_name="Business", last_name="User", email="biz@example.com", country="NG", password="CorporateHQ2025!", company_name="ACME Corp")
        assert user.company_name == "ACME Corp"


class TestEdgeCases:
    
    @pytest.mark.asyncio
    async def test_user_with_very_long_name(self):
        long_name = "A" * 51
        with pytest.raises(ValueError):
            account_schema.UserCreate(first_name=long_name, last_name="User", email="long@example.com", country="NG", password="TooLongName2025!")


class TestUserModelDirectAccess:
    
    @pytest.mark.asyncio
    async def test_user_default_tier_is_free(self, db_session):
        user = account.User(id=uuid.uuid4(), first_name="Default", last_name="Tier", email="default@example.com", status="PENDING", password="hashed", country="NG", is_active=True, is_admin=False, is_2fa_enabled=False, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        assert user.tier == UserTier.FREE

    @pytest.mark.asyncio
    async def test_user_virtual_balance_fields_default_null(self, db_session):
        user = account.User(id=uuid.uuid4(), first_name="Virtual", last_name="Test", email="virtual@example.com", status="PENDING", password="hashed", country="NG", is_active=True, is_admin=False, is_2fa_enabled=False, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        assert user.virtual_balance_reset_at is None
        assert user.virtual_balance_blown_at is None
