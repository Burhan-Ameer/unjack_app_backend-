import logging

from app.features.auth.repository import UserRepository
from app.features.auth.models import User
from app.features.auth.schemas import UserCreate, LoginRequest
from app.utils.hashing import verify_password, get_password_hash
from app.utils.jwt import create_access_token, create_refresh_token, verify_refresh_token
from datetime import datetime

logger = logging.getLogger("app.auth.service")

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, user: UserCreate) -> User:
        # Check if user exists
        existing = await self.user_repo.get_by_email(user.email) or await self.user_repo.get_by_username(user.username)
        if existing:
            logger.info("Duplicate registration attempt email=%s username=%s", user.email, user.username)
            raise ValueError("User already exists")
        hashed = get_password_hash(user.password)
        db_user = User(username=user.username, email=user.email, hashed_password=hashed, created_at=datetime.utcnow())
        logger.debug("Creating user record username=%s", user.username)
        return await self.user_repo.create(db_user)

    async def authenticate_user(self, login: LoginRequest) -> User | None:
        user = await self.user_repo.get_by_email(login.email)
        if not user or not verify_password(login.password, user.hashed_password):
            logger.info("Authentication failed email=%s", login.email)
            return None
        logger.debug("Authentication succeeded user_id=%s", user.id)
        return user

    async def create_user_tokens(self, user: User) -> dict:
        access_token = create_access_token(data={"sub": user.username})
        refresh_token = create_refresh_token(data={"sub": user.username})
        logger.debug("Generated tokens for user_id=%s", user.id)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def refresh_tokens(self, refresh_token: str) -> dict:
        # For now, refresh tokens are JWTs signed with the same secret.
        # We verify the token and re-issue a fresh pair.
        username = verify_refresh_token(refresh_token)
        user = await self.user_repo.get_by_username(username)
        if not user:
            logger.warning("Refresh rejected: user not found username=%s", username)
            raise ValueError("User not found")
        logger.info("Refresh success user_id=%s username=%s", user.id, user.username)
        return await self.create_user_tokens(user)
