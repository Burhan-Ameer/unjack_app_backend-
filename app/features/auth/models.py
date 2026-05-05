from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Partial index for active users to optimize cron job queries
    __table_args__ = (
        Index(
            "ix_users_active_only",
            "id",
            postgresql_where=(is_active == True),
        ),
    )