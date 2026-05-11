from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from .models import Group, GroupMember
from typing import List, Optional

class GroupRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_group(self, name: str, creator_id: int) -> Group:
        group = Group(name=name)
        self.db.add(group)
        await self.db.flush()  # Triggers insert to generate group.id
        
        # Create creator as admin member
        member = GroupMember(group_id=group.id, user_id=creator_id, is_admin=True)
        self.db.add(member) 
        
        await self.db.commit()
        
        # Reload with relationships for Pydantic serialization
        stmt = select(Group).options(selectinload(Group.members)).filter(Group.id == group.id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def add_member(self, group_id: int, user_id: int, is_admin: bool = False) -> GroupMember:
        member = GroupMember(group_id=group_id, user_id=user_id, is_admin=is_admin)
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def get_membership(self, group_id: int, user_id: int) -> Optional[GroupMember]:
        stmt = select(GroupMember).filter(
            GroupMember.group_id == group_id, 
            GroupMember.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_group_by_id(self, group_id: int) -> Optional[Group]:
        stmt = select(Group).options(selectinload(Group.members)).filter(Group.id == group_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_group_by_name(self, name: str) -> Optional[Group]:
        stmt = select(Group).options(selectinload(Group.members)).filter(Group.name == name)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_groups(self) -> List[Group]:
        stmt = select(Group).options(selectinload(Group.members))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_group(self, group_id: int) -> bool:
        group = await self.get_group_by_id(group_id)
        if group:
            await self.db.delete(group)
            await self.db.commit()
            return True
        return False

    async def update_group(self, group_id: int, name: str) -> Optional[Group]:
        group = await self.get_group_by_id(group_id)
        if group:
            group.name = name
            await self.db.commit()
            await self.db.refresh(group)
            
            # Reload with relationships
            stmt = select(Group).options(selectinload(Group.members)).filter(Group.id == group_id)
            result = await self.db.execute(stmt)
            return result.scalars().first()
        return None

    async def update_highest_streak(self, group_id: int, user_id: int, streak: int):
        group = await self.get_group_by_id(group_id)
        if group and streak > group.highest_streak:
            group.highest_streak = streak
            group.top_user_id = user_id
            await self.db.commit()
