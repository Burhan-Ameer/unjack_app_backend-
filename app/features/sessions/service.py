import logging
import json
from datetime import datetime, timezone, timedelta
from redis.asyncio import Redis

from app.features.sessions.repository import SessionRepository
from app.features.sessions.models import AppSession
from app.features.sessions.schemas import SessionStart, SessionResponse
from app.features.leaderboard.repository import LeaderboardRepository
from app.features.leaderboard.models import Streak
from app.features.groups.repository import GroupRepository

logger = logging.getLogger("app.sessions.service")

class SessionService:
    def __init__(self, session_repo: SessionRepository, leaderboard_repo: LeaderboardRepository, group_repo: GroupRepository, redis: Redis):
        self.session_repo = session_repo
        self.leaderboard_repo = leaderboard_repo
        self.group_repo = group_repo
        self.redis = redis
        self.key_prefix = "active_session:"
        self.max_session_seconds = 4 * 60 * 60  # 4 Hours TTL

    async def start_session(self, user_id: int, session: SessionStart) -> dict:
        key = f"{self.key_prefix}{user_id}"
        
        # Optionally reject if a session is already active
        existing = await self.redis.get(key)
        if existing:
            raise ValueError("You already have an active focus session running")

        ttl = session.ttl_seconds if session.ttl_seconds is not None else self.max_session_seconds

        session_data = {
            "app_name": session.app_name,
            "package": session.package,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "ttl_seconds": ttl
        }

        await self.redis.set(key, json.dumps(session_data), ex=ttl)
        logger.info("Started active session for user_id=%s app_name=%s ttl=%s", user_id, session.app_name, ttl)
        return {"status": "started", "start_time": session_data["start_time"], "ttl_seconds": ttl}

    async def stop_session(self, user_id: int) -> AppSession:
        key = f"{self.key_prefix}{user_id}"
        
        # 1. Retrieve session data
        data = await self.redis.get(key)
        if not data:
            raise ValueError("No active focus session found or it has expired")

        if isinstance(data, bytes):
            data = data.decode("utf-8")
        session_data = json.loads(data)
        start_time = datetime.fromisoformat(session_data["start_time"])
        now = datetime.now(timezone.utc)
        
        # 2. Calculate duration
        duration = int((now - start_time).total_seconds())
        if duration < 10:
            # Delete active session to allow user to retry
            await self.redis.delete(key)
            raise ValueError("Focus session was too short (under 10 seconds). Logging skipped.")

        # 3. Create completed AppSession
        db_session = AppSession(
            user_id=user_id,
            app_name=session_data["app_name"],
            package=session_data["package"],
            duration=duration,
            blocked_date=now
        )
        
        saved_session = await self.session_repo.create(db_session)

        # 4. Retrieve the user's streak record
        streak = await self.leaderboard_repo.get_streak_by_user(user_id)
        is_new = False
        if not streak:
            streak = Streak(
                user_id=user_id,
                current_streak=0,
                longest_streak=0,
                total_focus_time=0,
                last_active=None
            )
            is_new = True

        # 5. Update total focus time
        streak.total_focus_time += duration

        # 6. Calculate streak updates based on last active date
        today = now.date()
        if streak.last_active is None:
            # First session ever
            streak.current_streak = 1
            streak.last_active = today
        elif today == streak.last_active:
            # Session on the same day, streak does not change
            pass
        elif today == streak.last_active + timedelta(days=1):
            # Session on the consecutive day, streak increments
            streak.current_streak += 1
            streak.last_active = today
        else:
            # Session after a gap, streak resets
            streak.current_streak = 1
            streak.last_active = today

        # 7. Update longest streak if necessary
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        # 8. Save or update the streak record
        if is_new:
            await self.leaderboard_repo.create_streak(streak)
        else:
            await self.leaderboard_repo.update_streak(streak)

        # 9. Update group highest_streak and top_user_id
        groups = await self.group_repo.get_groups_by_user(user_id)
        for group in groups:
            if streak.current_streak > group.highest_streak:
                await self.group_repo.update_group_streak(group.id, streak.current_streak, user_id)
        if groups:
            await self.group_repo.db.commit()

        # 10. Clean up Redis active session
        await self.redis.delete(key)
        
        logger.info("Session stopped and logged user_id=%s duration=%s seconds", user_id, duration)
        return saved_session

    async def get_session_history(self, user_id: int) -> list[SessionResponse]:
        sessions = await self.session_repo.get_sessions_by_user(user_id)
        logger.debug("Transforming session history user_id=%s count=%s", user_id, len(sessions))
        return [SessionResponse.model_validate(s) for s in sessions]