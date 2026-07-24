import pytest
import httpx
from datetime import datetime, timezone
from app.main import app

@pytest.fixture
def test_client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")

@pytest.mark.asyncio
async def test_create_session(test_client: httpx.AsyncClient):
    """Test logging a focus session successfully via start/stop handshake."""
    from unittest.mock import patch
    import datetime as dt
    
    # 1. Start session
    start_time = dt.datetime(2026, 6, 14, 12, 0, 0, tzinfo=dt.timezone.utc)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start_time
        response = await test_client.post("/api/v1/sessions/start", json={
            "app_name": "Instagram",
            "package": "com.instagram.android"
        })
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "started"
        
    # 2. Stop session (1 hour later)
    stop_time = start_time + dt.timedelta(hours=1)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = stop_time
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/stop")
        
    assert response.status_code == 200, response.text
    data = response.json()
    assert "session_id" in data
    assert data["duration"] == 3600

@pytest.mark.asyncio
async def test_get_session_history(test_client: httpx.AsyncClient):
    """Test retrieving session history for the logged-in user."""
    from unittest.mock import patch
    import datetime as dt
    
    # 1. Start session
    start_time = dt.datetime(2026, 6, 14, 12, 0, 0, tzinfo=dt.timezone.utc)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start_time
        await test_client.post("/api/v1/sessions/start", json={
            "app_name": "Facebook",
            "package": "com.facebook.katana"
        })
        
    # 2. Stop session
    stop_time = start_time + dt.timedelta(seconds=1800)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = stop_time
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        await test_client.post("/api/v1/sessions/stop")
    
    # Retrieve history
    response = await test_client.get("/api/v1/sessions/history")
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) >= 1
    session = data["sessions"][0]
    assert session["app_name"] == "Facebook"
    assert session["package"] == "com.facebook.katana"
    assert session["duration"] == 1800

@pytest.mark.asyncio
async def test_streak_calculation_flow(db_session, test_client: httpx.AsyncClient):
    """Test the complete streak calculation flow over multiple simulated days."""
    from unittest.mock import patch
    import datetime as dt
    from app.features.leaderboard.models import Streak
    from sqlalchemy import select

    # --- DAY 1: Monday, June 8, 2026 ---
    # Log first session ever
    day1_start = dt.datetime(2026, 6, 8, 10, 0, 0, tzinfo=dt.timezone.utc)
    day1_stop = day1_start + dt.timedelta(seconds=1800)
    
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = day1_start
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/start", json={
            "app_name": "Instagram",
            "package": "com.instagram.android"
        })
        assert response.status_code == 200, response.text

    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = day1_stop
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/stop")
        assert response.status_code == 200, response.text

    # Verify streak is created
    result = await db_session.execute(select(Streak).where(Streak.user_id == 1))
    streak = result.scalar_one_or_none()
    assert streak is not None
    assert streak.current_streak == 1
    assert streak.longest_streak == 1
    assert streak.total_focus_time == 1800
    assert streak.last_active == dt.date(2026, 6, 8)

    # --- DAY 1 (Later same day): Monday, June 8, 2026 ---
    # Log second session on same day
    day1_later_start = day1_start + dt.timedelta(hours=2)
    day1_later_stop = day1_later_start + dt.timedelta(seconds=1200)
    
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = day1_later_start
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/start", json={
            "app_name": "Facebook",
            "package": "com.facebook.katana"
        })
        assert response.status_code == 200, response.text

    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = day1_later_stop
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/stop")
        assert response.status_code == 200, response.text

    # Verify duration updated but streak count unchanged
    await db_session.refresh(streak)
    assert streak.current_streak == 1
    assert streak.longest_streak == 1
    assert streak.total_focus_time == 3000  # 1800 + 1200
    assert streak.last_active == dt.date(2026, 6, 8)

    # --- DAY 2: Tuesday, June 9, 2026 ---
    # Log session on consecutive day
    day2_start = dt.datetime(2026, 6, 9, 14, 0, 0, tzinfo=dt.timezone.utc)
    day2_stop = day2_start + dt.timedelta(seconds=3600)
    
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = day2_start
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/start", json={
            "app_name": "YouTube",
            "package": "com.google.android.youtube"
        })
        assert response.status_code == 200, response.text

    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = day2_stop
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/stop")
        assert response.status_code == 200, response.text

    # Verify streak incremented to 2
    await db_session.refresh(streak)
    assert streak.current_streak == 2
    assert streak.longest_streak == 2
    assert streak.total_focus_time == 6600  # 3000 + 3600
    assert streak.last_active == dt.date(2026, 6, 9)

    # --- DAY 4: Thursday, June 11, 2026 (Skipped Wednesday, June 10) ---
    # Log session after a gap
    day4_start = dt.datetime(2026, 6, 11, 11, 0, 0, tzinfo=dt.timezone.utc)
    day4_stop = day4_start + dt.timedelta(seconds=600)
    
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = day4_start
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/start", json={
            "app_name": "Instagram",
            "package": "com.instagram.android"
        })
        assert response.status_code == 200, response.text

    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = day4_stop
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/stop")
        assert response.status_code == 200, response.text

    # Verify streak resets to 1, longest streak remains 2
    await db_session.refresh(streak)
    assert streak.current_streak == 1
    assert streak.longest_streak == 2
    assert streak.total_focus_time == 7200  # 6600 + 600
    assert streak.last_active == dt.date(2026, 6, 11)

@pytest.mark.asyncio
async def test_stop_no_active_session(test_client: httpx.AsyncClient):
    """Test stopping a session when none is active."""
    response = await test_client.post("/api/v1/sessions/stop")
    assert response.status_code == 400
    assert "no active focus session" in response.json()["error"]["message"].lower()

@pytest.mark.asyncio
async def test_start_already_active_session(test_client: httpx.AsyncClient):
    """Test starting a session when one is already active."""
    await test_client.post("/api/v1/sessions/start", json={
        "app_name": "Instagram",
        "package": "com.instagram.android"
    })
    response = await test_client.post("/api/v1/sessions/start", json={
        "app_name": "Facebook",
        "package": "com.facebook.katana"
    })
    assert response.status_code == 400
    assert "already have an active focus session" in response.json()["error"]["message"].lower()

@pytest.mark.asyncio
async def test_session_too_short(test_client: httpx.AsyncClient):
    """Test session rejected if under 10 seconds."""
    from unittest.mock import patch
    import datetime as dt
    
    start_time = dt.datetime(2026, 6, 14, 12, 0, 0, tzinfo=dt.timezone.utc)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start_time
        await test_client.post("/api/v1/sessions/start", json={
            "app_name": "Instagram",
            "package": "com.instagram.android"
        })
        
    # Stop 5 seconds later
    stop_time = start_time + dt.timedelta(seconds=5)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = stop_time
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        response = await test_client.post("/api/v1/sessions/stop")
        
    assert response.status_code == 400
    assert "too short" in response.json()["error"]["message"].lower()
