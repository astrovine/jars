import pytest
import pytest_asyncio
import uuid
import httpx
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from application.services.paystack_service import PaystackService
from application.utilities.config import settings
from application.utilities import exceptions as es


class TestPaystackHeaders:
    
    @pytest.mark.asyncio
    async def test_get_headers_contains_authorization(self):
        headers = PaystackService._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {settings.PAYSTACK_SECRET_KEY}"

    @pytest.mark.asyncio
    async def test_get_headers_contains_content_type(self):
        headers = PaystackService._get_headers()
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"


class TestInitializeTransaction:
    
    @pytest.mark.asyncio
    async def test_initialize_transaction_success(self, db_session, test_user, system_accounts):
        amount_naira = 500
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": "https://checkout.paystack.com/abc123",
                "access_code": "abc123",
                "reference": "dep_xyz_12345"
            }
        }
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock) as mock_create_deposit, \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            
            result = await PaystackService.initialize_transaction(
                db=db_session,
                user_id=test_user.id,
                email=test_user.email,
                amount_naira=amount_naira
            )
            
            assert "reference" in result
            assert "authorization_url" in result
            assert "access_code" in result
            mock_create_deposit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_initialize_transaction_below_minimum_fails(self, db_session, test_user, system_accounts):
        amount_naira = 50  # Below ₦100 minimum
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock) as mock_create_deposit:
            with pytest.raises(es.InvalidAmountError) as exc_info:
                await PaystackService.initialize_transaction(
                    db=db_session,
                    user_id=test_user.id,
                    email=test_user.email,
                    amount_naira=amount_naira
                )
            
            assert "Minimum deposit" in str(exc_info.value)
            mock_create_deposit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_initialize_transaction_exact_minimum_succeeds(self, db_session, test_user, system_accounts):
        amount_naira = 100  # Exactly ₦100 minimum
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "authorization_url": "https://checkout.paystack.com/min123",
                "access_code": "min123"
            }
        }
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            
            result = await PaystackService.initialize_transaction(
                db=db_session,
                user_id=test_user.id,
                email=test_user.email,
                amount_naira=amount_naira
            )
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_initialize_transaction_paystack_api_error(self, db_session, test_user, system_accounts):
        amount_naira = 500
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": False,
            "message": "Invalid API key"
        }
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            
            with pytest.raises(es.DepositError) as exc_info:
                await PaystackService.initialize_transaction(
                    db=db_session,
                    user_id=test_user.id,
                    email=test_user.email,
                    amount_naira=amount_naira
                )
            
            assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_initialize_transaction_network_error(self, db_session, test_user, system_accounts):
        amount_naira = 500
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.RequestError("Connection timeout")):
            
            with pytest.raises(es.ServiceUnavailableError):
                await PaystackService.initialize_transaction(
                    db=db_session,
                    user_id=test_user.id,
                    email=test_user.email,
                    amount_naira=amount_naira
                )

    @pytest.mark.asyncio
    async def test_initialize_transaction_generates_unique_reference(self, db_session, test_user, system_accounts):
        amount_naira = 500
        references = set()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": {"authorization_url": "url", "access_code": "code"}
        }
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            
            for _ in range(5):
                result = await PaystackService.initialize_transaction(
                    db=db_session,
                    user_id=test_user.id,
                    email=test_user.email,
                    amount_naira=amount_naira
                )
                references.add(result["reference"])
        
        assert len(references) == 5


class TestInitializeTierPayment:
    
    @pytest.mark.asyncio
    async def test_initialize_plus_tier_payment_success(self, db_session, test_user, system_accounts):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "authorization_url": "https://checkout.paystack.com/tierplus123",
                "access_code": "tierplus123"
            }
        }
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock), \
             patch("application.services.paystack_service.ExchangeRateConverter.convert_usd_to_ngn", new_callable=AsyncMock, return_value=(Decimal("75000"), Decimal("1500"))), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            
            result = await PaystackService.initialize_tier_payment(
                db=db_session,
                user_id=test_user.id,
                email=test_user.email,
                tier="plus"
            )
            
            assert "reference" in result
            assert "tier_plus" in result["reference"]
            assert "authorization_url" in result

    @pytest.mark.asyncio
    async def test_initialize_business_tier_payment_success(self, db_session, test_user, system_accounts):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "authorization_url": "https://checkout.paystack.com/tierbiz123",
                "access_code": "tierbiz123"
            }
        }
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock), \
             patch("application.services.paystack_service.ExchangeRateConverter.convert_usd_to_ngn", new_callable=AsyncMock, return_value=(Decimal("150000"), Decimal("1500"))), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            
            result = await PaystackService.initialize_tier_payment(
                db=db_session,
                user_id=test_user.id,
                email=test_user.email,
                tier="business"
            )
            
            assert "tier_business" in result["reference"]

    @pytest.mark.asyncio
    async def test_initialize_invalid_tier_fails(self, db_session, test_user, system_accounts):
        with pytest.raises(es.InvalidRequestError) as exc_info:
            await PaystackService.initialize_tier_payment(
                db=db_session,
                user_id=test_user.id,
                email=test_user.email,
                tier="premium"  # Invalid tier
            )
        
        assert "Unknown tier" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tier_payment_network_error(self, db_session, test_user, system_accounts):
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock), \
             patch("application.services.paystack_service.ExchangeRateConverter.convert_usd_to_ngn", new_callable=AsyncMock, return_value=(Decimal("75000"), Decimal("1500"))), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.RequestError("Network down")):
            
            with pytest.raises(es.ServiceUnavailableError):
                await PaystackService.initialize_tier_payment(
                    db=db_session,
                    user_id=test_user.id,
                    email=test_user.email,
                    tier="plus"
                )


