from app.features.friends.repository import FriendshipRepository
from app.features.auth.repository import UserRepository  # cross-feature
from app.features.friends.models import Friendship, FriendshipStatus
from app.features.auth.models import User
from app.schemas.friends import FriendRequest, FriendResponse, FriendshipResponse
from sqlalchemy import select, or_, and_

class FriendsService:
    def __init__(self, friendship_repo: FriendshipRepository, user_repo: UserRepository):
        self.friendship_repo = friendship_repo
        self.user_repo = user_repo

    async def send_friend_request(self, requester_id: int, friend_username: str) -> Friendship | None:
        friend = await self.user_repo.get_by_username(friend_username)
        if not friend:
            return None
        # Check if already exists - this should be in repo or service
        # For simplicity, assume repo has a method or check here
        friendships = await self.friendship_repo.get_friends_by_user(requester_id)
        for f in friendships:
            if (f.requester_id == requester_id and f.addressee_id == friend.id) or \
               (f.requester_id == friend.id and f.addressee_id == requester_id):
                return None
        friendship = Friendship(requester_id=requester_id, addressee_id=friend.id)
        return await self.friendship_repo.create_request(friendship)

    async def accept_friend_request(self, friendship_id: int, user_id: int) -> bool:
        # This should be in repo
        friendship = await self.friendship_repo.update_status(friendship_id, FriendshipStatus.accepted)
        return friendship is not None and friendship.addressee_id == user_id

    async def get_friends(self, user_id: int) -> list[FriendResponse]:
        # This is complex, needs join, perhaps add method to repo
        # Placeholder
        return []

    async def get_pending_requests(self, user_id: int) -> list[FriendshipResponse]:
        # Placeholder
        return []

    async def remove_friend(self, user_id: int, friend_id: int) -> bool:
        # Placeholder
        return False