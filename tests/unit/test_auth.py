import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch, AsyncMock

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import account
from application.models.ledger import Account as LedgerAccount, LedgerTransaction
from application.models.enums import AccountType, UserTier, TransactionType
from application.services.registration_service import RegistrationService
from application.services.auth_service import AuthService
from application.schemas import account as account_schema
from application.utilities import oauth2
from application.utilities import exceptions as es


class TestUserRegistration:
    
    @pytest.mark.asyncio
    async def test_register_free_user_success(self, db_session, system_accounts, mock_send_email):
        user_data = account_schema.UserCreate(
            first_name="Test",
            last_name="User",
            email="newuser@example.com",
            country="NG",
            password="SunriseHarbor42!"
        )
        
        user = await RegistrationService.register_free_user(db_session, user_data)
        await db_session.commit()
        
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.tier == UserTier.FREE
        assert user.status == "PENDING"
        
        result = await db_session.execute(
            select(LedgerAccount).filter(
                LedgerAccount.owner_id == user.id,
                LedgerAccount.type == AccountType.USER_DEMO_WALLET
            )
        )
        demo_wallet = result.scalar_one_or_none()
        
        assert demo_wallet is not None
        assert demo_wallet.balance == Decimal("10000")
        assert demo_wallet.currency == "USD"
        assert demo_wallet.is_active == True
        
        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_free_user_duplicate_email_fails(self, db_session, test_user, system_accounts, mock_send_email):
        user_data = account_schema.UserCreate(
            first_name="Duplicate",
            last_name="User",
            email=test_user.email,
            country="NG",
            password="MidnightRiver99!"
        )
        
        with pytest.raises(es.EmailAlreadyExistsError):
            await RegistrationService.register_free_user(db_session, user_data)

    @pytest.mark.asyncio
    async def test_register_plus_user_creates_both_wallets(self, db_session, system_accounts, mock_send_email):
        user_data = account_schema.UserCreate(
            first_name="Plus",
            last_name="User",
            email="plusnew@example.com",
            country="NG",
            password="GoldenMeadow77!"
        )
        
        user = await RegistrationService.register_plus_user(db_session, user_data)
        await db_session.commit()
        
        assert user.tier == UserTier.PLUS
        
        result = await db_session.execute(
            select(LedgerAccount).filter(LedgerAccount.owner_id == user.id)
        )
        wallets = result.scalars().all()
        
        wallet_types = {w.type for w in wallets}
        assert AccountType.USER_DEMO_WALLET in wallet_types
        assert AccountType.USER_LIVE_WALLET in wallet_types
        
        demo_wallet = next(w for w in wallets if w.type == AccountType.USER_DEMO_WALLET)
        live_wallet = next(w for w in wallets if w.type == AccountType.USER_LIVE_WALLET)
        
        assert demo_wallet.is_active == True
        assert live_wallet.is_active == False

    @pytest.mark.asyncio
    async def test_register_business_user_creates_both_wallets(self, db_session, system_accounts, mock_send_email):
        user_data = account_schema.UserCreate(
            first_name="Business",
            last_name="User",
            email="business@example.com",
            country="NG",
            password="SilverMountain88!"
        )
        
        user = await RegistrationService.register_business_user(db_session, user_data)
        await db_session.commit()
        
        assert user.tier == UserTier.BUSINESS
        
        result = await db_session.execute(
            select(LedgerAccount).filter(LedgerAccount.owner_id == user.id)
        )
        wallets = result.scalars().all()
        
        assert len(wallets) == 2

    @pytest.mark.asyncio
    async def test_register_without_system_accounts_fails(self, db_session, mock_send_email):
        user_data = account_schema.UserCreate(
            first_name="Test",
            last_name="User",
            email="nosystem@example.com",
            country="NG",
            password="OceanBreeze2024!"
        )
        
        with pytest.raises(es.SystemAccountNotFoundError):
            await RegistrationService.register_free_user(db_session, user_data)


