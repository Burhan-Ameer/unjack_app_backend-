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
    # 1. Create the user in the database (matching the mocked current_user id=1)
    user = DBUser(id=1, username="burhan", email="burhan@test.com", hashed_password="hashedpassword")
    db_session.add(user)
    await db_session.commit()

    # 2. Create a group (which adds user 1 as an admin member)
    response = await test_client.post("/api/v1/groups/", json={"name": "Focus Warriors"})
    assert response.status_code == 201
    group_id = response.json()["id"]

    # 3. Log a focus session for the user
    await test_client.post("/api/v1/sessions/", json={
        "app_name": "YouTube",
        "package": "com.google.android.youtube",
        "duration": 5400, # 1.5 hours
        "blocked_date": datetime.now(timezone.utc).isoformat()
    })

    # 4. Retrieve the weekly leaderboard
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
    # 1. Create the user in the database
    user = DBUser(id=1, username="burhan", email="burhan@test.com", hashed_password="hashedpassword")
    db_session.add(user)
    await db_session.commit()

    # 2. Create a group
    response = await test_client.post("/api/v1/groups/", json={"name": "Streak Kings"})
    assert response.status_code == 201
    group_id = response.json()["id"]

    # 3. Log a focus session
    await test_client.post("/api/v1/sessions/", json={
        "app_name": "Facebook",
        "package": "com.facebook.katana",
        "duration": 7200, # 2 hours
        "blocked_date": datetime.now(timezone.utc).isoformat()
    })

    # 4. Retrieve the winner
    response = await test_client.get(f"/api/v1/leaderboard/{group_id}/winner")
    assert response.status_code == 200, response.text
    data = response.json()
    
    assert data["username"] == "burhan"
    assert data["total_time"] == 7200
