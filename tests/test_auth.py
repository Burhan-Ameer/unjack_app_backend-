import pytest
import httpx
from unittest.mock import patch
from app.main import app

# Create a fixture to mock the rate limiter for auth tests
# This prevents our tests from failing if Redis is not available,
# and also prevents rate limiting from breaking our tests.
@pytest.fixture(autouse=True)
def mock_rate_limiter():
    with patch("app.features.auth.router.auth_rate_limiter.check", return_value=None):
        yield

# We use an ASGITransport to test the FastAPI app directly without starting a server
@pytest.fixture
def test_client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")

@pytest.mark.asyncio
async def test_register_success(test_client: httpx.AsyncClient):
    """Test successful user registration."""
    response = await test_client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "strongpassword123"
    })
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert "user_id" in data
    assert data["user_id"] is not None

@pytest.mark.asyncio
async def test_register_duplicate_username(test_client: httpx.AsyncClient):
    """Test registering a user with an already existing username fails."""
    # Register first user
    await test_client.post("/api/v1/auth/register", json={
        "username": "duplicate_user",
        "email": "first@example.com",
        "password": "strongpassword123"
    })
    
    # Attempt to register second user with the same username
    response = await test_client.post("/api/v1/auth/register", json={
        "username": "duplicate_user",
        "email": "second@example.com",
        "password": "strongpassword123"
    })
    
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower() or "exists" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_register_duplicate_email(test_client: httpx.AsyncClient):
    """Test registering a user with an already existing email fails."""
    # Register first user
    await test_client.post("/api/v1/auth/register", json={
        "username": "user_one",
        "email": "duplicate@example.com",
        "password": "strongpassword123"
    })
    
    # Attempt to register second user with the same email
    response = await test_client.post("/api/v1/auth/register", json={
        "username": "user_two",
        "email": "duplicate@example.com",
        "password": "strongpassword123"
    })
    
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower() or "exists" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_register_invalid_payload(test_client: httpx.AsyncClient):
    """Test registering with missing required fields fails validation."""
    # Missing password
    response = await test_client.post("/api/v1/auth/register", json={
        "username": "invaliduser",
        "email": "invaliduser@example.com"
    })
    
    assert response.status_code == 422 # 422 Unprocessable Entity (FastAPI validation error)