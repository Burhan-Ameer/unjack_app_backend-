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
    """Test logging a focus session successfully."""
    response = await test_client.post("/api/v1/sessions/", json={
        "app_name": "Instagram",
        "package": "com.instagram.android",
        "duration": 3600,
        "blocked_date": datetime.now(timezone.utc).isoformat()
    })
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert "session_id" in data
    assert data["session_id"] is not None

@pytest.mark.asyncio
async def test_get_session_history(test_client: httpx.AsyncClient):
    """Test retrieving session history for the logged-in user."""
    # First, create a session
    await test_client.post("/api/v1/sessions/", json={
        "app_name": "Facebook",
        "package": "com.facebook.katana",
        "duration": 1800,
        "blocked_date": datetime.now(timezone.utc).isoformat()
    })
    
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
