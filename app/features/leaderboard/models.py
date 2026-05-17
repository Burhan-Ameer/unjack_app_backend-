from sqlalchemy import Column, Integer, BigInteger, Date, ForeignKey
from app.db.session import Base

class Streak(Base):
    __tablename__ = "streaks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_focus_time = Column(BigInteger, default=0)  # in seconds

class WeeklyStat(Base):
    __tablename__ = "weekly_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_start = Column(Date, nullable=False)
    total_time = Column(BigInteger, default=0)
    rank = Column(Integer)