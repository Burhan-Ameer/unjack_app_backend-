from pydantic import BaseModel
from typing import List

class FriendRequest(BaseModel):
    friend_username: str

class FriendResponse(BaseModel):
    id: int
    username: str
    email: str

class FriendshipResponse(BaseModel):
    id: int
    requester: FriendResponse
    addressee: FriendResponse
    status: str

class FriendsList(BaseModel):
    friends: List[FriendResponse]

class RequestsList(BaseModel):
    requests: List[FriendshipResponse]