# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, update
# from app.features.leaderboard.models import Streak, WeeklyStat

# class LeaderboardRepository:
#     def __init__(self, db: AsyncSession):
#         self.db = db

#     async def get_streak_by_user(self, user_id: int) -> Streak | None:
#         result = await self.db.execute(select(Streak).where(Streak.user_id == user_id))
#         return result.scalar_one_or_none()

#     async def create_streak(self, streak: Streak) -> Streak:
#         self.db.add(streak)
#         await self.db.commit()
#         await self.db.refresh(streak)
#         return streak

#     async def update_streak(self, streak: Streak) -> Streak:
#         await self.db.commit()
#         await self.db.refresh(streak)
#         return streak

#     async def get_weekly_stats(self, limit: int = 10) -> list[WeeklyStat]:
#         result = await self.db.execute(
#             select(WeeklyStat).order_by(WeeklyStat.rank).limit(limit)
#         )
#         return result.scalars().all()