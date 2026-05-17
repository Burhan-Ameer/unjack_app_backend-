import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .jobs import run_weekly_winner_calculation, prune_expired_rate_limit_buckets

logger = logging.getLogger("app.scheduler")

scheduler = AsyncIOScheduler()

def setup_scheduler():
    """
    Schedules the background cron jobs.
    """
    # 1. Weekly Winner Calculation (Mon 00:05 UTC)
    trigger = CronTrigger(day_of_week="mon", hour=0, minute=5, timezone="UTC")
    scheduler.add_job(
        run_weekly_winner_calculation,
        trigger=trigger,
        id="weekly_winner_calculation",
        replace_existing=True,
    )
    logger.info("Scheduler: Scheduled weekly winner calculation job (every Monday at 00:05 UTC).")

    # 2. Rate Limit Database Pruning (Every 30 minutes)
    scheduler.add_job(
        prune_expired_rate_limit_buckets,
        trigger="interval",
        minutes=30,
        id="rate_limit_pruning",
        replace_existing=True,
    )
    logger.info("Scheduler: Scheduled rate limit pruning job (every 30 minutes).")

