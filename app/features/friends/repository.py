from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, delete, or_, select

from app.features.auth.models import User
from app.features.friends.models import Friendship, FriendshipStatus

class FriendshipRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_friends_by_user(self, user_id: int) -> list[Friendship]:
        return await self.get_friendships_by_user(user_id)

    async def get_friendships_by_user(self, user_id: int) -> list[Friendship]:
        result = await self.db.execute(
            select(Friendship).where(
                (Friendship.requester_id == user_id) | (Friendship.addressee_id == user_id)
            )
        )
        return result.scalars().all()

    async def get_friendship_between(self, user_a_id: int, user_b_id: int) -> Friendship | None:
        result = await self.db.execute(
            select(Friendship).where(
                or_(
                    and_(
                        Friendship.requester_id == user_a_id,
                        Friendship.addressee_id == user_b_id,
                    ),
                    and_(
                        Friendship.requester_id == user_b_id,
                        Friendship.addressee_id == user_a_id,
                    ),
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_request(self, requester_id: int, addressee_id: int) -> Friendship:
        friendship = Friendship(requester_id=requester_id, addressee_id=addressee_id)
        self.db.add(friendship)
        await self.db.commit()
        await self.db.refresh(friendship)
        return friendship

    async def get_by_id(self, friendship_id: int) -> Friendship | None:
        result = await self.db.execute(
            select(Friendship).where(Friendship.id == friendship_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, friendship: Friendship, status: FriendshipStatus) -> Friendship:
        friendship.status = status
        await self.db.commit()
        await self.db.refresh(friendship)
        return friendship

    async def get_accepted_friend_users(self, user_id: int) -> list[tuple[int, str]]:
        result = await self.db.execute(
            select(User.id, User.username)
            .select_from(Friendship)
            .join(
                User,
                or_(
                    and_(
                        Friendship.requester_id == user_id,
                        Friendship.addressee_id == User.id,
                    ),
                    and_(
                        Friendship.addressee_id == user_id,
                        Friendship.requester_id == User.id,
                    ),
                ),
            )
            .where(Friendship.status == FriendshipStatus.accepted)
        )
        return result.all()

    async def get_pending_requests(self, user_id: int) -> list[tuple[int, str, object]]:
        result = await self.db.execute(
            select(Friendship.id, User.username, Friendship.created_at)
            .join(User, User.id == Friendship.requester_id)
            .where(
                Friendship.addressee_id == user_id,
                Friendship.status == FriendshipStatus.pending,
            )
            .order_by(Friendship.created_at.desc())
        )
        return result.all()

    async def remove_friendship_between(self, user_id: int, friend_id: int) -> bool:
        result = await self.db.execute(
            delete(Friendship).where(
                or_(
                    and_(
                        Friendship.requester_id == user_id,
                        Friendship.addressee_id == friend_id,
                    ),
                    and_(
                        Friendship.requester_id == friend_id,
                        Friendship.addressee_id == user_id,
                    ),
                )
            )
        )
        await self.db.commit()
        return result.rowcount > 0