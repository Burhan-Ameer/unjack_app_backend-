from pydantic import BaseModel
from datetime import datetime

class SessionCreate(BaseModel):
    app_name: str
    package: str
    duration: int  # seconds
    blocked_date: datetime

class SessionResponse(BaseModel):
    id: int
    user_id: int
    app_name: str
    package: str
    duration: int
    blocked_date: datetime

    class Config:
        from_attributes = True

class SessionHistory(BaseModel):
    sessions: list[SessionResponse]