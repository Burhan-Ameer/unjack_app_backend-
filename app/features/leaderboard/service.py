from app.features.leaderboard.repository import LeaderboardRepository
from app.features.friends.repository import FriendshipRepository  # assuming cross-feature access
from app.schemas.leaderboard import LeaderboardEntry, WeeklyLeaderboard, WinnerResponse
from datetime import date, timedelta
from sqlalchemy import select, desc, or_, and_
from app.features.auth.models import User  # cross-feature
from app.features.friends.models import Friendship, FriendshipStatus

class LeaderboardService:
    def __init__(self, leaderboard_repo: LeaderboardRepository, friendship_repo: FriendshipRepository):
        self.leaderboard_repo = leaderboard_repo
        self.friendship_repo = friendship_repo

    async def get_weekly_leaderboard(self, user_id: int) -> WeeklyLeaderboard:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday

        # Get friends - this might need to be in friendship service
        friendships = await self.friendship_repo.get_friends_by_user(user_id)
        friend_ids = []
        for f in friendships:
            if f.status == FriendshipStatus.accepted:
                if f.requester_id == user_id:
                    friend_ids.append(f.addressee_id)
                else:
                    friend_ids.append(f.requester_id)
        friend_ids.append(user_id)  # include self

        # For now, simplified, assuming we have a way to get weekly stats with user info
        # In reality, might need a combined query or service method
        # Placeholder
        return WeeklyLeaderboard(week_start=week_start, entries=[])

    async def get_weekly_winner(self, user_id: int) -> WinnerResponse | None:
        leaderboard = await self.get_weekly_leaderboard(user_id)
        if leaderboard.entries:
            winner = leaderboard.entries[0]
            return WinnerResponse(
                user_id=winner.user_id,
                username=winner.username,
                total_time=winner.total_time,
                week_start=leaderboard.week_start
            )
        return None