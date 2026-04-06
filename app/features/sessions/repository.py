import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.features.sessions.models import AppSession

logger = logging.getLogger("app.sessions.repository")

class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_sessions_by_user(self, user_id: int) -> list[AppSession]:
        result = await self.db.execute(select(AppSession).where(AppSession.user_id == user_id))
        return result.scalars().all()

    async def create(self, session: AppSession) -> AppSession:
        self.db.add(session)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            logger.exception("Session create commit failed user_id=%s", session.user_id)
            raise
        await self.db.refresh(session)
        logger.debug("Session persisted session_id=%s", session.id)
        return session