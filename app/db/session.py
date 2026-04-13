from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

db_url = make_url(settings.database_url)
connect_args = {}

# asyncpg does not accept the psycopg-style `sslmode` keyword.
sslmode = db_url.query.get("sslmode")
if db_url.drivername.endswith("+asyncpg") and sslmode is not None:
    cleaned_query = dict(db_url.query)
    cleaned_query.pop("sslmode", None)
    db_url = db_url.set(query=cleaned_query)
    if sslmode.lower() not in {"disable", "allow", "prefer"}:
        connect_args["ssl"] = "require"

engine = create_async_engine(db_url, echo=settings.sqlalchemy_echo, connect_args=connect_args)
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
