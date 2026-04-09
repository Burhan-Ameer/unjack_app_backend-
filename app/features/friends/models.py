from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.sql import func
from app.db.session import Base
import enum

class FriendshipStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"

class Friendship(Base):
    __tablename__ = "friendships"
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    addressee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(FriendshipStatus), default=FriendshipStatus.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)