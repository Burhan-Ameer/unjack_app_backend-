from pydantic import BaseModel
from datetime import date
from typing import List

class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    total_time: int
    rank: int

class WeeklyLeaderboard(BaseModel):
    week_start: date
    entries: List[LeaderboardEntry]

class WinnerResponse(BaseModel):
    user_id: int
    username: str
    total_time: int
    week_start: date