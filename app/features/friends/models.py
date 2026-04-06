from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum

class FriendshipStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"

class Friendship(Base):
    __tablename__ = "friendships"
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"))
    addressee_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(FriendshipStatus), default=FriendshipStatus.pending)