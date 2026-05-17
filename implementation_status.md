# Unjack Backend: Implementation Status

Based on the original "Unjack Backend — Full Implementation Plan" and the current state of the codebase, here is a detailed breakdown of what has been implemented, what has changed, and what remains unimplemented.

## 🏗️ Structural & Schema Changes (Divergences from Plan)

1. **Folder Structure Redesign (Domain-Driven)**
   - *Planned:* A flat `/api/v1/endpoints/` folder with global `models.py` and `schemas/` directories.
   - *Actual:* Migrated to a **Modular Clean Router Structure (MCRS)** organized by domain under `app/features/` (e.g., `app/features/auth`, `app/features/sessions`). Each feature encapsulates its own `router.py`, `models.py`, `schemas.py`, `repository.py`, and `service.py`.
2. **Social Graph: Friendships -> Groups**
   - *Planned:* A 1-to-1 `friendships` table (`requester_id`, `addressee_id`).
   - *Actual:* Replaced entirely with a **Groups** system (`groups` and `group_members` tables). Users join groups instead of adding individual friends.
3. **Database Primary Keys**
   - *Planned:* `UUID` for all tables.
   - *Actual:* `Integer` (auto-incrementing) is being used across all implemented models.

---

## ✅ Implemented Items

* **Core Project Scaffolding:** FastAPI application is set up with Alembic, SQLAlchemy, and asyncpg.
* **Authentication Feature (`app/features/auth`):**
  * `User` database model is implemented (with `id`, `username`, `email`, `hashed_password`, `is_active`, `last_active_at`).
  * JWT authentication routing and services are set up.
* **App Sessions Feature (`app/features/sessions`):**
  * `AppSession` model is implemented to track `app_name`, `package`, `duration`, and `blocked_date`.
  * Associated router and business logic are connected to the main API router.
* **Groups Feature (`app/features/groups`):**
  * Models for `Group` and `GroupMember` are implemented, supporting a many-to-many relationship with admin privileges and top user tracking.
* **Health Check Endpoint (`app/features/health`):**
  * Fully implemented and exposed on the API.
* **Docker Support:**
  * `Dockerfile` and `docker-compose.yml` are present and ready for local containerized development.

---

## ❌ Unimplemented / Incomplete Items

* **Leaderboard & Weekly Stats (`app/features/leaderboard`):**
  * The `Streak` and `WeeklyStat` models are currently **commented out** in `models.py`.
  * The `/leaderboard` router is **commented out** in `app/api/v1/router.py`.
* **Stats Endpoints:**
  * The planned `/stats/me` and `/stats/{user_id}` endpoints for retrieving focus metrics and top blocked apps are missing.
* **Winner of the Week Cron Job:**
  * The APScheduler job meant to run every Monday at 00:05 UTC to aggregate focus time, rank users within groups, and declare winners is not implemented.
* **Missing User Fields:**
  * The `User` model currently lacks the `avatar_url` and `fcm_token` (Firebase Cloud Messaging) columns specified in the plan.
* **Push Notifications (FCM):**
  * While a `notifications/service.py` skeleton exists, the actual integration to send "You won this week!" alerts via Firebase is unimplemented.
* **Admin Module (`app/features/admin`):**
  * The directory exists but is currently completely empty.
* **CI/CD Deployment Pipeline:**
  * The GitHub Actions workflow (`.github/workflows/deploy.yml`) for Azure Container Apps deployment is not yet present.
