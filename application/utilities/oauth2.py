import base64
import secrets
import string
from datetime import datetime, timedelta, timezone
import jwt
from typing import Any, Union, Optional

from cryptography.fernet import Fernet
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from application.models import account
from application.utilities.config import settings
from application.schemas.token import TokenData as tk
from application.models.refresh_token import RefreshToken
import uuid
from fastapi import Request, Depends, HTTPException, status
from application.models.base import get_db
from application.utilities.audit import setup_logger

logger = setup_logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def encrypt_api_secret(secret: str) -> bytes:
    key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'\0'))
    f = Fernet(key)
    return f.encrypt(secret.encode())


def decrypt_api_secret(encrypted: bytes) -> str:
    key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'\0'))
    f = Fernet(key)
    return f.decrypt(encrypted).decode()


def create_pre_auth_token(subject: Union[str, any]) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode ={
        'exp': expiry,
        'sub': str(subject),
        'iat': datetime.now(timezone.utc),
        'iss': 'jars_app',
        'type': 'pre_auth'
    }
    encoded_jwt = jwt.encode(to_encode, settings.PRIVATE_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_pre_auth_token(token: str, credentials_exception) -> tk:
    try:
        payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "pre_auth":
            raise credentials_exception

        return tk(id=user_id)

    except jwt.PyJWTError:
        raise credentials_exception

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "iss": "jars_app"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.PRIVATE_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def create_refresh_token(subject: Union[str, Any], db: AsyncSession) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = uuid.uuid4()

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "jti": str(jti),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.PRIVATE_KEY,
        algorithm=settings.ALGORITHM
    )

    refresh_token_record = RefreshToken(
        jti=jti,
        user_id=uuid.UUID(str(subject)),
        token=encoded_jwt,
        expires_at=expire,
        is_revoked=False
    )
    db.add(refresh_token_record)
    await db.commit()
    await db.refresh(refresh_token_record)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = tk(id=user_id)
        return token_data

    except jwt.PyJWTError as e:
        raise credentials_exception
    except Exception as e:
        raise credentials_exception

async def verify_refresh_token(token: str, db: AsyncSession, credentials_exception):
    try:
        payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")

        if token_type != "refresh" or jti is None:
            raise credentials_exception

        result = await db.execute(
            select(RefreshToken).filter(
                RefreshToken.jti == uuid.UUID(jti),
                RefreshToken.user_id == uuid.UUID(user_id),
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise credentials_exception

        token_data = tk(id=user_id)
        return token_data

    except jwt.PyJWTError as e:
        raise credentials_exception
    except Exception as e:
        raise credentials_exception


async def revoke_refresh_token(token: str, db: AsyncSession) -> bool:
    try:
        result = await db.execute(
            select(RefreshToken).filter(RefreshToken.token == token)
        )
        token_record = result.scalar_one_or_none()
        if token_record:
            token_record.is_revoked = True
            await db.commit()
            return True
        return False
    except Exception:
        return False


async def revoke_all_user_tokens(user_id: uuid.UUID, db: AsyncSession) -> bool:
    try:
        result = await db.execute(
            select(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.is_revoked = True
        await db.commit()
        return True
    except Exception:
        return False

def get_token_from_request(
    request: Request,
    token_from_header: Optional[str] = Depends(oauth2_scheme)
) -> Optional[str]:
    token_from_cookie = request.cookies.get("access_token")
    if token_from_cookie:
        if token_from_cookie.startswith("Bearer "):
            return token_from_cookie.split(" ")[1]
        return token_from_cookie
    if token_from_header:
        return token_from_header
    return None


async def get_current_user(
    request: Request,
    token_from_header: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> account.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = get_token_from_request(request, token_from_header)

    if token is None:
        raise credentials_exception

    token_data = verify_access_token(token, credentials_exception)

    if token_data.id is None:
        raise credentials_exception

    result = await db.execute(
        select(account.User).filter(account.User.id == token_data.id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    request.state.user_id = str(user.id)

    return user

async def get_current_admin(current_user: account.User = Depends(get_current_user)) -> account.User:
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.id} ({current_user.email}) attempted superadmin only action.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: Requires superadmin privileges"
        )
    return current_user


def generate_random_password(length: int = 32) -> str:
    try:
        if length < 16:
            raise ValueError("Password length must be at least 16 characters")
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    except Exception as e:
        raise Exception(f"Failed to generate secure password: {str(e)}")
