from typing import Optional, List
import requests
from rich.console import Console
from rich.status import Status
from .config import API_BASE_URL, API_PREFIX, TOKEN_FILE


class JarsApiError(Exception):
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class JarsClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.api_url = f"{base_url}{API_PREFIX}"
        self._token: Optional[str] = None
    
    def _ensure_token_dir(self) -> None:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    def save_token(self, token: str) -> None:
        self._ensure_token_dir()
        TOKEN_FILE.write_text(token)
        self._token = token
    
    def load_token(self) -> Optional[str]:
        if self._token:
            return self._token
        if TOKEN_FILE.exists():
            self._token = TOKEN_FILE.read_text().strip()
            return self._token
        return None
    
    def clear_token(self) -> None:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
        self._token = None
    
    def _headers(self) -> dict:
        token = self.load_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def _get_spinner_text(self, method: str, path: str) -> str:
        if "login" in path: return "Authenticating..."
        if "register" in path: return "Creating account..."
        if "balance" in path: return "Checking wallet..."
        if "trader" in path: return "Loading trader data..."
        if "subs" in path: return "Fetching subscriptions..."
        return f"{method} {path}..."

    def _request(self, method: str, path: str, **kwargs) -> dict:
        console = Console()
        text = self._get_spinner_text(method, path)
        
        try:
            with console.status(f"[bold cyan]{text}[/]", spinner="dots"):
                url = f"{self.api_url}{path}"
                if method == "GET":
                    resp = requests.get(url, headers=self._headers(), timeout=10, **kwargs)
                elif method == "POST":
                    resp = requests.post(url, headers=self._headers(), timeout=30, **kwargs)
                elif method == "PUT":
                    resp = requests.put(url, headers=self._headers(), timeout=30, **kwargs)
                elif method == "DELETE":
                    resp = requests.delete(url, headers=self._headers(), timeout=30, **kwargs)
                
                if resp.status_code >= 400:
                    try:
                        error_data = resp.json()
                        detail = error_data.get("detail", "Unknown error")
                    except:
                        detail = resp.text or "Server refused connection"
                        
                    if resp.status_code == 401:
                        if "Incorrect username or password" in str(detail):
                            detail = "Incorrect email or password."
                        elif "Could not validate credentials" in str(detail):
                            detail = "Session expired. Please login again."
                    
                    raise JarsApiError(detail, resp.status_code)
                
                return resp.json()
                
        except requests.RequestException as e:
            if isinstance(e, requests.ConnectionError):
                raise JarsApiError("Could not connect to JARS server. Is it online?")
            raise JarsApiError(str(e))

    def _get(self, path: str, **kwargs) -> dict:
        return self._request("GET", path, **kwargs)
    
    def _post(self, path: str, **kwargs) -> dict:
        return self._request("POST", path, **kwargs)
    
    def _put(self, path: str, **kwargs) -> dict:
        return self._request("PUT", path, **kwargs)
    
    def _delete(self, path: str, **kwargs) -> dict:
        return self._request("DELETE", path, **kwargs)

    def login(self, email: str, password: str) -> dict:
        resp = requests.post(
            f"{self.api_url}/auth/login",
            data={"username": email, "password": password},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("access_token"):
            self.save_token(data["access_token"])
        return data
    
    def register(self, first_name: str, last_name: str, email: str, country: str, password: str) -> dict:
        return self._post("/auth/register", json={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "country": country,
            "password": password
        })
    
    def register_plus(self, first_name: str, last_name: str, email: str, country: str, password: str) -> dict:
        return self._post("/auth/register/plus", json={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "country": country,
            "password": password
        })
    
    def register_business(self, first_name: str, last_name: str, email: str, country: str, password: str, company_name: str = "") -> dict:
        return self._post("/auth/register/business", json={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "country": country,
            "password": password,
            "company_name": company_name
        })
    
    def logout(self) -> None:
        try:
            self._post("/auth/logout")
        except:
            pass
        self.clear_token()
    
    def logout_all(self) -> dict:
        result = self._post("/auth/logout-all")
        self.clear_token()
        return result
    
    def setup_2fa(self) -> dict:
        return self._post("/auth/2fa/setup")
    
    def verify_2fa(self, code: str, pre_auth_token: str) -> dict:
        resp = requests.post(
            f"{self.api_url}/auth/2fa/verify",
            json={"code": code, "pre_auth_token": pre_auth_token},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("access_token"):
            self.save_token(data["access_token"])
        return data
    
    def confirm_2fa(self, code: str) -> dict:
        return self._post("/auth/2fa/confirm", json={"code": code})
    
    def refresh_token(self, refresh_token: str) -> dict:
        resp = requests.post(
            f"{self.api_url}/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("access_token"):
            self.save_token(data["access_token"])
        return data
    
    def verify_email(self, token: str) -> dict:
        return self._post(f"/auth/verify-email?token={token}")
    
    def resend_verification(self, email: str) -> dict:
        return self._post(f"/auth/resend-verification?email={email}")
    
    def request_password_reset(self, email: str) -> dict:
        return self._post("/auth/password-reset/request", json={"email": email})
    
    def confirm_password_reset(self, token: str, new_password: str) -> dict:
        return self._post("/auth/password-reset/confirm", json={
            "token": token,
            "new_password": new_password
        })

    def get_me(self) -> dict:
        return self._get("/users/me")
    
    def get_me_full(self) -> dict:
        return self._get("/users/me/full")
    
    def refresh_user_data(self) -> dict:
        return self._get("/users/me/refresh")
    
    def update_me(self, data: dict) -> dict:
        return self._put("/users/me", json=data)
    
    def delete_me(self) -> dict:
        return self._delete("/users/me")
    
    def change_password(self, old_password: str, new_password: str, confirm_password: str) -> dict:
        return self._post("/users/me/change-password", json={
            "old_password": old_password,
            "new_password": new_password,
            "confirm_password": confirm_password
        })
    
    def get_activity(self) -> List[dict]:
        return self._get("/users/me/activity")
    
    def upgrade_plus(self) -> dict:
        return self._post("/users/me/upgrade/plus")
    
    def upgrade_business(self) -> dict:
        return self._post("/users/me/upgrade/business")
    
    def downgrade_free(self) -> dict:
        return self._post("/users/me/downgrade/free")
    
    def ensure_demo_wallet(self) -> dict:
        return self._post("/users/me/ensure-demo-wallet")

    def list_traders(self, skip: int = 0, limit: int = 50) -> List[dict]:
        return self._get(f"/traders?skip={skip}&limit={limit}")
    
    def get_trader(self, trader_id: str) -> dict:
        return self._get(f"/traders/{trader_id}")
    
    def get_my_trader_profile(self) -> dict:
        return self._get("/traders/me")
    
    def get_my_kyc(self) -> dict:
        return self._get("/traders/me/kyc")
    
    def submit_kyc(self, first_name: str, last_name: str, country: str, id_document_path: str, date_of_birth: str = None, past_trades: str = None) -> dict:
        url = f"{self.api_url}/traders/kyc/submit"
        
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "country": country
        }
        if date_of_birth:
            data["date_of_birth"] = date_of_birth
        if past_trades:
            data["past_trades"] = past_trades
            
        try:
            with open(id_document_path, "rb") as f:
                files = {"id_document": (id_document_path, f, "application/pdf")}
                
                from rich.console import Console
                console = Console()
                
                with console.status(f"[bold cyan]Uploading KYC documents...[/]", spinner="dots"):
                    headers = self._headers()
                    resp = requests.post(url, headers=headers, data=data, files=files, timeout=60)
                    
                    if resp.status_code >= 400:
                        try:
                            error_data = resp.json()
                            detail = error_data.get("detail", "Unknown error")
                        except:
                            detail = resp.text or "Server refused connection"
                        raise JarsApiError(detail, resp.status_code)
                        
                    return resp.json()
        except FileNotFoundError:
            raise JarsApiError(f"File not found: {id_document_path}")
    
    def apply_trader(self, alias: str, bio: str = "", performance_fee: float = 10.0) -> dict:
        return self._post("/traders/apply", json={
            "alias": alias,
            "bio": bio,
            "performance_fee_percentage": performance_fee
        })
    
    def update_trader_profile(self, data: dict) -> dict:
        return self._put("/traders/me", json=data)
    
    def delete_trader_profile(self) -> dict:
        return self._delete("/traders/me")
    
    def deactivate_trader(self) -> dict:
        return self._post("/traders/me/deactivate")
    
    def reactivate_trader(self) -> dict:
        return self._post("/traders/me/reactivate")
    
    def approve_kyc(self, trader_id: str) -> dict:
        return self._post(f"/traders/{trader_id}/kyc/approve")
    
    def reject_kyc(self, trader_id: str, reason: str) -> dict:
        return self._post(f"/traders/{trader_id}/kyc/reject", json={"reason": reason})
    
    def graduate_trader(self, trader_id: str) -> dict:
        return self._post(f"/traders/{trader_id}/graduate")
    
    def suspend_trader(self, trader_id: str) -> dict:
        return self._post(f"/traders/{trader_id}/suspend")

    def get_subscriptions(self, active_only: bool = True) -> List[dict]:
        return self._get(f"/subscriptions?active_only={str(active_only).lower()}")
    
    def get_subscribers(self, active_only: bool = True) -> List[dict]:
        return self._get(f"/subscriptions/as-trader?active_only={str(active_only).lower()}")
    
    def get_subscription(self, sub_id: str) -> dict:
        return self._get(f"/subscriptions/{sub_id}")
    
    def follow_trader(self, trader_id: str, allocation: float) -> dict:
        return self._post("/subscriptions/follow", json={
            "trader_id": trader_id,
            "allocation_amount": allocation
        })
    
    def unfollow_trader(self, sub_id: str) -> dict:
        return self._delete(f"/subscriptions/{sub_id}")
    
    def pause_subscription(self, sub_id: str, reason: str = "") -> dict:
        return self._post(f"/subscriptions/{sub_id}/pause", json={"reason": reason})
    
    def resume_subscription(self, sub_id: str) -> dict:
        return self._post(f"/subscriptions/{sub_id}/resume")
    
    def get_tier_info(self) -> dict:
        return self._get("/subscriptions/tier/info")

    def list_keys(self, exchange: Optional[str] = None) -> List[dict]:
        path = "/keys"
        if exchange:
            path += f"?exchange={exchange}"
        return self._get(path)
    
    def get_key(self, key_id: str) -> dict:
        return self._get(f"/keys/{key_id}")
    
    def add_key(self, exchange: str, api_key: str, secret: str, label: str = "") -> dict:
        return self._post("/keys", json={
            "exchange": exchange,
            "api_key": api_key,
            "api_secret": secret,
            "label": label
        })
    
    def update_key(self, key_id: str, data: dict) -> dict:
        return self._put(f"/keys/{key_id}", json=data)
    
    def delete_key(self, key_id: str) -> dict:
        return self._delete(f"/keys/{key_id}")
    
    def test_key(self, key_id: str) -> dict:
        return self._post(f"/keys/{key_id}/test")

    def get_balance(self) -> dict:
        return self._get("/wallet/balance")
    
    def get_wallet_summary(self) -> dict:
        return self._get("/wallet/summary")
    
    def get_transactions(self, limit: int = 50, offset: int = 0) -> List[dict]:
        return self._get(f"/wallet/transactions?limit={limit}&offset={offset}")
    
    def init_deposit(self, amount: float, currency: str = "NGN") -> dict:
        return self._post("/wallet/deposit/initialize", json={
            "amount": amount,
            "currency": currency
        })
    
    def verify_deposit(self, reference: str) -> dict:
        return self._get(f"/wallet/deposit/verify/{reference}")
    
    def get_banks(self) -> List[dict]:
        return self._get("/wallet/banks")

    def get_virtual_wallet_status(self) -> dict:
        return self._get("/wallet/virtual/status")
    
    def request_free_reset(self) -> dict:
        return self._post("/wallet/virtual/reset/free")
    
    def request_paid_reset(self) -> dict:
        return self._post("/wallet/virtual/reset/paid")

    def get_tier_pricing(self) -> dict:
        return self._get("/payments/pricing")
    
    def initiate_tier_upgrade(self, tier: str) -> dict:
        return self._post(f"/payments/upgrade/{tier}")
    
    def verify_payment(self, reference: str) -> dict:
        return self._get(f"/payments/verify/{reference}")
    
    def get_payment_banks(self) -> List[dict]:
        return self._get("/payments/banks")

    def join_waitlist(self, email: str) -> dict:
        return self._post("/waitlist", json={"email": email})

    def create_system_account(self) -> dict:
        return self._post("/admin/accounts/system")

    def health(self) -> dict:
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            resp.raise_for_status()
            return {"status": "online", "data": resp.json()}
        except requests.RequestException:
            return {"status": "offline", "data": None}


client = JarsClient()
__all__ = ["client", "JarsApiError"]
