import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.features.auth.models import User

logger = logging.getLogger("app.auth.repository")

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            logger.exception("User create commit failed email=%s username=%s", user.email, user.username)
            raise
        await self.db.refresh(user)
        logger.debug("User persisted user_id=%s", user.id)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()