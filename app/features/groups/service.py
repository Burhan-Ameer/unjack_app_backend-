import logging
from typing import List, Optional
from .repository import GroupRepository
from .models import Group, GroupMember

logger = logging.getLogger("app.groups.service")

class GroupService:
    def __init__(self, repository: GroupRepository):
        self.repository = repository

    async def create_group(self, name: str) -> Group:
        existing = self.repository.get_group_by_name(name)
        if existing:
            raise ValueError(f"Group with name '{name}' already exists")
        return self.repository.create_group(name)

    async def get_group(self, group_id: int) -> Optional[Group]:
        return self.repository.get_group_by_id(group_id)

    async def list_groups(self) -> List[Group]:
        return self.repository.list_groups()

    async def update_group(self, group_id: int, name: str) -> Optional[Group]:
        existing = self.repository.get_group_by_name(name)
        if existing and existing.id != group_id:
            raise ValueError(f"Group with name '{name}' already exists")
        return self.repository.update_group(group_id, name)

    async def delete_group(self, group_id: int) -> bool:
        return self.repository.delete_group(group_id)

    async def add_user_to_group(self, group_id: int, user_id: int) -> GroupMember:
        group = self.repository.get_group_by_id(group_id)
        if not group:
            raise ValueError("Group not found")
        
        # Check if user already in group
        for member in group.members:
            if member.user_id == user_id:
                raise ValueError("User already in group")
                
        return self.repository.add_member(group_id, user_id)
