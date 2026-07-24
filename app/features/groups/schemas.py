from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List, Optional

class GroupBase(BaseModel):
    """
    Base schema containing common properties for a Group.
    """
    name: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name must be non-empty string')
        if len(v.strip()) < 2:
            raise ValueError('name must be at least 2 characters long')
        return v.strip()

class GroupCreate(GroupBase):
    """
    Schema for creating a new Group. Inherits 'name' from GroupBase.
    """
    pass

class GroupUpdate(BaseModel):
    """
    Schema for updating an existing Group. 
    All fields are optional to allow partial updates.
    """ 
    name: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('name must be non-empty string')
            if len(v.strip()) < 2:
                raise ValueError('name must be at least 2 characters long')
            return v.strip()
        return v

class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    joined_at: datetime

    model_config = {"from_attributes": True}

class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    highest_streak: int
    top_user_id: Optional[int] = None
    members: List[GroupMemberResponse] = []

    model_config = {"from_attributes": True}

class GroupMemberAdd(BaseModel):
    """
    Schema for adding a new user to a Group.
    """
    user_id: int
