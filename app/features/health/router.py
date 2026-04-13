import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.auth.models import User

router = APIRouter()
logger = logging.getLogger("app.health.router")


@router.get("/health/live")
async def liveness_check():
    return {"status": "ok"}


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))
    except Exception:
        logger.exception("Health DB probe failed")
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "database": "ok"}


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
