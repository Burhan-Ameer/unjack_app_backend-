import logging
import datetime
from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.features.leaderboard.repository import LeaderboardRepository
from app.features.leaderboard.service import LeaderboardService
from app.features.groups.repository import GroupRepository
from app.features.auth.models import RateLimitBucket

logger = logging.getLogger("app.scheduler.jobs")

async def run_weekly_winner_calculation():
    """
    Background job to run the weekly winner calculation.
    Instantiates its own DB session manually since it runs outside of the FastAPI request context.
    """
    logger.info("Scheduler Jobs: Starting weekly winner calculation background task...")
    async with AsyncSessionLocal() as db:
        try:
            leaderboard_repo = LeaderboardRepository(db)
            group_repo = GroupRepository(db)
            leaderboard_service = LeaderboardService(leaderboard_repo, group_repo)
            
            await leaderboard_service.calculate_and_persist_weekly_winners()
            logger.info("Scheduler Jobs: Weekly winner calculation background task completed successfully.")
        except Exception as e:
            logger.exception(f"Scheduler Jobs: Error running weekly winner calculation background task: {e}")


async def prune_expired_rate_limit_buckets():
    """
    Background job to delete expired rate limit rows from PostgreSQL.
    Runs periodically to prevent table bloat.
    """
    logger.info("Scheduler Jobs: Starting rate limit bucket pruning...")
    now = datetime.datetime.now(datetime.timezone.utc)
    async with AsyncSessionLocal() as db:
        try:
            stmt = delete(RateLimitBucket).where(RateLimitBucket.expires_at < now)
            result = await db.execute(stmt)
            await db.commit()
            logger.info(f"Scheduler Jobs: Rate limit bucket pruning completed successfully. Cleared expired entries.")
        except Exception as e:
            await db.rollback()
            logger.exception(f"Scheduler Jobs: Error running rate limit bucket pruning: {e}")

