from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from app.db.session import Base

class AppSession(Base):
    __tablename__ = "app_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    app_name = Column(String)
    package = Column(String)
    duration = Column(BigInteger)  # in seconds
    blocked_date = Column(DateTime)