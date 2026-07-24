---
name: unjack_context_tracker
description: Onboards agents to the Unjack backend, tracks active features, current backlog, and maintains context across chat sessions.
version: 1.0.0
---

# 🎯 Unjack Backend Context Tracker & Developer Journal

Welcome! This is the central context and onboarding repository for the Unjack Backend application. If you are an AI assistant or a new developer starting a session, please review this document to instantly align on project status, directory layout, and active tickets.

> [!IMPORTANT]
> **Instructions for AI Agents:**
> 1. At the start of a new chat session, execute `view_file` on [SKILL.md](file:///C:/Users/Admin/Desktop/unjack_app_backend-/SKILL.md) with `IsSkillFile: true` to load this context.
> 2. Whenever you complete a feature, fix a bug, or plan a new feature, update the **Current Context & Backlog** and **Recent Work Log** sections in this file using the `replace_file_content` or `multi_replace_file_content` tools. Do not let the log grow excessively; prune old logs or archive them if needed.

---

## 🏗️ Project Architecture Map

The project is built as a modular monolith following the **Modular Clean Router Structure (MCRS)** under the [app/features/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features) directory. Each domain encapsulates its own router, models, service, schemas, and repository.

### Directory Layout
*   [app/features/auth/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/auth) - JWT authentication, registration, refresh logic, and Redis sliding-window rate limiting.
*   [app/features/sessions/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/sessions) - App focus logging and active session management.
*   [app/features/groups/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/groups) - Social groups management (replaces individual friends).
*   [app/features/leaderboard/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/leaderboard) - Streaks, weekly stats, and leaderboard rankings.
*   [app/features/scheduler/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/scheduler) - APScheduler tasks (triggers weekly score resets and FCM pushes).
*   [app/features/notifications/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/notifications) - Firebase Cloud Messaging (FCM) wrappers.
*   [app/core/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/core) - Project configuration, settings, security utils.
*   [app/db/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/db) - Session builders, database engine setups.
*   [tests/](file:///C:/Users/Admin/Desktop/unjack_app_backend-/tests) - Integration tests for auth, groups, sessions, and scheduler.

---

## 🚦 Implementation Roadmap

### ✅ Completed Features
1.  **Core Scaffolding:** FastAPI app with SQLAlchemy (asyncpg/asyncio), Alembic migrations, and local PostgreSQL container.
2.  **Authentication & Rate Limiting:** JWT sign-in, signup, refresh, and Redis-backed sliding-window rate limiting.
3.  **Groups & Social Features:** Replacement of individual friendship graph with competitive groups.
4.  **Weekly Scheduler:** Cron job running Mondays at 00:05 UTC to aggregate leaderboard scores, award weekly top slots, reset stats, and issue push notifications.
5.  **Focus Streak Calculation:** Session logging automatically increments streaks if logged consecutively, resets if there is a gap, or maintains if logged on the same day.

### ⏳ Current Active Feature (In Progress)
*   **Focus Session Start/Stop Handshake:** Transitioning from client-reported durations to server-validated durations using Redis transient states to prevent leaderboard cheating.
    *   *Reference Plan:* [session_handshake_implementation_plan.md](file:///C:/Users/Admin/Desktop/unjack_app_backend-/session_handshake_implementation_plan.md)

### 📋 Backlog (To Be Done)
1.  **Stats API Endpoints:** Implement `/stats/me` and `/stats/{user_id}` endpoints for focus analytics and top blocked apps.
2.  **GitHub Actions CI/CD Pipeline:** Create `.github/workflows/deploy.yml` for automated test execution and deployment to Azure Container Apps.

---

## 🛠️ Local Developer Commands

### Environment Setup
1.  **Activate Virtual Environment:**
    ```powershell
    .\venv\Scripts\Activate.ps1
    ```
2.  **Start Database Containers:**
    ```powershell
    docker-compose up -d
    ```
3.  **Run Migrations:**
    ```powershell
    alembic upgrade head
    ```
4.  **Start Dev Server:**
    ```powershell
    uvicorn app.main:app --reload
    ```
5.  **Run Tests:**
    ```powershell
    .\venv\Scripts\pytest
    ```

---

## 📓 Recent Work Log

### 2026-06-13 (Current Session)
*   **Created Skill File:** Initialized [SKILL.md](file:///C:/Users/Admin/Desktop/unjack_app_backend-/SKILL.md) to serve as a persistent context onboarding skill.
*   **Verified Test Suite:** Ran all unit/integration tests (`13 passed` successfully).
*   **Identified Active Task:** Handshake-based session logging is ready to be implemented next.

---

## 📝 Rules of Engagement for Future Agents

When you pick up this repository:
1.  **Load the Skill:** Start by viewing this file: `SKILL.md` (with `IsSkillFile: true`).
2.  **Acknowledge and Propose:** State the current task you have extracted from the **Current Active Feature** section and describe your plan.
3.  **Perform Work:** Keep code changes clean, maintain the MCRS directory pattern, and ensure tests pass.
4.  **Log Changes:** Before ending the chat session:
    - Update the **Roadmap** sections (mark items as completed, move items to active).
    - Add a bullet point to the **Recent Work Log** detailing what you changed/fixed.
