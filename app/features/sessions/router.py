import logging

from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_session_service
from app.features.sessions.service import SessionService
from app.features.sessions.schemas import SessionCreate, SessionHistory
from app.utils.jwt import get_current_user

router = APIRouter()
logger = logging.getLogger("app.sessions.router")

@router.post("/")
async def create_session(session: SessionCreate, current_user = Depends(get_current_user), service: SessionService = Depends(get_session_service)):
    userId=current_user.id
    try:
        db_session = await service.log_session(current_user.id, session)
        logger.info("Session logged user_id=%s session_id=%s", userId, db_session.id)
        return {"session_id": db_session.id}
    except Exception:
        logger.exception("Failed to log session for user_id=%s",userId)
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("/history", response_model=SessionHistory)
async def session_history(current_user = Depends(get_current_user), service: SessionService = Depends(get_session_service)):
    try:
        sessions = await service.get_session_history(current_user.id)
        logger.info("Session history fetched user_id=%s count=%s", current_user.id, len(sessions))
        return SessionHistory(sessions=sessions)
    except Exception:
        logger.exception("Failed to fetch session history for user_id=%s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to fetch session history")