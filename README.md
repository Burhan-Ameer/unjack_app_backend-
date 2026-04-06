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

2. Set up environment variables in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   FCM_SERVER_KEY=your_fcm_key
   ```

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
