import pytest
import httpx
from datetime import datetime, timezone
from app.features.auth.models import User as DBUser
from app.main import app

@pytest.fixture
def test_client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")

@pytest.mark.asyncio
async def test_get_weekly_leaderboard(test_client: httpx.AsyncClient, db_session):
    """Test retrieving weekly leaderboard for a group with aggregated session data."""
    from unittest.mock import patch
    import datetime as dt

    user = DBUser(id=1, username="burhan", email="burhan@test.com", hashed_password="hashedpassword")
    db_session.add(user)
    await db_session.commit()

    response = await test_client.post("/api/v1/groups/", json={"name": "Focus Warriors"})
    assert response.status_code == 201
    group_id = response.json()["id"]

    start_time = dt.datetime(2026, 6, 14, 12, 0, 0, tzinfo=dt.timezone.utc)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start_time
        await test_client.post("/api/v1/sessions/start", json={
            "app_name": "YouTube",
            "package": "com.google.android.youtube"
        })

    stop_time = start_time + dt.timedelta(seconds=5400)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = stop_time
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        await test_client.post("/api/v1/sessions/stop")

    freeze_week = dt.date(2026, 6, 14)  # Sunday — week_start = June 8, covers June 14 session
    with patch("app.features.leaderboard.service.date") as mock_service_date:
        mock_service_date.today.return_value = freeze_week
        mock_service_date.side_effect = lambda *args, **kwargs: dt.date(*args, **kwargs) if args else freeze_week
        response = await test_client.get(f"/api/v1/leaderboard/{group_id}/weekly")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "entries" in data
    assert len(data["entries"]) == 1
    
    entry = data["entries"][0]
    assert entry["username"] == "burhan"
    assert entry["total_time"] == 5400
    assert entry["rank"] == 1

@pytest.mark.asyncio
async def test_get_weekly_winner(test_client: httpx.AsyncClient, db_session):
    """Test retrieving the weekly winner for a group."""
    from unittest.mock import patch
    import datetime as dt

    user = DBUser(id=1, username="burhan", email="burhan@test.com", hashed_password="hashedpassword")
    db_session.add(user)
    await db_session.commit()

    response = await test_client.post("/api/v1/groups/", json={"name": "Streak Kings"})
    assert response.status_code == 201
    group_id = response.json()["id"]

    start_time = dt.datetime(2026, 6, 14, 12, 0, 0, tzinfo=dt.timezone.utc)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = start_time
        await test_client.post("/api/v1/sessions/start", json={
            "app_name": "Facebook",
            "package": "com.facebook.katana"
        })

    stop_time = start_time + dt.timedelta(seconds=7200)
    with patch("app.features.sessions.service.datetime") as mock_datetime:
        mock_datetime.now.return_value = stop_time
        mock_datetime.fromisoformat = dt.datetime.fromisoformat
        await test_client.post("/api/v1/sessions/stop")

    freeze_week = dt.date(2026, 6, 14)
    with patch("app.features.leaderboard.service.date") as mock_service_date:
        mock_service_date.today.return_value = freeze_week
        mock_service_date.side_effect = lambda *args, **kwargs: dt.date(*args, **kwargs) if args else freeze_week
        response = await test_client.get(f"/api/v1/leaderboard/{group_id}/winner")
    assert response.status_code == 200, response.text
    data = response.json()
    
    assert data["username"] == "burhan"
    assert data["total_time"] == 7200
