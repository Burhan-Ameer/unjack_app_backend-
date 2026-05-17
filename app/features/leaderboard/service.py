from datetime import date, timedelta, datetime
from typing import Optional
from app.features.leaderboard.repository import LeaderboardRepository
from app.features.groups.repository import GroupRepository
from app.features.leaderboard.schemas import LeaderboardEntry, WeeklyLeaderboard, WinnerResponse

class LeaderboardService:
    def __init__(self, leaderboard_repo: LeaderboardRepository, group_repo: GroupRepository):
        self.leaderboard_repo = leaderboard_repo
        self.group_repo = group_repo

    async def get_weekly_leaderboard(self, group_id: int) -> WeeklyLeaderboard:
        today = date.today()
        week_start_date = today - timedelta(days=today.weekday())  # Monday
        
        week_start = datetime.combine(week_start_date, datetime.min.time())
        week_end = week_start + timedelta(days=7)

        group = await self.group_repo.get_group_by_id(group_id)
        if not group:
            raise ValueError("Group not found")

        user_times = await self.leaderboard_repo.get_group_focus_times(group_id, week_start, week_end)

        entries = []
        rank = 1
        for user, total_time in user_times:
            entries.append(
                LeaderboardEntry(
                    user_id=user.id,
                    username=user.username,
                    total_time=int(total_time),
                    rank=rank
                )
            )
            rank += 1

        return WeeklyLeaderboard(week_start=week_start_date, entries=entries)

    async def get_weekly_winner(self, group_id: int) -> WinnerResponse | None:
        try:
            leaderboard = await self.get_weekly_leaderboard(group_id)
        except ValueError:
            return None
            
        if leaderboard.entries:
            winner = leaderboard.entries[0]
            if winner.total_time > 0:
                return WinnerResponse(
                    user_id=winner.user_id,
                    username=winner.username,
                    total_time=winner.total_time,
                    week_start=leaderboard.week_start
                )
        return None

    async def calculate_and_persist_weekly_winners(self, week_start_date: Optional[date] = None):
        """
        Calculates rankings for all users in all groups for the week starting at `week_start_date`.
        Ranks are saved to the WeeklyStat model, and winners receive a push notification.
        If `week_start_date` is not provided, it defaults to last week's Monday.
        """
        import logging
        logger = logging.getLogger("app.leaderboard.service")
        
        # If week_start_date is not specified, default to the previous week's Monday
        if not week_start_date:
            today = date.today()
            # Calculate last week's Monday
            week_start_date = today - timedelta(days=today.weekday() + 7)
            
        week_start = datetime.combine(week_start_date, datetime.min.time())
        week_end = week_start + timedelta(days=7)
        
        groups = await self.leaderboard_repo.get_all_groups()
        logger.info(f"Calculating weekly winners for {len(groups)} groups for week starting {week_start_date}")
        
        from app.features.notifications.service import NotificationService
        notification_service = NotificationService()
        
        for group in groups:
            group_id = group.id
            group_name = group.name
            try:
                # Fetch all group members with focus times sorted by duration DESC
                user_times = await self.leaderboard_repo.get_group_focus_times(group_id, week_start, week_end)
                
                # Rank users and upsert WeeklyStat rows
                rank = 1
                winner_user = None
                winner_time = 0
                
                for user, total_time in user_times:
                    total_time_int = int(total_time)
                    # Persist stat in DB
                    await self.leaderboard_repo.upsert_weekly_stat(
                        group_id=group_id,
                        user_id=user.id,
                        week_start=week_start_date,
                        total_time=total_time_int,
                        rank=rank
                    )
                    
                    if rank == 1 and total_time_int > 0:
                        winner_user = user
                        winner_time = total_time_int
                        
                    rank += 1
                
                # Extract notification details before committing to avoid accessing expired attributes
                winner_fcm_token = winner_user.fcm_token if winner_user else None
                winner_username = winner_user.username if winner_user else None

                # Commit rankings for this group
                await self.leaderboard_repo.db.commit()
                
                # If there's a winner and they have an FCM token, send a push notification
                if winner_user and winner_fcm_token:
                    hours = winner_time // 3600
                    minutes = (winner_time % 3600) // 60
                    time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                    
                    title = "You won this week! 🏆"
                    body = f"Your focus time of {time_str} beat all your friends in '{group_name}'."
                    
                    logger.info(f"Sending win notification to user {winner_username} (FCM: {winner_fcm_token})")
                    await notification_service.send_push_notification(
                        fcm_token=winner_fcm_token,
                        title=title,
                        body=body
                    )
                    
            except Exception as e:
                logger.error(f"Error calculating winner for group {group_name} (ID: {group_id}): {e}", exc_info=True)
                await self.leaderboard_repo.db.rollback()