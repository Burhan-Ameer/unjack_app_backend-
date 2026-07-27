import pytest
import httpx
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

@pytest.mark.asyncio
async def test_add_member_limit_exceeded():
    from app.features.groups.service import GroupService
    from unittest.mock import AsyncMock, MagicMock
    
    # Mock repository
    mock_repo = MagicMock()
    
    # Mock membership to make the requester an admin
    mock_membership = MagicMock()
    mock_membership.is_admin = True
    mock_repo.get_membership = AsyncMock(return_value=mock_membership)
    
    # Mock a group that already has 60 members
    mock_group = MagicMock()
    mock_group.members = [MagicMock(user_id=i) for i in range(60)]
    mock_repo.get_group_by_id = AsyncMock(return_value=mock_group)
    
    service = GroupService(mock_repo)
    
    # Assert that adding another member raises a ValueError
    with pytest.raises(ValueError) as exc:
        await service.add_user_to_group(group_id=1, user_id=999, requester_id=1)
        
    assert str(exc.value) == "Group has reached its maximum limit of 60 members"