import logging

from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_session_service
from app.features.sessions.service import SessionService
from app.features.sessions.schemas import SessionStart, SessionHistory
from app.utils.jwt import get_current_user

router = APIRouter()
logger = logging.getLogger("app.sessions.router")

@router.post("/start")
async def start_session(
    session: SessionStart,
    current_user = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    userId = current_user.id
    try:
        res = await service.start_session(userId, session)
        return res
    except ValueError as e:
        logger.warning("Failed to start session for user_id=%s: %s", userId, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Error starting session for user_id=%s", userId)
        raise HTTPException(status_code=500, detail="Failed to start session")

@router.post("/stop")
async def stop_session(
    current_user = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    userId = current_user.id
    try:
        db_session = await service.stop_session(userId)
        logger.info("Session stopped and logged for user_id=%s session_id=%s", userId, db_session.id)
        return {"session_id": db_session.id, "duration": db_session.duration}
    except ValueError as e:
        logger.warning("Failed to stop session for user_id=%s: %s", userId, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Error stopping session for user_id=%s", userId)
        raise HTTPException(status_code=500, detail="Failed to stop session")

@router.get("/history", response_model=SessionHistory)
async def session_history(current_user = Depends(get_current_user), service: SessionService = Depends(get_session_service)):
    try:
        sessions = await service.get_session_history(current_user.id)
        logger.info("Session history fetched user_id=%s count=%s", current_user.id, len(sessions))
        return SessionHistory(sessions=sessions)
    except Exception:
        logger.exception("Failed to fetch session history for user_id=%s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to fetch session history")