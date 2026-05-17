from datetime import date, timedelta, datetime
from typing import Optional
from app.features.leaderboard.repository import LeaderboardRepository
from app.features.groups.repository import GroupRepository
from app.features.leaderboard.schemas import LeaderboardEntry, WeeklyLeaderboard, WinnerResponse

class LeaderboardService:
    def __init__(self, leaderboard_repo: LeaderboardRepository, group_repo: GroupRepository):
        self.leaderboard_repo = leaderboard_repo
        self.group_repo = group_repo

    async def get_weekly_leaderboard(self, group_id: int) -> WeeklyLeaderboard:
        today = date.today()
        week_start_date = today - timedelta(days=today.weekday())  # Monday
        
        week_start = datetime.combine(week_start_date, datetime.min.time())
        week_end = week_start + timedelta(days=7)

        group = await self.group_repo.get_group_by_id(group_id)
        if not group:
            raise ValueError("Group not found")

        user_times = await self.leaderboard_repo.get_group_focus_times(group_id, week_start, week_end)

        entries = []
        rank = 1
        for user, total_time in user_times:
            entries.append(
                LeaderboardEntry(
                    user_id=user.id,
                    username=user.username,
                    total_time=int(total_time),
                    rank=rank
                )
            )
            rank += 1

        return WeeklyLeaderboard(week_start=week_start_date, entries=entries)

    async def get_weekly_winner(self, group_id: int) -> WinnerResponse | None:
        try:
            leaderboard = await self.get_weekly_leaderboard(group_id)
        except ValueError:
            return None
            
        if leaderboard.entries:
            winner = leaderboard.entries[0]
            if winner.total_time > 0:
                return WinnerResponse(
                    user_id=winner.user_id,
                    username=winner.username,
                    total_time=winner.total_time,
                    week_start=leaderboard.week_start
                )
        return None