from app.features.friends.repository import FriendshipRepository
from app.features.auth.repository import UserRepository  # cross-feature
from app.features.friends.models import FriendshipStatus
from app.schemas.friends import FriendListItem, FriendRequestItem

class FriendsService:
    def __init__(self, friendship_repo: FriendshipRepository, user_repo: UserRepository):
        self.friendship_repo = friendship_repo
        self.user_repo = user_repo

    async def send_friend_request(self, requester_id: int, friend_id: int, friend_username: str) -> int:
        friend = await self.user_repo.get_by_id(friend_id)
        if not friend:
            raise ValueError("Friend user not found")
        if friend.username != friend_username:
            raise ValueError("friend_id and friend_username do not match")
        if friend.id == requester_id:
            raise ValueError("You cannot send a friend request to yourself")

        existing = await self.friendship_repo.get_friendship_between(requester_id, friend.id)
        if existing:
            raise ValueError("Friend request already exists")

        friendship = await self.friendship_repo.create_request(
            requester_id=requester_id,
            addressee_id=friend.id,
        )
        return friendship.id

    async def accept_friend_request(self, friendship_id: int, user_id: int) -> bool:
        friendship = await self.friendship_repo.get_by_id(friendship_id)
        if not friendship:
            return False
        if friendship.addressee_id != user_id:
            raise PermissionError("You can only accept requests sent to you")
        if friendship.status == FriendshipStatus.accepted:
            return True

        await self.friendship_repo.update_status(friendship, FriendshipStatus.accepted)
        return True

    async def get_friends(self, user_id: int) -> list[FriendListItem]:
        friends = await self.friendship_repo.get_accepted_friend_users(user_id)
        return [
            FriendListItem(user_id=friend_id, username=username, avatar_url=None)
            for friend_id, username in friends
        ]

    async def get_pending_requests(self, user_id: int) -> list[FriendRequestItem]:
        requests = await self.friendship_repo.get_pending_requests(user_id)
        return [
            FriendRequestItem(
                friendship_id=friendship_id,
                from_user=from_user,
                created_at=created_at,
            )
            for friendship_id, from_user, created_at in requests
        ]

    async def remove_friend(self, user_id: int, friend_id: int) -> bool:
        return await self.friendship_repo.remove_friendship_between(user_id, friend_id)