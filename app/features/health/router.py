from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.auth.models import User

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    # Light DB probe so this endpoint also confirms database connectivity.
    await db.execute(select(1))
    return {"status": "ok"}


@router.get("/users/check")
async def check_users(
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar_one()

    users_result = await db.execute(
        select(User.id, User.username, User.email)
        .order_by(User.id.asc())
        .limit(limit)
    )
    users = users_result.all()

    return {
        "total_users": total_users,
        "showing": len(users),
        "users": [
            {"id": user_id, "username": username, "email": email}
            for user_id, username, email in users
        ],
    }