# Unjack Backend: Implementation Status

This file documents the current development progress of the Unjack Backend application, highlighting what is completed, what has changed from the original plan, and what remains to be implemented.

---

## 🏗️ Structural & Schema Changes (Divergences from Plan)

1.  **Folder Structure Redesign (Domain-Driven)**
    *   *Planned:* A flat `/api/v1/endpoints/` folder with global `models.py` and `schemas/` directories.
    *   *Actual:* Organized via a **Modular Clean Router Structure (MCRS)** under `app/features/`. Each domain (e.g., `auth`, `sessions`, `groups`, `leaderboard`) encapsulates its own router, models, schemas, repository, and service.
2.  **Social Graph: Friendships -> Groups**
    *   *Planned:* A 1-to-1 `friendships` table.
    *   *Actual:* Replaced entirely with a **Groups** system (`groups` and `group_members` tables). Users join groups and compete/compare stats within those groups instead of adding individual friends.
3.  **Database Primary Keys**
    *   *Planned:* `UUID` for all tables.
    *   *Actual:* `Integer` (auto-incrementing) is being used across all implemented models.
4.  **Argon2 Hashing**
    *   *Planned:* Hashing with `bcrypt`.
    *   *Actual:* Hashing with `argon2` (a more secure alternative).

---

## ✅ Implemented Items

*   **Core Project Scaffolding:** FastAPI application is set up with Alembic, SQLAlchemy, and asyncpg.
*   **Local Containerized Database:** Added a local PostgreSQL container service directly in the Docker setup, configuring internal networking for both Postgres and Redis.
*   **Authentication Feature (`app/features/auth`):**
    *   `User` database model (including `avatar_url` and `fcm_token`).
    *   JWT registration, login, and token refresh endpoints.
    *   Redis sliding window rate limiting.
*   **App Sessions Feature (`app/features/sessions`):**
    *   `AppSession` model to track focus sessions (duration, app name, blocked date).
    *   Secure **Start/Stop Handshake Flow** (Redis transient state) to prevent leaderboard cheating.
    *   Router endpoints to start active session, stop session, and retrieve history.
*   **Groups Feature (`app/features/groups`):**
    *   Models for `Group` and `GroupMember`, supporting many-to-many relationship with admin privileges and top user tracking.
*   **Leaderboard & Scheduler Feature (`app/features/leaderboard` & `app/features/scheduler`):**
    *   `Streak` and `WeeklyStat` database models.
    *   `last_active` column added to `Streak` model (and database migration generated).
    *   APScheduler task setup running Monday at 00:05 UTC to aggregate weekly scores and persist weekly rankings.
    *   Firebase push notification service to alert weekly winners.
*   **Focus Streak Calculation Logic:**
    *   `SessionService.stop_session` updates the user's `Streak` table metrics (current streak, longest streak, total focus time, and last active date) when a session is completed and logged.

---

## ❌ Unimplemented / Remaining Items

*   **Stats API Endpoints:**
    *   The planned `/stats/me` and `/stats/{user_id}` endpoints for focus analytics and top blocked apps have not been implemented.
*   **CI/CD Deployment Pipeline:**
    *   The GitHub Actions workflow (`.github/workflows/deploy.yml`) for running tests and building/deploying the Docker image to Azure is missing.
