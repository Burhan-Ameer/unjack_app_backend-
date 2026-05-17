from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.features.auth.repository import UserRepository
from app.features.auth.service import AuthService
from app.features.sessions.repository import SessionRepository
from app.features.sessions.service import SessionService
from app.features.leaderboard.repository import LeaderboardRepository
from app.features.leaderboard.service import LeaderboardService
from app.features.groups.repository import GroupRepository
from app.features.groups.service import GroupService
from app.features.notifications.service import NotificationService

# Repositories
def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_session_repository(db: AsyncSession = Depends(get_db)) -> SessionRepository:
    return SessionRepository(db)

def get_leaderboard_repository(db: AsyncSession = Depends(get_db)) -> LeaderboardRepository:
    return LeaderboardRepository(db)

def get_group_repository(db: AsyncSession = Depends(get_db)) -> GroupRepository:
    return GroupRepository(db)

# Services
def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)

def get_session_service(session_repo: SessionRepository = Depends(get_session_repository)) -> SessionService:
    return SessionService(session_repo)

def get_leaderboard_service(
    leaderboard_repo: LeaderboardRepository = Depends(get_leaderboard_repository),
    group_repo: GroupRepository = Depends(get_group_repository)
) -> LeaderboardService:
    return LeaderboardService(leaderboard_repo, group_repo)

def get_group_service(
    group_repo: GroupRepository = Depends(get_group_repository)
) -> GroupService:
    return GroupService(group_repo)

def get_notification_service() -> NotificationService:
    return NotificationService()