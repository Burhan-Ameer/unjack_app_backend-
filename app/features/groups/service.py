import logging
from typing import List, Optional
from .repository import GroupRepository
from .models import Group, GroupMember

logger = logging.getLogger("app.groups.service")

class GroupService:
    """
    Business logic layer for handling Group operations.
    Orchestrates validation, business rules, and delegates database operations to the GroupRepository.
    """
    def __init__(self, repository: GroupRepository):
        self.repository = repository

    async def create_group(self, name: str) -> Group:
        """
        Create a new group with the given name.
        
        Raises:
            ValueError: If a group with this name already exists.
        """
        existing = await self.repository.get_group_by_name(name)
        if existing:
            raise ValueError(f"Group with name '{name}' already exists")
        return await self.repository.create_group(name)
        

    async def get_group(self, group_id: int) -> Optional[Group]:
        """
        Retrieve a specific group by its ID.
        
        Returns:
            The Group object if found, otherwise None.
        """
        return await self.repository.get_group_by_id(group_id)

    async def list_groups(self) -> List[Group]:
        """
        Retrieve a list of all groups currently in the system.
        """
        return await self.repository.list_groups()

    async def update_group(self, group_id: int, name: str) -> Optional[Group]:
        """
        Update the name of an existing group.
        
        Raises:
            ValueError: If the newly proposed name is already taken by a different group.
        Returns:
            The updated Group object, or None if the group does not exist.
        """
        existing = await self.repository.get_group_by_name(name)
        if existing and existing.id != group_id:
            raise ValueError(f"Group with name '{name}' already exists")
        return await self.repository.update_group(group_id, name)

    async def delete_group(self, group_id: int) -> bool:
        """
        Delete a group by its ID.
        
        Returns:
            True if the deletion was successful, False if the group was not found.
        """
        return await self.repository.delete_group(group_id)

    async def add_user_to_group(self, group_id: int, user_id: int) -> GroupMember:
        """
        Add a specific user to a group.
        
        Raises:
            ValueError: If the group does not exist, or if the user is already a member.
        Returns:
            The newly created GroupMember association record.
        """
        group = await self.repository.get_group_by_id(group_id)
        if not group:
            raise ValueError("Group not found")
        
        # Check if user already in group
        for member in group.members:
            if member.user_id == user_id:
                raise ValueError("User already in group")
                
        return await self.repository.add_member(group_id, user_id)
