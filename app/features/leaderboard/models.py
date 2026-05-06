# from sqlalchemy import Column, Integer, BigInteger, Date, ForeignKey
# from app.db.session import Base

# class Streak(Base):
#     __tablename__ = "streaks"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), unique=True)
#     current_streak = Column(Integer, default=0)
#     longest_streak = Column(Integer, default=0)
#     total_focus_time = Column(BigInteger, default=0)  # in seconds

# class WeeklyStat(Base):
#     __tablename__ = "weekly_stats"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     week_start = Column(Date)
#     total_time = Column(BigInteger, default=0)
#     rank = Column(Integer)