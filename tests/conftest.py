import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from app.utils.jwt import get_current_user
from app.main import app
from app.db.session import Base, get_db

# Use an in-memory SQLite database for fast, isolated tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create an async engine for the test database
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed for SQLite
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """
    This fixture runs automatically before every test.
    It creates the database tables, and drops them after the test finishes.
    This ensures every test starts with a completely clean, empty database.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield # The test runs here!
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh database session for the test."""
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="function", autouse=True)
def override_get_db(db_session: AsyncSession):
    """
    This intercepts FastAPI's `Depends(get_db)` and forces it to 
    use our test database session instead of the real one.
    """
    async def _get_test_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _get_test_db
    yield
    # Clean up the override after the test
    app.dependency_overrides.clear()




@pytest.fixture(autouse=True)
def override_auth():
    fake_user = type("User", (), {"id": 1, "email": "burhan@test.com"})()
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield