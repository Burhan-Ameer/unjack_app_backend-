# Unjack Backend

> A FastAPI-based backend powering **Unjack** — a social accountability and app-blocking app for Gen Z. Handles authentication, focus session tracking, group management, and weekly leaderboards, built with an anti-cheat-first architecture.

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-async-336791?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-cache%20%26%20rate--limit-DC382D?logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/SQLAlchemy-async%20ORM-CC2927" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/status-in%20development-yellow" alt="Status">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License">
</p>

---

## Why Unjack

Most focus/app-blocking apps rely on self-reported honesty. Unjack adds a **social accountability layer** — group leaderboards, weekly winners, and a Redis-backed start/stop session handshake — so focus time is verified, not just logged.

---

## Features

* **Authentication** — JWT-based auth with registration, login, token refresh, and Argon2 password hashing.
* **Sessions** — Focus sessions logged via a secure start/stop handshake, staged in Redis before being committed, to prevent leaderboard cheating.
* **Groups** — Create, manage, and join groups (max **60 members** per group, enforced business rule).
* **Leaderboard** — Weekly rankings within groups with automated winner calculation.
* **Cron Job** — Scheduled weekly winner calculation and persistence.
* **Database Logging** — Asynchronous, non-blocking queue-based logging engine capturing tracebacks, request IDs, and user IDs to PostgreSQL.
* **Rate Limiting** — Redis-backed sliding window limiter (15 requests / 15 minutes on auth endpoints).

---

## Architecture

Built using a **Modular Clean Router Structure (MCRS)** — each feature domain owns its router, models, schemas, repositories, and services.

```mermaid
flowchart TD
    Client[Client / Mobile App] -->|HTTPS| API[FastAPI App]

    subgraph API_Layer["FastAPI - Feature Modules"]
        Auth[auth]
        Sessions[sessions]
        Groups[groups]
        Leaderboard[leaderboard]
        Logs[logs]
        Notifications[notifications]
        Scheduler[scheduler]
    end

    API --> Auth
    API --> Sessions
    API --> Groups
    API --> Leaderboard

    Auth -->|rate limit check| Redis[(Redis)]
    Sessions -->|start/stop handshake| Redis
    Leaderboard -->|weekly cron trigger| Scheduler

    Auth -->|async SQLAlchemy| DB[(PostgreSQL)]
    Sessions -->|commit verified session| DB
    Groups --> DB
    Leaderboard -->|persist winners| DB

    Logs -->|async queue worker| DB
    API -.->|errors / traces| Logs

    Scheduler -->|weekly job| Leaderboard
```

**Flow highlights:**
- Sessions are staged in Redis during the start/stop handshake, then committed to Postgres only once verified — this is what prevents leaderboard manipulation.
- The logging engine runs as a background async queue worker (via FastAPI lifespan events) so log writes never block request handling.
- The scheduler spins up at app startup and handles weekly winner calculation as a cron-style background job.

---

## Tech Stack

| Layer              | Technology                          |
|---------------------|--------------------------------------|
| API Framework        | FastAPI                             |
| Language              | Python 3.11+                        |
| Database              | PostgreSQL (async via `asyncpg`)    |
| ORM                    | SQLAlchemy (async)                  |
| Migrations            | Alembic                             |
| Cache / Rate Limiting | Redis                               |
| Auth                    | JWT + Argon2                        |
| Background Jobs      | APScheduler / FastAPI lifespan tasks|
| Containerization    | Docker Compose                      |
| Testing                | Pytest                              |

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

To spin up the entire application stack (FastAPI backend, PostgreSQL, and Redis) locally with hot-reloading:

```bash
docker compose up --build -d
```

---

## API Documentation

Once running, visit `http://localhost:8000/docs` for the interactive Swagger UI.

<!--
Add a screenshot here once available, e.g.:
![Swagger UI](docs/screenshots/swagger_ui.png)
-->

**Suggested screenshots to add:**
- Swagger UI (`/docs`) overview
- A sample authenticated request in Postman/curl with response
- Leaderboard endpoint response showing a group's weekly ranking

---

## API & Testing Guides

Additional project documentation lives in [`docs/`](./docs):

* [cURL Testing Guide](./docs/curl_test_guide.md) — raw `curl` queries for every endpoint.
* [API Testing Guide](./docs/api_testing_guide.md) — comprehensive request/response details.
* [Database Logging Guide](./docs/TEST_GUIDE.md) — structural sequencing and request flows.

---

## Testing

Run the automated test suite locally:

```bash
pytest
```

---

## Roadmap

- [ ] Push notifications for group activity
- [ ] Public API rate-limit dashboard
- [ ] Deployment guide (Azure Container Apps)

---

## License

MIT — see [LICENSE](./LICENSE) for details.