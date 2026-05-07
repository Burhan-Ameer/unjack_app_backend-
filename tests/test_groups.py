import pytest
import httpx
from unittest.mock import patch
from app.main import app

# We use an ASGITransport to test the FastAPI app directly without starting a server
@pytest.fixture
def test_client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")

@pytest.mark.asyncio
async def test_create_group(test_client):
    response = await test_client.post("/api/v1/groups/", json={"name": "Study Group"})
    
    assert response.status_code == 201
    assert response.json()["name"] == "Study Group"
    assert response.json()["id"] is not None



@pytest.mark.asyncio
async def test_create_group_without_name(test_client):
    response = await test_client.post("/api/v1/groups/", json={"name":" "})
    
    assert response.status_code == 422
    assert "name must be non-empty string" in response.json()["error"]["details"][0]["msg"]

@pytest.mark.asyncio
async def test_create_group_short_name(test_client):
    response = await test_client.post("/api/v1/groups/", json={"name":" A "})
    
    assert response.status_code == 422
    assert "name must be at least 2 characters long" in response.json()["error"]["details"][0]["msg"]