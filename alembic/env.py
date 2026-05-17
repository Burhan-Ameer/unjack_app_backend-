import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.session import Base

# Import models so metadata includes all tables.
from app.features.auth import models as auth_models  # noqa: F401

from app.features.leaderboard import models as leaderboard_models  # noqa: F401
from app.features.sessions import models as sessions_models  # noqa: F401
from app.features.groups import models as groups_models  # noqa: F401

from sqlalchemy.engine import make_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Parse and clean URL for asyncpg (stripping sslmode parameter)
async_db_url = make_url(settings.database_url)
if not async_db_url.drivername.endswith("+asyncpg"):
    async_db_url = async_db_url.set(
        drivername=async_db_url.drivername.replace("postgresql", "postgresql+asyncpg")
    )

connect_args = {}
sslmode = async_db_url.query.get("sslmode")
if sslmode is not None:
    cleaned_query = dict(async_db_url.query)
    cleaned_query.pop("sslmode", None)
    async_db_url = async_db_url.set(query=cleaned_query)
    if sslmode.lower() not in {"disable", "allow", "prefer"}:
        connect_args["ssl"] = "require"

config.set_main_option("sqlalchemy.url", async_db_url.render_as_string(hide_password=False))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_async_engine(
        async_db_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async def do_run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_migrate)
        await connectable.dispose()

    def do_migrate(connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(do_run_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
