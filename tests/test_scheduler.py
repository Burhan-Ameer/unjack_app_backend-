import pytest
from datetime import datetime, date, timedelta, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy import select
from app.features.auth.models import User
from app.features.groups.models import Group, GroupMember
from app.features.sessions.models import AppSession
from app.features.leaderboard.models import WeeklyStat
from app.features.leaderboard.service import LeaderboardService
from app.features.leaderboard.repository import LeaderboardRepository
from app.features.groups.repository import GroupRepository

@pytest.mark.asyncio
async def test_calculate_and_persist_weekly_winners(db_session):
    # 1. Create test users (one with FCM token, one without)
    user1 = User(
        id=1,
        username="user1",
        email="user1@test.com",
        hashed_password="hashedpassword",
        fcm_token="token_user_1"
    )
    user2 = User(
        id=2,
        username="user2",
        email="user2@test.com",
        hashed_password="hashedpassword",
        fcm_token="token_user_2"
    )
    db_session.add_all([user1, user2])
    await db_session.commit()

    # 2. Create a test group and join both users
    group = Group(id=1, name="Focus Champions")
    db_session.add(group)
    await db_session.commit()
    
    member1 = GroupMember(group_id=1, user_id=1, is_admin=True)
    member2 = GroupMember(group_id=1, user_id=2, is_admin=False)
    db_session.add_all([member1, member2])
    await db_session.commit()

    # 3. Create app sessions in the *previous* week
    # Let's say last week's Monday was 7 days ago.
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    
    # Session for user1 (longer duration: 2 hours = 7200 seconds)
    session1 = AppSession(
        user_id=1,
        app_name="YouTube",
        package="com.google.android.youtube",
        duration=7200,
        blocked_date=datetime.combine(last_monday + timedelta(days=2), datetime.min.time()).replace(tzinfo=timezone.utc)
    )
    # Session for user2 (shorter duration: 1 hour = 3600 seconds)
    session2 = AppSession(
        user_id=2,
        app_name="Facebook",
        package="com.facebook.katana",
        duration=3600,
        blocked_date=datetime.combine(last_monday + timedelta(days=3), datetime.min.time()).replace(tzinfo=timezone.utc)
    )
    db_session.add_all([session1, session2])
    await db_session.commit()

    # 4. Invoke calculate_and_persist_weekly_winners with a mock NotificationService
    leaderboard_repo = LeaderboardRepository(db_session)
    group_repo = GroupRepository(db_session)
    service = LeaderboardService(leaderboard_repo, group_repo)

    with patch("app.features.notifications.service.NotificationService.send_push_notification", new_callable=AsyncMock) as mock_send:
        await service.calculate_and_persist_weekly_winners(week_start_date=last_monday)

        # Verify that the push notification was sent to user1 (winner)
        mock_send.assert_called_once()
        called_args, called_kwargs = mock_send.call_args
        
        # Check params passed to send_push_notification
        assert called_kwargs.get("fcm_token") == "token_user_1"
        assert "You won this week!" in called_kwargs.get("title")
        assert "2h 0m" in called_kwargs.get("body")
        assert "Focus Champions" in called_kwargs.get("body")

    # 5. Check database state to verify WeeklyStat records
    result = await db_session.execute(
        select(WeeklyStat).where(WeeklyStat.group_id == 1, WeeklyStat.week_start == last_monday).order_by(WeeklyStat.rank)
    )
    stats = result.scalars().all()
    
    assert len(stats) == 2
    
    # Rank 1: user1 (7200 seconds)
    assert stats[0].user_id == 1
    assert stats[0].rank == 1
    assert stats[0].total_time == 7200

    # Rank 2: user2 (3600 seconds)
    assert stats[1].user_id == 2
    assert stats[1].rank == 2
    assert stats[1].total_time == 3600
