# Unjack Backend

A FastAPI-based backend for the Unjack app, a focus and app-blocking tool. It provides user authentication, session logging, stats tracking, friend management, and weekly leaderboards with push notifications.

## Features

- **Authentication**: JWT-based auth with registration, login, and token refresh.
- **Sessions**: Log and retrieve focus sessions.
- **Stats**: Track streaks, total focus time, and top blocked apps.
- **Friends**: Manage friend requests and relationships.
- **Leaderboard**: Weekly rankings among friends, with winner notifications.
- **Cron Job**: Automated weekly winner calculation and FCM push alerts.

## Architecture

- **Model-Controller-Service-Schema**: Endpoints (controllers) call services, which interact with SQLAlchemy models. Pydantic schemas handle validation.
- Async operations with SQLAlchemy.
- Firebase Cloud Messaging (FCM) for notifications.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill values for your environment
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?sslmode=require
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   FCM_SERVER_KEY=your_fcm_key
   LOG_LEVEL=INFO
   SQLALCHEMY_ECHO=false
   AUTH_RATE_LIMIT_PER_MINUTE=15
   AUTH_RATE_LIMIT_WINDOW_SECONDS=60
   RATE_LIMIT_KEY_PREFIX=rate_limit:auth
   REDIS_URL=redis://localhost:6379/0
   ```

   Notes:
   - Supabase: use your project connection string with `?sslmode=require`.
   - Azure PostgreSQL (production): use `username@servername` and keep `?sslmode=require`.

3. Run database migrations (if using Alembic):
   ```
   alembic upgrade head
   ```

4. Start the server:
   ```
   uvicorn app.main:app --reload
   ```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API docs.

## Operational Endpoints

- `GET /api/v1/health/live` for process liveness checks.
- `GET /api/v1/health` for readiness checks including a DB probe.

## Rate Limiting

- Auth endpoints use a Redis-backed sliding window limiter.
- Configure via `AUTH_RATE_LIMIT_PER_MINUTE`, `AUTH_RATE_LIMIT_WINDOW_SECONDS`, `RATE_LIMIT_KEY_PREFIX`, and `REDIS_URL`.
- For multi-container production, all backend instances must use the same shared `REDIS_URL`.
- Use env-specific prefixes like `RATE_LIMIT_KEY_PREFIX=rate_limit:prod:auth` to isolate environments.

### Managed Redis Examples

- Aiven Redis (TLS): `rediss://default:<password>@<service-name>.aivencloud.com:<port>/0`
- Upstash Redis (TLS): `rediss://default:<password>@<region>.upstash.io:6379/0`
- Azure Cache for Redis (TLS): `rediss://:<access-key>@<name>.redis.cache.windows.net:6380/0`

## Testing

Run tests with:
```
pytest
```

## Directory Structure

- `app/`: Main application code
  - `api/v1/`: API endpoints and router
  - `core/`: Configuration
  - `db/`: Database session
  - `models/`: SQLAlchemy models
  - `schemas/`: Pydantic schemas
  - `services/`: Business logic
  - `utils/`: Utilities (JWT, hashing)
- `tests/`: Test files
- `requirements.txt`: Dependencies# unjack_app_backend-