class TestPasswordValidation:
    
    def test_password_without_uppercase_fails(self):
        with pytest.raises(ValueError, match="uppercase"):
            account_schema.UserCreate(
                first_name="Test",
                last_name="User",
                email="test@example.com",
                country="NG",
                password="nouppercase123!"
            )

    def test_password_without_lowercase_fails(self):
        with pytest.raises(ValueError, match="lowercase"):
            account_schema.UserCreate(
                first_name="Test",
                last_name="User",
                email="test@example.com",
                country="NG",
                password="NOLOWERCASE123!"
            )

    def test_password_without_digit_fails(self):
        with pytest.raises(ValueError, match="digit"):
            account_schema.UserCreate(
                first_name="Test",
                last_name="User",
                email="test@example.com",
                country="NG",
                password="NoDigitsHere!"
            )

    def test_password_too_short_fails(self):
        with pytest.raises(ValueError):
            account_schema.UserCreate(
                first_name="Test",
                last_name="User",
                email="test@example.com",
                country="NG",
                password="Ab1!"
            )

    def test_valid_password_passes(self):
        user = account_schema.UserCreate(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            country="NG",
            password="CrystalLake55!"
        )
        assert user.password == "CrystalLake55!"


class TestNameValidation:
    
    def test_name_with_numbers_fails(self):
        with pytest.raises(ValueError, match="letters"):
            account_schema.UserCreate(
                first_name="Test123",
                last_name="User",
                email="test@example.com",
                country="NG",
                password="ForestPath2025!"
            )

    def test_name_with_special_chars_fails(self):
        with pytest.raises(ValueError, match="letters"):
            account_schema.UserCreate(
                first_name="Test@Name",
                last_name="User",
                email="test@example.com",
                country="NG",
                password="DesertWind33!"
            )

    def test_hyphenated_name_passes(self):
        user = account_schema.UserCreate(
            first_name="Mary-Jane",
            last_name="OBrien",
            email="test@example.com",
            country="NG",
            password="StarlightDream44!"
        )
        assert "Mary-Jane" in user.first_name

    def test_name_with_spaces_passes(self):
        user = account_schema.UserCreate(
            first_name="Mary Jane",
            last_name="Van Der Berg",
            email="test@example.com",
            country="NG",
            password="TwilightGarden66!"
        )
        assert user.first_name == "Mary Jane"


class TestEmailValidation:
    
    def test_invalid_email_format_fails(self):
        with pytest.raises(ValueError):
            account_schema.UserCreate(
                first_name="Test",
                last_name="User",
                email="not-an-email",
                country="NG",
                password="MoonlitPath77!"
            )

    def test_email_without_domain_fails(self):
        with pytest.raises(ValueError):
            account_schema.UserCreate(
                first_name="Test",
                last_name="User",
                email="test@",
                country="NG",
                password="NorthernLights88!"
            )

    def test_valid_email_passes(self):
        user = account_schema.UserCreate(
            first_name="Test",
            last_name="User",
            email="valid.email@example.com",
            country="NG",
            password="SouthernWaves99!"
        )
        assert user.email == "valid.email@example.com"


