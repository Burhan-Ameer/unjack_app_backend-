# Focus Session Start/Stop Handshake: Implementation Plan (Option 3)

This plan outlines the architecture and implementation steps to transition the `/sessions` logging API from client-reported durations to a secure **Start/Stop Handshake Flow** to prevent cheating on leaderboards.

---

## 🏗️ Architecture Design (Redis-Backed Transient State)

Instead of modifying PostgreSQL schemas to track incomplete sessions, we will store active sessions in **Redis**. This keeps the relational database clean, achieves fast performance, and utilizes Redis's TTL (Time-to-Live) to automatically prune abandoned sessions.

```
[Mobile Client]                       [FastAPI Backend]                 [Redis Cache]           [PostgreSQL DB]
       │                                     │                                │                        │
       │─── POST /sessions/start ───────────>│                                │                        │
       │    {app_name, package}              │─── SET active_session:{uid} ──>│ (TTL: 4 Hours)         │
       │                                     │    {start_time, app, pkg}      │                        │
       │<── 200 OK (Session Started) ────────│                                │                        │
       │                                     │                                │                        │
       │    ... User Focuses ...             │                                │                        │
       │                                     │                                │                        │
       │─── POST /sessions/stop ────────────>│                                │                        │
       │                                     │─── GET active_session:{uid} ──>│                        │
       │                                     │<── {start_time, app, pkg} ─────│                        │
       │                                     │                                │                        │
       │                                     │─── Calculate Duration ─────────│                        │
       │                                     │─── Log Completed Session ──────────────────────────────>│
       │                                     │─── Update User Streak ─────────────────────────────────>│
       │                                     │─── DEL active_session:{uid} ──>│                        │
       │<── 201 Created (Logged Session) ────│                                │                        │
```

---

## 🛠️ Step-by-Step Implementation

### 1. Update Session Schemas
We will update [app/features/sessions/schemas.py](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/sessions/schemas.py):
* **`SessionStart`**: Schema for starting a session (inputs: `app_name`, `package`).
* **`SessionResponse`** / **`SessionHistory`**: Remain the same.

### 2. Implement Redis Session Storage in `SessionService`
We will add Redis operations to `SessionService` in [app/features/sessions/service.py](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/sessions/service.py):
* **`start_session`**:
  * Set a key `active_session:{user_id}` in Redis containing a JSON payload: `{"app_name": app_name, "package": package, "start_time": datetime.now(timezone.utc).isoformat()}`.
  * Enforce an expiry TTL (e.g., 4 hours) so that if a user crashes or leaves the app, the session expires instead of running forever.
* **`stop_session`**:
  * Fetch `active_session:{user_id}` from Redis.
  * If it doesn't exist, raise a `ValueError("No active focus session found")`.
  * Calculate `duration = current_utc_time - start_time` (in seconds).
  * Enforce a minimum duration check (e.g., reject sessions under 10 seconds to prevent spam).
  * Save the completed session to the `app_sessions` PostgreSQL table and update the user's focus streak.
  * Delete the active session key from Redis.

### 3. Update Session Endpoints
We will modify [app/features/sessions/router.py](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/sessions/router.py):
* **`POST /api/v1/sessions/start`**: Start a timer.
* **`POST /api/v1/sessions/stop`**: Stop the timer, save the session, and return the logged session details.

---

## 📝 Proposed Code Diffs

### `app/features/sessions/schemas.py`
```python
from pydantic import BaseModel, Field
from datetime import datetime

class SessionStart(BaseModel):
    app_name: str = Field(..., min_length=1)
    package: str = Field(..., min_length=1)
```

