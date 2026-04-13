import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.config import settings
from app.core.rate_limiter import RedisSlidingWindowRateLimiter
from app.dependencies import get_auth_service
from app.features.auth.service import AuthService
from app.schemas.auth import UserCreate, LoginRequest, Token

router = APIRouter()
logger = logging.getLogger("app.auth.router")
auth_rate_limiter = RedisSlidingWindowRateLimiter(
    redis_url=settings.redis_url,
    key_prefix=settings.rate_limit_key_prefix,
    max_requests=settings.auth_rate_limit_per_minute,
    window_seconds=settings.auth_rate_limit_window_seconds,
)

@router.post("/register")
async def register(
    user: UserCreate,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    await auth_rate_limiter.check(request)
    try:
        db_user = await service.register_user(user)
        logger.info("User registered username=%s user_id=%s", user.username, db_user.id)
        return {"user_id": db_user.id}
    except ValueError as e:
        logger.warning("Registration rejected username=%s reason=%s", user.username, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Unexpected registration error username=%s", user.username)
        raise HTTPException(status_code=500, detail="Failed to register user")

@router.post("/login", response_model=Token)
async def login(
    login: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    await auth_rate_limiter.check(request)
    try:
        user = await service.authenticate_user(login)
        if not user:
            logger.warning("Login failed email=%s", login.email)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        tokens = await service.create_user_tokens(user)
        logger.info("Login success user_id=%s username=%s", user.id, user.username)
        return tokens
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected login error email=%s", login.email)
        raise HTTPException(status_code=500, detail="Failed to process login")
