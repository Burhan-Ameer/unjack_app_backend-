import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .jobs import run_weekly_winner_calculation

logger = logging.getLogger("app.scheduler")

scheduler = AsyncIOScheduler()

def setup_scheduler():
    trigger = CronTrigger(day_of_week="thu", hour=1, minute=5, timezone="UTC")
    scheduler.add_job(
        run_weekly_winner_calculation,
        trigger=trigger, 
        id="weekly_winner_calculation",
        replace_existing=True,
    )
    logger.info("Scheduler: Scheduled weekly winner calculation job (every Thursday at 01:05 UTC).")

