from fastapi import APIRouter
from app.features.auth.router import router as auth_router
from app.features.health.router import router as health_router
from app.features.sessions.router import router as sessions_router
from app.features.groups.router import router as groups_router
# from app.features.leaderboard.router import router as leaderboard_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
api_router.include_router(groups_router, prefix="/groups", tags=["groups"])
api_router.include_router(health_router, tags=["health"])
# api_router.include_router(leaderboard_router, prefix="/leaderboard", tags=["leaderboard"])