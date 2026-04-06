from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.features.friends.models import Friendship, FriendshipStatus

class FriendshipRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_friends_by_user(self, user_id: int) -> list[Friendship]:
        result = await self.db.execute(
            select(Friendship).where(
                (Friendship.requester_id == user_id) | (Friendship.addressee_id == user_id)
            )
        )
        return result.scalars().all()

    async def create_request(self, friendship: Friendship) -> Friendship:
        self.db.add(friendship)
        await self.db.commit()
        await self.db.refresh(friendship)
        return friendship

    async def update_status(self, friendship_id: int, status: FriendshipStatus) -> Friendship | None:
        result = await self.db.execute(
            select(Friendship).where(Friendship.id == friendship_id)
        )
        friendship = result.scalar_one_or_none()
        if friendship:
            friendship.status = status
            await self.db.commit()
            await self.db.refresh(friendship)
        return friendship