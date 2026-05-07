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
    """
    Schema representing a user's membership in a Group.
    """
    id: int
    user_id: int
    joined_at: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to read from ORM models

class GroupResponse(GroupBase):
    """
    Schema for a full Group response, including its statistics and current members.
    """
    id: int
    created_at: datetime
    highest_streak: int
    top_user_id: Optional[int] = None
    members: List[GroupMemberResponse] = []

    class Config:
        from_attributes = True

class GroupMemberAdd(BaseModel):
    """
    Schema for adding a new user to a Group.
    """
    user_id: int
