from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class SessionStart(BaseModel):
    app_name: str = Field(..., min_length=1)
    package: str = Field(..., min_length=1)
    ttl_seconds: int | None = Field(default=None)

    @field_validator("ttl_seconds")
    @classmethod
    def validate_ttl(cls, v: int | None) -> int | None:
        if v is not None:
            if v <= 0:
                raise ValueError("ttl_seconds must be positive if provided")
            if v > 21600:
                raise ValueError("ttl_seconds cannot exceed 6 hours (21600 seconds)")
        return v

class SessionResponse(BaseModel):
    id: int
    user_id: int
    app_name: str
    package: str
    duration: int
    blocked_date: Optional[datetime] = None

    model_config = {"from_attributes": True}

class SessionHistory(BaseModel):
    sessions: list[SessionResponse]