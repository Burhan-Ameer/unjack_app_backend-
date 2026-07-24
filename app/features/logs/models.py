from sqlalchemy import Column,Integer,String,Text,DateTime 
from sqlalchemy.sql import func
from app.db.session import Base



class DBLog(Base):
    __tablename__="db_logs"
    id=Column(Integer,primary_key=True,index=True)
    level =Column(String(50),nullable=False,index=True)
    logger =Column(String(100),nullable=False) # means where it came from (i.e: app.router.auth something like this )
    message=Column(Text,nullable=False)
    occured_at=Column(DateTime(timezone=True),server_default=func.now())
     # Trackers for context:
    request_id = Column(String(100), nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    traceback = Column(Text, nullable=True)