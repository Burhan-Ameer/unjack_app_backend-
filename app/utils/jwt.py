import logging
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.session import get_db
from app.features.auth.models import User

logger = logging.getLogger("app.jwt")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def _credentials_exception(detail: str = "Could not validate credentials") -> HTTPException:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
    return credentials_exception


def verify_token(token: str, expected_type: str | None = None, allow_legacy: bool = False) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token missing subject claim")
            raise _credentials_exception()

        token_type = payload.get("type")
        if expected_type is not None:
            if token_type is None:
                if not allow_legacy:
                    raise _credentials_exception("Invalid token type")
                # Legacy tokens didn\'t include a type. Allow them, but try to
                # prevent access tokens being used as refresh tokens.
                if expected_type == "refresh":
                    exp = payload.get("exp")
                    if exp is None:
                        raise _credentials_exception()
                    try:
                        exp_ts = float(exp)
                    except (TypeError, ValueError):
                        raise _credentials_exception()
                    remaining_seconds = exp_ts - datetime.utcnow().timestamp()
                    # Refresh tokens should live much longer than access tokens.
                    if remaining_seconds <= (settings.access_token_expire_minutes * 60 * 2):
                        raise _credentials_exception("Invalid token type")
            elif token_type != expected_type:
                raise _credentials_exception("Invalid token type")

        return username
    except ExpiredSignatureError:
        logger.warning("Token expired")
        raise _credentials_exception("Token expired")
    except JWTError:
        logger.warning("Token verification failed")
        raise _credentials_exception()


def verify_access_token(token: str) -> str:
    # Allow legacy access tokens that predate the `type` claim.
    return verify_token(token, expected_type="access", allow_legacy=True)


def verify_refresh_token(token: str) -> str:
    # Allow legacy refresh tokens that predate the `type` claim.
    return verify_token(token, expected_type="refresh", allow_legacy=True)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    username = verify_access_token(token)
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning("Token user not found username=%s", username)
        raise HTTPException(status_code=404, detail="User not found")
    return user
