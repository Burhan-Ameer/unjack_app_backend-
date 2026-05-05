from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None

class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    joined_at: datetime

    class Config:
        from_attributes = True

class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    highest_streak: int
    top_user_id: Optional[int] = None
    members: List[GroupMemberResponse] = []

    class Config:
        from_attributes = True

class GroupMemberAdd(BaseModel):
    user_id: int
