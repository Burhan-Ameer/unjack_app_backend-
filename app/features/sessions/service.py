import logging

from app.features.sessions.repository import SessionRepository
from app.features.sessions.models import AppSession
from app.schemas.session import SessionCreate, SessionResponse

logger = logging.getLogger("app.sessions.service")

class SessionService:
    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo

    async def log_session(self, user_id: int, session: SessionCreate) -> AppSession:
        db_session = AppSession(user_id=user_id, **session.model_dump())
        logger.debug("Persisting session user_id=%s app_name=%s", user_id, session.app_name)
        return await self.session_repo.create(db_session)

    async def get_session_history(self, user_id: int) -> list[SessionResponse]:
        sessions = await self.session_repo.get_sessions_by_user(user_id)
        logger.debug("Transforming session history user_id=%s count=%s", user_id, len(sessions))
        return [SessionResponse.from_orm(s) for s in sessions]