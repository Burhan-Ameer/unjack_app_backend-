from datetime import datetime

from pydantic import BaseModel

class FriendRequest(BaseModel):
    friend_id: int
    friend_username: str

class FriendRequestCreated(BaseModel):
    friendship_id: int

class FriendAcceptResponse(BaseModel):
    status: str = "accepted"

class FriendListItem(BaseModel):
    user_id: int
    username: str
    avatar_url: str | None = None

class FriendRequestItem(BaseModel):
    friendship_id: int
    from_user: str
    created_at: datetime