### `app/features/sessions/service.py`
```python
import json
import logging
from datetime import datetime, timezone, timedelta
from redis.asyncio import Redis

# ... existing imports ...

class SessionService:
    def __init__(self, session_repo: SessionRepository, leaderboard_repo: LeaderboardRepository, redis: Redis):
        self.session_repo = session_repo
        self.leaderboard_repo = leaderboard_repo
        self.redis = redis
        self.key_prefix = "active_session:"
        self.max_session_seconds = 4 * 60 * 60  # 4 Hours TTL

    async def start_session(self, user_id: int, session: SessionStart) -> dict:
        key = f"{self.key_prefix}{user_id}"
        
        # Optionally reject if a session is already active
        existing = await self.redis.get(key)
        if existing:
            raise ValueError("You already have an active focus session running")

        session_data = {
            "app_name": session.app_name,
            "package": session.package,
            "start_time": datetime.now(timezone.utc).isoformat()
        }
        
        await self.redis.set(key, json.dumps(session_data), ex=self.max_session_seconds)
        logger.info("Started active session for user_id=%s app_name=%s", user_id, session.app_name)
        return {"status": "started", "start_time": session_data["start_time"]}

    async def stop_session(self, user_id: int) -> AppSession:
        key = f"{self.key_prefix}{user_id}"
        
        # 1. Retrieve session data
        data_bytes = await self.redis.get(key)
        if not data_bytes:
            raise ValueError("No active focus session found or it has expired")

        session_data = json.loads(data_bytes.decode("utf-8"))
        start_time = datetime.fromisoformat(session_data["start_time"])
        now = datetime.now(timezone.utc)
        
        # 2. Calculate duration
        duration = int((now - start_time).total_seconds())
        if duration < 10:
            # Delete active session to allow user to retry
            await self.redis.delete(key)
            raise ValueError("Focus session was too short (under 10 seconds). Logging skipped.")

        # 3. Create completed AppSession
        db_session = AppSession(
            user_id=user_id,
            app_name=session_data["app_name"],
            package=session_data["package"],
            duration=duration,
            blocked_date=now
        )
        
        saved_session = await self.session_repo.create(db_session)

        # 4. Calculate user streak updates
        streak = await self.leaderboard_repo.get_streak_by_user(user_id)
        is_new = False
        if not streak:
            streak = Streak(user_id=user_id, current_streak=0, longest_streak=0, total_focus_time=0, last_active=None)
            is_new = True

        streak.total_focus_time += duration
        today = now.date()
        
        if streak.last_active is None:
            streak.current_streak = 1
            streak.last_active = today
        elif today == streak.last_active:
            pass
        elif today == streak.last_active + timedelta(days=1):
            streak.current_streak += 1
            streak.last_active = today
        else:
            streak.current_streak = 1
            streak.last_active = today

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        if is_new:
            await self.leaderboard_repo.create_streak(streak)
        else:
            await self.leaderboard_repo.update_streak(streak)

        # 5. Clean up Redis active session
        await self.redis.delete(key)
        
        logger.info("Session stopped and logged user_id=%s duration=%s seconds", user_id, duration)
        return saved_session
```

### `app/features/sessions/router.py`
```python
@router.post("/start")
async def start_session(
    session: SessionStart, 
    current_user = Depends(get_current_user), 
    service: SessionService = Depends(get_session_service)
):
    try:
        res = await service.start_session(current_user.id, session)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stop")
async def stop_session(
    current_user = Depends(get_current_user), 
    service: SessionService = Depends(get_session_service)
):
    try:
        db_session = await service.stop_session(current_user.id)
        return {"session_id": db_session.id, "duration": db_session.duration}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 🏁 Verification Plan
We will write integration tests in [tests/test_sessions.py](file:///C:/Users/Admin/Desktop/unjack_app_backend-/tests/test_sessions.py) mock-injecting or utilizing the Redis client to test the full lifecycle:
1. `POST /start` successfully starts a session.
2. `POST /start` fails if a session is already active.
3. `POST /stop` successfully calculates duration, updates PostgreSQL, updates user streak, and deletes the Redis key.
4. `POST /stop` fails if no session is active.
