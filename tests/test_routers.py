import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch, AsyncMock

from application.models import account
from application.models.ledger import Account as LedgerAccount
from application.models.enums import AccountType, UserTier
from application.utilities import oauth2


class TestAuthRouterRegistration:
    
    @pytest.mark.asyncio
    async def test_register_endpoint_success(self, client, system_accounts, mock_send_email):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": f"new{uuid.uuid4().hex[:6]}@example.com",
                "country": "NG",
                "password": "SunnyMorning2024!"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["tier"] == "free"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, client, test_user, system_accounts, mock_send_email):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Duplicate",
                "last_name": "User",
                "email": test_user.email,
                "country": "NG",
                "password": "CloudyAfternoon55!"
            }
        )
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_password_returns_422(self, client, system_accounts):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "country": "NG",
                "password": "weak"
            }
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email_returns_422(self, client, system_accounts):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "not-an-email",
                "country": "NG",
                "password": "RainyEvening77!"
            }
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_required_field_returns_422(self, client, system_accounts):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Test",
                "email": "test@example.com",
                "password": "WindyNight2025!"
            }
        )
        
        assert response.status_code == 422


class TestAuthRouterLogin:
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "MorningCoffee42!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "pre_auth_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client, test_user):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "CompletelyWrongGuess88!"
            }
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_returns_401(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "RandomPassword2026!"
            }
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_password_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com"
            }
        )
        
        assert response.status_code == 422


class TestUsersRouterMe:
    
    @pytest.mark.asyncio
    async def test_get_me_success(self, client, test_user, auth_headers):
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["tier"] == "free"

    @pytest.mark.asyncio
    async def test_get_me_no_auth_returns_401(self, client):
        response = await client.get("/api/v1/users/me")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token_returns_401(self, client):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401


class TestUsersRouterUpdate:
    
    @pytest.mark.asyncio
    async def test_update_me_success(self, client, test_user, auth_headers):
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"first_name": "UpdatedName"}
        )
        
        assert response.status_code == 200
        assert response.json()["first_name"] == "UpdatedName"

    @pytest.mark.asyncio
    async def test_update_me_invalid_name_returns_422(self, client, test_user, auth_headers):
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"first_name": "Invalid123"}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_me_no_auth_returns_401(self, client):
        response = await client.put(
            "/api/v1/users/me",
            json={"first_name": "Test"}
        )
        
        assert response.status_code == 401


class TestUsersRouterTierUpgrade:
    
    @pytest.mark.asyncio
    async def test_upgrade_to_plus_success(self, client, test_user, auth_headers, system_accounts):
        response = await client.post(
            "/api/v1/users/me/upgrade/plus",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["tier"] == "plus"

    @pytest.mark.asyncio
    async def test_upgrade_already_plus_returns_400(self, client, plus_user, system_accounts):
        token = oauth2.create_access_token(data={"sub": str(plus_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            "/api/v1/users/me/upgrade/plus",
            headers=headers
        )
        
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upgrade_to_business_success(self, client, test_user, auth_headers, system_accounts):
        response = await client.post(
            "/api/v1/users/me/upgrade/business",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["tier"] == "business"

    @pytest.mark.asyncio
    async def test_downgrade_to_free_success(self, client, plus_user, system_accounts):
        token = oauth2.create_access_token(data={"sub": str(plus_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            "/api/v1/users/me/downgrade/free",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["tier"] == "free"


class TestVirtualWalletRouter:
    
    @pytest.mark.asyncio
    async def test_get_virtual_wallet_status(self, client, test_user_with_demo_wallet, auth_headers):
        response = await client.get(
            "/api/v1/wallet/virtual/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "current_balance" in data
        assert "is_blown" in data
        assert "free_reset_available" in data

    @pytest.mark.asyncio
    async def test_free_reset_success(self, client, test_user_with_demo_wallet, auth_headers, system_accounts):
        response = await client.post(
            "/api/v1/wallet/virtual/reset/free",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["reset_type"] == "free"
        assert Decimal(str(data["new_balance"])) == Decimal("10000")

    @pytest.mark.asyncio
    async def test_paid_reset_success(self, client, test_user_with_demo_wallet, auth_headers, system_accounts):
        response = await client.post(
            "/api/v1/wallet/virtual/reset/paid",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["reset_type"] == "paid"


class TestUsersRouterPasswordChange:
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, client, test_user, auth_headers):
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=auth_headers,
            json={
                "old_password": "MorningCoffee42!",
                "new_password": "EveningTea2025#",
                "confirm_password": "EveningTea2025#"
            }
        )
        
        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password_returns_401(self, client, test_user, auth_headers):
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=auth_headers,
            json={
                "old_password": "TotallyWrongOld99!",
                "new_password": "BrandNewSecret2026!",
                "confirm_password": "BrandNewSecret2026!"
            }
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_mismatch_returns_400(self, client, test_user, auth_headers):
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=auth_headers,
            json={
                "old_password": "MorningCoffee42!",
                "new_password": "FirstNewPassword77!",
                "confirm_password": "DifferentSecondOne88!"
            }
        )
        
        assert response.status_code == 400


class TestUsersRouterDelete:
    
    @pytest.mark.asyncio
    async def test_delete_account_success(self, client, test_user, auth_headers):
        response = await client.delete(
            "/api/v1/users/me",
            headers=auth_headers
        )
        
        assert response.status_code == 204


class TestErrorResponses:
    
    @pytest.mark.asyncio
    async def test_404_for_unknown_endpoint(self, client):
        response = await client.get("/api/v1/unknown/endpoint")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, client):
        response = await client.delete("/api/v1/auth/register")
        
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_invalid_json_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestRateLimiting:
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Rate limiting requires real redis connection")
    async def test_rate_limit_on_login(self, client):
        for _ in range(10):
            await client.post(
                "/api/v1/auth/login",
                data={
                    "username": "test@example.com",
                    "password": "wrong"
                }
            )
        
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrong"
            }
        )
        
        assert response.status_code == 429


class TestCORSHeaders:
    
    @pytest.mark.asyncio
    async def test_cors_preflight(self, client):
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        assert response.status_code in [200, 204]


class TestHealthCheck:
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