class TestLogin:
    
    @pytest.mark.asyncio
    async def test_login_with_correct_credentials_succeeds(self, db_session, test_user):
        result = await AuthService.login_user(
            db_session, 
            test_user.email, 
            "MorningCoffee42!"
        )
        
        assert result is not None
        assert "access_token" in result or "pre_auth_token" in result

    @pytest.mark.asyncio
    async def test_login_with_wrong_password_fails(self, db_session, test_user):
        with pytest.raises(es.InvalidCredentialsError):
            await AuthService.login_user(
                db_session, 
                test_user.email, 
                "TotallyWrongGuess99!"
            )

    @pytest.mark.asyncio
    async def test_login_with_nonexistent_email_fails(self, db_session):
        with pytest.raises(es.UserNotFoundError):
            await AuthService.login_user(
                db_session, 
                "nonexistent@example.com", 
                "SpringShowers2026!"
            )

    @pytest.mark.asyncio
    async def test_login_with_empty_password_fails(self, db_session, test_user):
        with pytest.raises(es.InvalidCredentialsError):
            await AuthService.login_user(
                db_session, 
                test_user.email, 
                ""
            )

    @pytest.mark.asyncio
    async def test_login_inactive_user_fails(self, db_session):
        hashed_password = oauth2.get_password_hash("WinterFrost2025!")
        inactive_user = account.User(
            id=uuid.uuid4(),
            first_name="Inactive",
            last_name="User",
            email="inactive@example.com",
            status="VERIFIED",
            password=hashed_password,
            country="NG",
            tier=UserTier.FREE,
            is_active=False,
            is_admin=False,
            is_2fa_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(inactive_user)
        await db_session.commit()
        
        with pytest.raises(es.PermissionDeniedError):
            await AuthService.login_user(
                db_session,
                "inactive@example.com",
                "WinterFrost2025!"
            )


class TestTokenGeneration:
    
    def test_access_token_generation(self):
        user_id = str(uuid.uuid4())
        token = oauth2.create_access_token(user_id)
        
        assert token is not None
        assert len(token) > 0

    @pytest.mark.skip(reason="create_refresh_token is async and requires db session")
    def test_refresh_token_generation(self):
        pass

    def test_token_verification_valid_token(self):
        user_id = str(uuid.uuid4())
        token = oauth2.create_access_token(user_id)
        
        payload = oauth2.verify_access_token(token, es.InvalidCredentialsError("Invalid"))
        
        assert payload is not None
        assert payload.id == user_id

    def test_token_verification_invalid_token_raises(self):
        with pytest.raises(es.InvalidCredentialsError):
            oauth2.verify_access_token("invalid.token.here", es.InvalidCredentialsError("Invalid"))

    @pytest.mark.skip(reason="Mocking settings for expired token is complex")
    def test_token_verification_expired_token_raises(self):
        pass


class TestPasswordHashing:
    
    def test_password_hash_is_different_from_plain(self):
        plain = "SummerBreeze2024!"
        hashed = oauth2.get_password_hash(plain)
        
        assert hashed != plain
        assert len(hashed) > len(plain)

    def test_same_password_produces_different_hashes(self):
        plain = "AutumnLeaves2025!"
        hash1 = oauth2.get_password_hash(plain)
        hash2 = oauth2.get_password_hash(plain)
        
        assert hash1 != hash2

    def test_verify_correct_password(self):
        plain = "SpringBlossom2026!"
        hashed = oauth2.get_password_hash(plain)
        
        assert oauth2.verify_password(plain, hashed) == True

    def test_verify_wrong_password(self):
        plain = "WinterSnow2025!"
        wrong = "CompletelyDifferent99!"
        hashed = oauth2.get_password_hash(plain)
        
        assert oauth2.verify_password(wrong, hashed) == False


class TestTierUpgrade:
    
    @pytest.mark.asyncio
    async def test_upgrade_free_to_plus(self, db_session, test_user, system_accounts):
        assert test_user.tier == UserTier.FREE
        
        upgraded_user = await RegistrationService.upgrade_to_plus(db_session, test_user.id)
        await db_session.commit()
        
        assert upgraded_user.tier == UserTier.PLUS
        
        result = await db_session.execute(
            select(LedgerAccount).filter(
                LedgerAccount.owner_id == test_user.id,
                LedgerAccount.type == AccountType.USER_LIVE_WALLET
            )
        )
        live_wallet = result.scalar_one_or_none()
        
        assert live_wallet is not None
        assert live_wallet.is_active == False

    @pytest.mark.asyncio
    async def test_upgrade_plus_to_business(self, db_session, plus_user, system_accounts):
        assert plus_user.tier == UserTier.PLUS
        
        upgraded_user = await RegistrationService.upgrade_to_business(db_session, plus_user.id)
        await db_session.commit()
        
        assert upgraded_user.tier == UserTier.BUSINESS

    @pytest.mark.asyncio
    async def test_upgrade_already_plus_fails(self, db_session, plus_user, system_accounts):
        with pytest.raises(es.InvalidRequestError, match="already on Plus"):
            await RegistrationService.upgrade_to_plus(db_session, plus_user.id)

    @pytest.mark.asyncio
    async def test_upgrade_already_business_fails(self, db_session, system_accounts):
        hashed_password = oauth2.get_password_hash("TopExecutive2025!")
        business_user = account.User(
            id=uuid.uuid4(),
            first_name="Business",
            last_name="User",
            email="bizuser@example.com",
            status="VERIFIED",
            password=hashed_password,
            country="NG",
            tier=UserTier.BUSINESS,
            is_active=True,
            is_admin=False,
            is_2fa_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(business_user)
        await db_session.commit()
        
        with pytest.raises(es.InvalidRequestError, match="already on Business"):
            await RegistrationService.upgrade_to_business(db_session, business_user.id)

    @pytest.mark.asyncio
    async def test_upgrade_nonexistent_user_fails(self, db_session, system_accounts):
        fake_user_id = uuid.uuid4()
        
        with pytest.raises(es.UserNotFoundError):
            await RegistrationService.upgrade_to_plus(db_session, fake_user_id)


class TestTierDowngrade:
    
    @pytest.mark.asyncio
    async def test_downgrade_plus_to_free(self, db_session, plus_user, system_accounts):
        live_wallet = LedgerAccount(
            id=uuid.uuid4(),
            owner_id=plus_user.id,
            type=AccountType.USER_LIVE_WALLET,
            name="Plus User Live",
            currency="USD",
            balance=Decimal("1000"),
            is_active=True,
            is_system=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(live_wallet)
        await db_session.commit()
        
        downgraded_user = await RegistrationService.downgrade_to_free(db_session, plus_user.id)
        await db_session.commit()
        
        assert downgraded_user.tier == UserTier.FREE
        
        await db_session.refresh(live_wallet)
        assert live_wallet.is_active == False

    @pytest.mark.asyncio
    async def test_downgrade_nonexistent_user_fails(self, db_session):
        fake_user_id = uuid.uuid4()
        
        with pytest.raises(es.UserNotFoundError):
            await RegistrationService.downgrade_to_free(db_session, fake_user_id)


class TestEnsureDemoWallet:
    
    @pytest.mark.asyncio
    async def test_ensure_demo_wallet_creates_if_missing(self, db_session, test_user, system_accounts):
        wallet = await RegistrationService.ensure_demo_wallet(db_session, test_user.id)
        await db_session.commit()
        
        assert wallet is not None
        assert wallet.type == AccountType.USER_DEMO_WALLET
        assert wallet.balance == Decimal("10000")

    @pytest.mark.asyncio
    async def test_ensure_demo_wallet_returns_existing(self, db_session, test_user, system_accounts):
        existing_wallet = LedgerAccount(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            type=AccountType.USER_DEMO_WALLET,
            name="Existing Demo",
            currency="USD",
            balance=Decimal("5000"),
            is_active=True,
            is_system=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(existing_wallet)
        await db_session.commit()
        
        wallet = await RegistrationService.ensure_demo_wallet(db_session, test_user.id)
        
        assert wallet.id == existing_wallet.id
        assert wallet.balance == Decimal("5000")

    @pytest.mark.asyncio
    async def test_ensure_demo_wallet_nonexistent_user_fails(self, db_session, system_accounts):
        fake_user_id = uuid.uuid4()
        
        with pytest.raises(es.UserNotFoundError):
            await RegistrationService.ensure_demo_wallet(db_session, fake_user_id)
