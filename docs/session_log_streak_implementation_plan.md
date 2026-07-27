# Focus Streak Calculation: Implementation Plan

This document details the plan to implement the **Focus Streak Calculation** logic inside the session logging service. This ensures that every time a user logs a focus session (`POST /api/v1/sessions/`), their productivity metrics (current streak, longest streak, total focus time, and last active date) are updated and persisted.

---

## 🛠️ Proposed Changes

To implement this feature, we need to modify **three** main files:
1. **`app/features/sessions/service.py`**: Retrieve the user's streak, apply the calculation logic, and save it.
2. **`app/dependencies.py`**: Inject `LeaderboardRepository` into `SessionService`.
3. **`tests/test_sessions.py`**: Add integration tests to verify the streak update flow under various conditions (same day, consecutive days, broken streak, etc.).

---

## 1. Dependency Injection Updates
In [app/dependencies.py](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/dependencies.py#L31-L32), we will inject the `LeaderboardRepository` into the `SessionService` instantiation:

```python
def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    leaderboard_repo: LeaderboardRepository = Depends(get_leaderboard_repository)
) -> SessionService:
    return SessionService(session_repo, leaderboard_repo)
```

---

## 2. Streak Update Logic in `SessionService.log_session`
We will update `log_session` in [app/features/sessions/service.py](file:///C:/Users/Admin/Desktop/unjack_app_backend-/app/features/sessions/service.py#L13-L16). 

### Step-by-Step Flow:
1. **Log Session:** Create and persist the `AppSession` as before.
2. **Retrieve Streak:** Fetch the user's `Streak` record using `self.leaderboard_repo.get_streak_by_user(user_id)`.
3. **Initialize Streak (if None):** If the user has no streak record, create one with default values (`current_streak=0`, `longest_streak=0`, `total_focus_time=0`, `last_active=None`).
4. **Update Total Time:** Increment `total_focus_time` by the session duration.
5. **Update Streak & Last Active:**
   * Get today's UTC date (`today = datetime.now(timezone.utc).date()`).
   * Compare `today` with the streak's `last_active` date:
     * **First Active (`last_active` is None):** Set `current_streak = 1` and `last_active = today`.
     * **Same Day (`today == last_active`):** Do not change `current_streak`.
     * **Consecutive Day (`today == last_active + timedelta(days=1)`):** Increment `current_streak` by 1, and set `last_active = today`.
     * **Broken Streak (`today > last_active + timedelta(days=1)`):** Reset `current_streak = 1` and set `last_active = today`.
6. **Update Longest Streak:** If `current_streak > longest_streak`, set `longest_streak = current_streak`.
7. **Commit Changes:** Save the streak record via `self.leaderboard_repo.create_streak()` (for new records) or `self.leaderboard_repo.update_streak()` (for existing ones).

---

## 3. Proposed Code Diffs

### `app/features/sessions/service.py`
```diff
@@ -3,6 +3,8 @@
 from app.features.sessions.repository import SessionRepository
 from app.features.sessions.models import AppSession
 from app.features.sessions.schemas import SessionCreate, SessionResponse
+from app.features.leaderboard.repository import LeaderboardRepository
+from app.features.leaderboard.models import Streak
+from datetime import datetime, timezone, timedelta
 
 logger = logging.getLogger("app.sessions.service")
 
-class SessionService:
-    def __init__(self, session_repo: SessionRepository):
-        self.session_repo = session_repo
-
-    async def log_session(self, user_id: int, session: SessionCreate) -> AppSession:
-        db_session = AppSession(user_id=user_id, **session.model_dump())
-        logger.debug("Persisting session user_id=%s app_name=%s", user_id, session.app_name)
-        return await self.session_repo.create(db_session)
+class SessionService:
+    def __init__(self, session_repo: SessionRepository, leaderboard_repo: LeaderboardRepository):
+        self.session_repo = session_repo
+        self.leaderboard_repo = leaderboard_repo
+
+    async def log_session(self, user_id: int, session: SessionCreate) -> AppSession:
+        # 1. Persist the session
+        db_session = AppSession(user_id=user_id, **session.model_dump())
+        logger.debug("Persisting session user_id=%s app_name=%s", user_id, session.app_name)
+        saved_session = await self.session_repo.create(db_session)
+
+        # 2. Retrieve or initialize user's streak
+        streak = await self.leaderboard_repo.get_streak_by_user(user_id)
+        is_new_streak = False
+        if not streak:
+            streak = Streak(
+                user_id=user_id,
+                current_streak=0,
+                longest_streak=0,
+                total_focus_time=0,
+                last_active=None
+            )
+            is_new_streak = True
+
+        # 3. Update total focus time
+        streak.total_focus_time += session.duration
+
+        # 4. Calculate streak increment
+        today = datetime.now(timezone.utc).date()
+        if streak.last_active is None:
+            streak.current_streak = 1
+            streak.last_active = today
+        elif today == streak.last_active:
+            # Already active today, streak doesn't change
+            pass
+        elif today == streak.last_active + timedelta(days=1):
+            # Consecutive day activity
+            streak.current_streak += 1
+            streak.last_active = today
+        else:
+            # Gap in activity, reset streak
+            streak.current_streak = 1
+            streak.last_active = today
+
+        # 5. Update longest streak
+        if streak.current_streak > streak.longest_streak:
+            streak.longest_streak = streak.current_streak
+
+        # 6. Save streak record
+        if is_new_streak:
+            await self.leaderboard_repo.create_streak(streak)
+        else:
+            await self.leaderboard_repo.update_streak(streak)
+
+        return saved_session
```

---

## 4. Verification Plan

We will add unit/integration tests in [tests/test_sessions.py](file:///C:/Users/Admin/Desktop/unjack_app_backend-/tests/test_sessions.py) to assert:
1. **First Session:** Creates a `Streak` entry with `current_streak = 1` and `longest_streak = 1`.
2. **Multiple Sessions on Same Day:** Increases `total_focus_time` but leaves `current_streak` at `1`.
3. **Consecutive Days:** Increments `current_streak` to `2` and updates `longest_streak` to `2`.
4. **Broken Streak:** If `last_active` is 2 days ago, `current_streak` resets to `1` but `longest_streak` remains `2`.
