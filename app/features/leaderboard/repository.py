from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import datetime, date
from typing import Sequence, Tuple
from app.features.leaderboard.models import Streak, WeeklyStat
from app.features.groups.models import GroupMember
from app.features.sessions.models import AppSession
from app.features.auth.models import User

class LeaderboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_streak_by_user(self, user_id: int) -> Streak | None:
        result = await self.db.execute(select(Streak).where(Streak.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_streak(self, streak: Streak) -> Streak:
        self.db.add(streak)
        await self.db.commit()
        await self.db.refresh(streak)
        return streak

    async def update_streak(self, streak: Streak) -> Streak:
        await self.db.commit()
        await self.db.refresh(streak)
        return streak

    async def get_group_focus_times(self, group_id: int, week_start: datetime, week_end: datetime) -> Sequence[Tuple[User, int]]:
        stmt = (
            select(
                User,
                func.coalesce(func.sum(AppSession.duration), 0).label('total_time')
            )
            .select_from(GroupMember)
            .join(User, User.id == GroupMember.user_id)
            .outerjoin(
                AppSession, 
                and_(
                    AppSession.user_id == User.id,
                    AppSession.blocked_date >= week_start,
                    AppSession.blocked_date < week_end
                )
            )
            .where(GroupMember.group_id == group_id)
            .group_by(User.id)
            .order_by(desc('total_time'))
        )
        
        result = await self.db.execute(stmt)
        return result.all()

    async def upsert_weekly_stat(self, group_id: int, user_id: int, week_start: date, total_time: int, rank: int) -> WeeklyStat:
        stmt = select(WeeklyStat).where(
            and_(
                WeeklyStat.group_id == group_id,
                WeeklyStat.user_id == user_id,
                WeeklyStat.week_start == week_start
            )
        )
        result = await self.db.execute(stmt)
        weekly_stat = result.scalar_one_or_none()
        
        if weekly_stat:
            weekly_stat.total_time = total_time
            weekly_stat.rank = rank
        else:
            weekly_stat = WeeklyStat(
                group_id=group_id,
                user_id=user_id,
                week_start=week_start,
                total_time=total_time,
                rank=rank
            )
            self.db.add(weekly_stat)
            
        return weekly_stat

    async def get_all_groups(self):
        from app.features.groups.models import Group
        result = await self.db.execute(select(Group))
        return result.scalars().all()