from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TwoFactorRequest(BaseModel):
    code: str
    pre_auth_token: str


class TwoFactorConfirmRequest(BaseModel):
    code: str
    secret: str


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code_uri: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
