import pytest
from unittest.mock import AsyncMock, patch

from application.utilities.config import settings
from application.services.paystack_service import PaystackService
from application.utilities.exceptions import DepositError


class TestPaymentRouter:

    @pytest.mark.asyncio
    async def test_get_pricing_success(self, client, test_user, auth_headers):
        response = await client.get("/api/v1/payments/pricing")

        assert response.status_code == 200
        assert 'exchange_rate' in response.json()
        assert 'plus' in response.json()
        assert 'business' in response.json()

    @pytest.mark.asyncio
    async def test_initiate_plus_tier_upgrade_success(self, client, test_user, auth_headers, db_session):
        expected_price = settings.PLUS_TIER_PRICE_USD
        response = await client.post("/api/v1/payments/upgrade/plus", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["amount_usd"] == expected_price
        data = response.json()
        assert 'reference' in data and data['reference'] != ''
        assert 'authorization_url' in data and data['authorization_url'] != ''

    @pytest.mark.asyncio
    async def test_initiate_business_tier_upgrade_success(self, client, test_user, auth_headers, db_session):
        expected_price = settings.BUSINESS_TIER_PRICE_USD
        response = await client.post("/api/v1/payments/upgrade/business", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["amount_usd"] == expected_price
        data = response.json()
        assert 'reference' in data and data['reference'] != ''
        assert 'authorization_url' in data and data['authorization_url'] != ''

    @pytest.mark.asyncio
    async def test_initiate_tier_upgrade_invalid_tier(self, client, test_user, auth_headers, db_session):
        response = await client.post("/api/v1/payments/upgrade/invalid_tier", headers=auth_headers)
        assert response.status_code == 400
        assert "Tier must be 'plus' or 'business'" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_initiate_tier_upgrade_unauthorized(self, client):
        response = await client.post("/api/v1/payments/upgrade/plus")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_payment_success(self, client, test_user, auth_headers, db_session):
        demo_payment = await PaystackService.initialize_tier_payment(
            db=db_session,
            user_id=test_user.id,
            email=test_user.email,
            tier="plus"
        )
        reference = demo_payment["reference"]

        with patch.object(
            PaystackService,
            "verify_transaction",
            new_callable=AsyncMock,
            return_value={
                "status": "success",
                "amount": 500000,  # 5000.00 Naira in kobo
                "gateway_response": "Successful"
            }
        ) as mock_verify:
            response = await client.get(
                f"/api/v1/payments/verify/{reference}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["reference"] == reference
            assert data["amount"] == 5000.00
            mock_verify.assert_called_once_with(reference)

    @pytest.mark.asyncio
    async def test_verify_payment_failure(self, client, auth_headers):
        fake_reference = "invalid_ref_123_hehe"

        with patch.object(
            PaystackService,
            "verify_transaction",
            new_callable=AsyncMock,
            side_effect=DepositError(reason="Verification failed: Invalid transaction")
        ):
            response = await client.get(
                f"/api/v1/payments/verify/{fake_reference}",
                headers=auth_headers
            )

            assert response.status_code == 400
            assert "Verification failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_payment_unauthorized(self, client):
        response = await client.get("/api/v1/payments/verify/some_reference")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_banks_success(self, client):
        with patch.object(
            PaystackService,
            "get_banks",
            new_callable=AsyncMock,
            return_value=[
                {"name": "Access Bank", "code": "044"},
                {"name": "GTBank", "code": "058"},
            ]
        ) as mock_banks:
            response = await client.get("/api/v1/payments/banks")

            assert response.status_code == 200
            data = response.json()
            assert "banks" in data
            assert len(data["banks"]) == 2
            mock_banks.assert_called_once()
