from pydantic import BaseModel
from typing import List

class StatsResponse(BaseModel):
    user_id: int
    current_streak: int
    longest_streak: int
    total_focus_time: int
    top_blocked_apps: List[str]