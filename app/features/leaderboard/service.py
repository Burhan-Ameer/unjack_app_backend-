# from app.features.leaderboard.repository import LeaderboardRepository
# from app.features.groups.repository import GroupRepository
# from app.features.leaderboard.schemas import LeaderboardEntry, WeeklyLeaderboard, WinnerResponse
# from datetime import date, timedelta
# from typing import Optional
# from sqlalchemy import select, desc, or_, and_
# from app.features.auth.models import User
# from app.features.groups.models import Group, GroupMember

# class LeaderboardService:
#     def __init__(self, leaderboard_repo: LeaderboardRepository, group_repo: GroupRepository):
#         self.leaderboard_repo = leaderboard_repo
#         self.group_repo = group_repo

#     async def get_weekly_leaderboard(self, user_id: int, group_id: Optional[int] = None) -> WeeklyLeaderboard:
#         today = date.today()
#         week_start = today - timedelta(days=today.weekday())  # Monday

#         # Get users from the specific group, or just the user if no group
#         member_ids = [user_id]
#         if group_id:
#             group = self.group_repo.get_group_by_id(group_id)
#             if group:
#                 member_ids = [member.user_id for member in group.members]

#         # For now, simplified, assuming we have a way to get weekly stats with user info
#         # In reality, might need a combined query or service method
#         # Placeholder
#         return WeeklyLeaderboard(week_start=week_start, entries=[])

#     async def get_weekly_winner(self, user_id: int) -> WinnerResponse | None:
#         leaderboard = await self.get_weekly_leaderboard(user_id)
#         if leaderboard.entries:
#             winner = leaderboard.entries[0]
#             return WinnerResponse(  week_start = today - timedelta(days=today.weekday()),
#                 user_id=winner.user_id,
#                 username=winner.username,
#                 total_time=winner.total_time,
#                 week_start=leaderboard.week_start
#             )
#         return None