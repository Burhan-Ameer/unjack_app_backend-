# Unjack Backend

A FastAPI-based backend for the Unjack app, a focus and app-blocking tool. It provides user authentication, session logging, stats tracking, group management, and weekly leaderboards.

---

## Features

* **Authentication**: JWT-based auth with registration, login, token refresh, and password hashing using Argon2.
* **Sessions**: Log and retrieve focus sessions using a secure start/stop handshake flow (stored temporarily in Redis to prevent leaderboard cheating).
* **Groups**: Create, manage, and join groups (enforces a business rule of **maximum 60 members** per group).
* **Leaderboard**: Weekly rankings within groups, with winner calculation.
* **Cron Job**: Automated weekly winner calculation and persistence.
* **Database Logging**: Asynchronous, non-blocking queue logging engine that captures logs (with tracebacks, request IDs, and user IDs) to PostgreSQL.
* **Rate Limiting**: Redis-backed sliding window rate limiter (restricts auth endpoints to 15 requests per 15 minutes).

---

## Architecture

This project is built using a **Modular Clean Router Structure (MCRS)**:
* **Features Domain Modules**: Code is separated by features under [app/features/](file:///c:/Users/Admin/Desktop/unjack_app_backend-/app/features) (e.g., `auth`, `sessions`, `groups`, `leaderboard`, `logs`, `notifications`, `scheduler`). Each domain folder encapsulates its own router, models, schemas, repositories, and services.
* **Async Database Connection**: Uses SQLAlchemy and `asyncpg` to communicate asynchronously with PostgreSQL.
* **FastAPI Lifespan Events**: Spawns background workers and schedulers at application startup and gracefully tears them down on shutdown.

---

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   * Copy `.env.example` to `.env`
   * Fill values for your local environment (database URL, secret key, etc.)

3. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## Docker Setup

To spin up the entire application stack (FastAPI Backend, PostgreSQL DB, and Redis) locally with hot-reloading:
```bash
docker compose up --build -d
```

---

## API & Testing Guides

All additional project documentation is organized inside the [docs/](file:///c:/Users/Admin/Desktop/unjack_app_backend-/docs) directory:
* [cURL Testing Guide](file:///c:/Users/Admin/Desktop/unjack_app_backend-/docs/curl_test_guide.md): Raw `curl` queries for every endpoint.
* [API Testing Guide](file:///c:/Users/Admin/Desktop/unjack_app_backend-/docs/api_testing_guide.md): Comprehensive request and response details.
* [Database Logging Guide](file:///c:/Users/Admin/Desktop/unjack_app_backend-/docs/TEST_GUIDE.md): Structural sequencing and request flows.

Once running, visit `http://localhost:8000/docs` for the interactive Swagger API documentation.

---

## Testing

Run the automated test suite locally:
```bash
pytest
```
