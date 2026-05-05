from sqlalchemy.orm import Session
from .models import Group, GroupMember
from typing import List, Optional

class GroupRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_group(self, name: str) -> Group:
        group = Group(name=name)
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def add_member(self, group_id: int, user_id: int) -> GroupMember:
        member = GroupMember(group_id=group_id, user_id=user_id)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_group_by_id(self, group_id: int) -> Optional[Group]:
        return self.db.query(Group).filter(Group.id == group_id).first()

    def get_group_by_name(self, name: str) -> Optional[Group]:
        return self.db.query(Group).filter(Group.name == name).first()

    def list_groups(self) -> List[Group]:
        return self.db.query(Group).all()

    def delete_group(self, group_id: int) -> bool:
        group = self.get_group_by_id(group_id)
        if group:
            self.db.delete(group)
            self.db.commit()
            return True
        return False

    def update_group(self, group_id: int, name: str) -> Optional[Group]:
        group = self.get_group_by_id(group_id)
        if group:
            group.name = name
            self.db.commit()
            self.db.refresh(group)
            return group
        return None

    def update_highest_streak(self, group_id: int, user_id: int, streak: int):
        group = self.get_group_by_id(group_id)
        if group and streak > group.highest_streak:
            group.highest_streak = streak
            group.top_user_id = user_id
            self.db.commit()
