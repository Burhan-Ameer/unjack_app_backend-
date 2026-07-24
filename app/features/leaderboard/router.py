from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.utils.jwt import get_current_user
from app.features.auth.models import User
from app.features.leaderboard.service import LeaderboardService
from app.dependencies import get_leaderboard_service
from app.features.leaderboard.schemas import WeeklyLeaderboard, WinnerResponse
from app.features.groups.models import GroupMember
from app.db.session import get_db

router = APIRouter()

async def _verify_group_membership(group_id: int, user_id: int, db: AsyncSession):
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You are not a member of this group")

@router.get("/{group_id}/weekly", response_model=WeeklyLeaderboard)
async def get_group_weekly_leaderboard(
    group_id: int,
    current_user: User = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        await _verify_group_membership(group_id, current_user.id, db)
        return await service.get_weekly_leaderboard(group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{group_id}/winner", response_model=WinnerResponse)
async def get_group_weekly_winner(
    group_id: int,
    current_user: User = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        await _verify_group_membership(group_id, current_user.id, db)
        winner = await service.get_weekly_winner(group_id)
        if not winner:
            raise HTTPException(status_code=404, detail="No winner found for this group yet")
        return winner
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
