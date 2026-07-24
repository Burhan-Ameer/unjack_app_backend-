# Changelog — Audit Fixes (June 28, 2026)

## Fixes Applied

### 1. Duplicate Alembic Migration (Critical)
**File:** `alembic/versions/8c15a1f281df_last_active_column_added.py` — **deleted**
- Migrations `0002` and `8c15a1f281df` both added the same `last_active` column to `streaks`.
- The second auto-generated migration would crash `alembic upgrade head`.

### 2. Missing Admin Authorization on Group Operations
**Files:** `features/groups/service.py`, `features/groups/router.py`
- `delete_group` — now requires the requester to be a group admin (`PermissionError` → 403).
- `add_user_to_group` — now requires the requester to be a group admin (`PermissionError` → 403).

### 3. `User.last_active_at` Never Updated
**File:** `features/auth/service.py`
- `authenticate_user` now sets `user.last_active_at = datetime.utcnow()` and commits on every successful login.

### 4. Redundant TTL Validation
**File:** `features/sessions/service.py`
- Removed duplicate TTL bounds check (1–21600s) that was already enforced by the Pydantic schema validator.

### 5. `SessionResponse.blocked_date` Not Nullable in Schema
**File:** `features/sessions/schemas.py`
- Changed `blocked_date: datetime` → `blocked_date: Optional[datetime] = None` to match the model's `nullable=True`.

### 6. Pydantic v1 Deprecated API → v2
**Files:** `features/sessions/schemas.py`, `features/groups/schemas.py`, `features/sessions/service.py`
- Replaced `Config.from_attributes = True` with `model_config = {"from_attributes": True}`.
- Replaced `SessionResponse.from_orm(s)` with `SessionResponse.model_validate(s)`.

### 7. Missing `groups/__init__.py`
**File:** `features/groups/__init__.py` — **created**
- Made the groups module a proper Python package.

### 8. Redis Connection Leak on Shutdown
**File:** `main.py`, `dependencies.py`
- `main.py` shutdown event now calls `await redis_client.close()` to clean up the Redis connection pool.

### 9. Unnecessary Scheduler Pruning Job Removed
**Files:** `features/scheduler/scheduler.py`, `features/scheduler/jobs.py`
- Removed `prune_expired_rate_limit_buckets` job (ran every 30 min for ~2-min TTL rows).
- Removed the unused `RateLimitBucket` import and `delete` import from jobs.

### 10. Leaderboard Endpoints Missing Group Membership Check
**File:** `features/leaderboard/router.py`
- Added `_verify_group_membership()` helper — both `/weekly` and `/winner` now reject non-members with 403.

### 11. Blocking FCM Call in Async Context
**File:** `features/notifications/service.py`
- Wrapped `messaging.send()` in `loop.run_in_executor()` to avoid blocking the event loop.

### 12. `FakeRedis` Missing `incrby` in Tests
**File:** `tests/conftest.py`
- Added `incrby` method to `FakeRedis` so the rate limiter lazy-seeding path doesn't crash if exercised.

### 13. `Group.highest_streak` / `top_user_id` Never Written
**Files:** `features/groups/repository.py`, `features/sessions/service.py`, `dependencies.py`
- Added `get_groups_by_user(user_id)` and `update_group_streak(group_id, streak, user_id)` to `GroupRepository`.
- `SessionService` now accepts `GroupRepository`; `stop_session` updates `Group.highest_streak` and `Group.top_user_id` when the user's current streak exceeds the group's stored value.

### 14. `User.is_active` Partial Index Unused by Queries
**File:** `features/leaderboard/repository.py`
- Added `User.is_active == True` filter to `get_group_focus_times()` so the weekly cron job and leaderboard endpoints exclude inactive users from rankings. The partial index `ix_users_active_only` now serves its intended purpose.

## Remaining (Not in Scope)
- Stats API endpoints (`/stats/me`, `/stats/{user_id}`)
- CI/CD pipeline (GitHub Actions)
