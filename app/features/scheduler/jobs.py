import logging
from app.db.session import AsyncSessionLocal
from app.features.leaderboard.repository import LeaderboardRepository
from app.features.leaderboard.service import LeaderboardService
from app.features.groups.repository import GroupRepository

logger = logging.getLogger("app.scheduler.jobs")

async def run_weekly_winner_calculation():
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