class TestGetTierPricing:
    
    @pytest.mark.asyncio
    async def test_get_tier_pricing_returns_all_tiers(self, db_session):
        with patch("application.services.paystack_service.ExchangeRateConverter.get_current_rate", new_callable=AsyncMock, return_value=Decimal("1500")):
            
            result = await PaystackService.get_tier_pricing(db_session)
            
            assert "exchange_rate" in result
            assert "plus" in result
            assert "business" in result

    @pytest.mark.asyncio
    async def test_get_tier_pricing_contains_usd_and_ngn(self, db_session):
        with patch("application.services.paystack_service.ExchangeRateConverter.get_current_rate", new_callable=AsyncMock, return_value=Decimal("1500")):
            
            result = await PaystackService.get_tier_pricing(db_session)
            
            assert "price_usd" in result["plus"]
            assert "price_ngn" in result["plus"]
            assert "price_usd" in result["business"]
            assert "price_ngn" in result["business"]

    @pytest.mark.asyncio
    async def test_get_tier_pricing_calculates_ngn_correctly(self, db_session):
        rate = Decimal("1500")
        
        with patch("application.services.paystack_service.ExchangeRateConverter.get_current_rate", new_callable=AsyncMock, return_value=rate):
            
            result = await PaystackService.get_tier_pricing(db_session)
            
            plus_usd = result["plus"]["price_usd"]
            plus_ngn = result["plus"]["price_ngn"]
            
            assert plus_ngn == plus_usd * float(rate)


class TestVerifyTransaction:
    
    @pytest.mark.asyncio
    async def test_verify_transaction_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "status": "success",
                "reference": "dep_abc_12345",
                "amount": 5000000,  # 50,000 kobo = ₦50,000
                "gateway_response": "Successful"
            }
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await PaystackService.verify_transaction("dep_abc_12345")
            
            assert result["status"] == "success"
            assert result["amount"] == 5000000

    @pytest.mark.asyncio
    async def test_verify_transaction_failed_payment(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "status": "failed",
                "reference": "dep_abc_12345",
                "gateway_response": "Declined"
            }
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await PaystackService.verify_transaction("dep_abc_12345")
            
            assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_verify_transaction_invalid_reference(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": False,
            "message": "Transaction reference not found"
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(es.DepositError) as exc_info:
                await PaystackService.verify_transaction("invalid_ref_123")
            
            assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_transaction_network_error(self):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.RequestError("Timeout")):
            with pytest.raises(es.ServiceUnavailableError):
                await PaystackService.verify_transaction("dep_abc_12345")


class TestGetBanks:
    
    @pytest.mark.asyncio
    async def test_get_banks_success(self):
        mock_banks = [
            {"name": "Access Bank", "code": "044"},
            {"name": "Kuda Bank", "code": "058"},
            {"name": "First Bank", "code": "011"}
        ]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": mock_banks
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await PaystackService.get_banks()
            
            assert len(result) == 3
            assert result[0]["name"] == "Access Bank"

    @pytest.mark.asyncio
    async def test_get_banks_empty_list(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": []
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await PaystackService.get_banks()
            
            assert result == []

    @pytest.mark.asyncio
    async def test_get_banks_api_failure_returns_empty(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": False,
            "message": "API error"
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await PaystackService.get_banks()
            
            assert result == []

    @pytest.mark.asyncio
    async def test_get_banks_network_error_returns_empty(self):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.RequestError("Connection refused")):
            result = await PaystackService.get_banks()
            
            assert result == []


class TestReferenceFormat:
    
    @pytest.mark.asyncio
    async def test_deposit_reference_format(self, db_session, test_user, system_accounts):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": {"authorization_url": "url", "access_code": "code"}
        }
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            
            result = await PaystackService.initialize_transaction(
                db=db_session,
                user_id=test_user.id,
                email=test_user.email,
                amount_naira=500
            )
            
            reference = result["reference"]
            assert reference.startswith("dep_")
            assert test_user.id.hex[:8] in reference

    @pytest.mark.asyncio
    async def test_tier_reference_includes_tier_name(self, db_session, test_user, system_accounts):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": {"authorization_url": "url", "access_code": "code"}
        }
        
        with patch("application.services.paystack_service.LedgerService.create_pending_deposit", new_callable=AsyncMock), \
             patch("application.services.paystack_service.ExchangeRateConverter.convert_usd_to_ngn", new_callable=AsyncMock, return_value=(Decimal("75000"), Decimal("1500"))), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            
            result = await PaystackService.initialize_tier_payment(
                db=db_session,
                user_id=test_user.id,
                email=test_user.email,
                tier="plus"
            )
            
            reference = result["reference"]
            assert reference.startswith("tier_plus_")
