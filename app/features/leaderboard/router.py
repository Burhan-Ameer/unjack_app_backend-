from fastapi import APIRouter, Depends, HTTPException
from app.utils.jwt import get_current_user
from app.features.auth.models import User
from app.features.leaderboard.service import LeaderboardService
from app.dependencies import get_leaderboard_service
from app.features.leaderboard.schemas import WeeklyLeaderboard, WinnerResponse

router = APIRouter()

@router.get("/{group_id}/weekly", response_model=WeeklyLeaderboard)
async def get_group_weekly_leaderboard(
    group_id: int,
    current_user: User = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    """
    Get the weekly leaderboard for a specific group.
    """
    try:
        # Note: In a production app, we would verify that `current_user` 
        # is actually a member of `group_id` before returning the data.
        return await service.get_weekly_leaderboard(group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{group_id}/winner", response_model=WinnerResponse)
async def get_group_weekly_winner(
    group_id: int,
    current_user: User = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    """
    Get the weekly winner for a specific group.
    """
    try:
        winner = await service.get_weekly_winner(group_id)
        if not winner:
            raise HTTPException(status_code=404, detail="No winner found for this group yet")
        return winner
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
