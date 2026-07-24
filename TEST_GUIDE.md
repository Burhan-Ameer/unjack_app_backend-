# Test Guide — Edge Cases for All Features

> Covers all endpoints, background jobs, and global concerns.

---

## Table of Contents

- [1. Auth (`/api/v1/auth`)](#1-auth-apiv1auth)
  - [Register `POST /register`](#register-post-register)
  - [Login `POST /login`](#login-post-login)
  - [Refresh `POST /refresh`](#refresh-post-refresh)
- [2. Sessions (`/api/v1/sessions`)](#2-sessions-apiv1sessions)
  - [Start `POST /start`](#start-post-start)
  - [Stop `POST /stop`](#stop-post-stop)
  - [History `GET /history`](#history-get-history)
- [3. Groups (`/api/v1/groups`)](#3-groups-apiv1groups)
  - [Create `POST /`](#create-post-)
  - [List `GET /`](#list-get-)
  - [Get `GET /{id}`](#get-get-id)
  - [Update `PATCH /{id}`](#update-patch-id)
  - [Delete `DELETE /{id}`](#delete-delete-id)
  - [Add Member `POST /{id}/add`](#add-member-post-idadd)
- [4. Leaderboard (`/api/v1/leaderboard`)](#4-leaderboard-apiv1leaderboard)
  - [Weekly `GET /{group_id}/weekly`](#weekly-get-group_idweekly)
  - [Winner `GET /{group_id}/winner`](#winner-get-group_idwinner)
- [5. Scheduler (Background Jobs)](#5-scheduler-background-jobs)
  - [Weekly Winner Calculation](#weekly-winner-calculation)
- [6. Health (`/api/v1/health`)](#6-health-apiv1health)
  - [Liveness `GET /health/live`](#liveness-get-healthlive)
  - [Health `GET /health`](#health-get-health)
- [7. Global Edge Cases](#7-global-edge-cases)

---

## 1. Auth (`/api/v1/auth`)

### Register `POST /register`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 1.1 | Valid registration | POST with `username`, `email`, `password` | `200` with `user_id` |
| 1.2 | Duplicate username | Register user A, then register user B with same username | `400` "User already exists" |
| 1.3 | Duplicate email | Register user A, then register user B with same email | `400` "User already exists" |
| 1.4 | Missing password | POST without `password` field | `422` |
| 1.5 | Missing username | POST without `username` field | `422` |
| 1.6 | Missing email | POST without `email` field | `422` |
| 1.7 | Empty username `""` | POST with `username: ""` | `422` |
| 1.8 | Very long username (256+ chars) | POST with 256-char username | `422` or succeeds (depends on schema — no length validator currently) |
| 1.9 | Rate limit exceeded | Send 16 register requests in 60 seconds | `429` "Too many requests" |
| 1.10 | Concurrent duplicate registration | Fire 2 register requests simultaneously with same email | One returns `200`, other returns `400` |
| 1.11 | Special characters in username | `username: "<script>alert(1)</script>"` | `200` — stored as-is (frontend must sanitize on display) |

### Login `POST /login`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 1.12 | Correct credentials | POST with registered email + correct password | `200` with `access_token`, `refresh_token`, `token_type` |
| 1.13 | Wrong password | POST with correct email + wrong password | `401` "Invalid credentials" |
| 1.14 | Non-existent email | POST with unregistered email | `401` "Invalid credentials" (same message — no user enumeration) |
| 1.15 | Empty password | POST without `password` | `422` |
| 1.16 | Rate limited | 16 login requests in 60s | `429` |
| 1.17 | Inactive user login | Set `user.is_active = False`, try to login | Currently allowed — `authenticate_user` doesn't check `is_active` |
| 1.18 | `last_active_at` updated | Login, then check DB | `User.last_active_at` is updated to current timestamp (Fix #3) |

### Refresh `POST /refresh`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 1.19 | Valid refresh token | Login, use `refresh_token` from response | `200` with new token pair |
| 1.20 | Expired refresh token | Use a token with `exp` older than 7 days | `401` "Token expired" |
| 1.21 | Access token used as refresh | Login, send `access_token` where `refresh_token` expected | `401` "Invalid token type" |
| 1.22 | Tampered token | Send `refresh_token: "garbage"` | `401` "Could not validate credentials" |
| 1.23 | Refresh for deleted user | Register → login → delete user from DB → refresh | `401` "User not found" |
| 1.24 | Rate limited | 16 refresh requests in 60s | `429` |

---

## 2. Sessions (`/api/v1/sessions`)

### Start `POST /start`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 2.1 | Valid session start | POST with `app_name`, `package` | `200` with `status: "started"`, `start_time`, `ttl_seconds: 14400` |
| 2.2 | Already active session | Start session → start another without stopping | `400` "You already have an active focus session running" |
| 2.3 | No `ttl_seconds` provided | POST without `ttl_seconds` | `200` — defaults to 14400 (4h) |
| 2.4 | Custom TTL = 1 second | POST with `ttl_seconds: 1` | `200` — session auto-expires after 1s |
| 2.5 | Custom TTL = 21600 (6h max) | POST with `ttl_seconds: 21600` | `200` |
| 2.6 | Custom TTL = 0 | POST with `ttl_seconds: 0` | `422` — "ttl_seconds must be positive" |
| 2.7 | Custom TTL = 21601 (exceeds max) | POST with `ttl_seconds: 21601` | `422` — "cannot exceed 6 hours" |
| 2.8 | Custom TTL = -1 | POST with `ttl_seconds: -1` | `422` — "must be positive" |
| 2.9 | Empty `app_name` | POST with `app_name: ""` | `422` |
| 2.10 | Empty `package` | POST with `package: ""` | `422` |
| 2.11 | Missing JWT | POST without `Authorization` header | `401` |
| 2.12 | Redis is down | Stop Redis, try to start session | `500` — session service uses Redis directly |

### Stop `POST /stop`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 2.13 | Valid stop | Start → wait → stop | `200` with `session_id`, `duration` |
| 2.14 | No active session | POST `/stop` without starting | `400` "No active focus session found or it has expired" |
| 2.15 | Session expired (TTL elapsed) | Start with `ttl_seconds: 1`, wait 2s, stop | `400` — Redis key auto-deleted |
| 2.16 | Duration < 10 seconds | Start → stop after 5s | `400` "Focus session was too short" — Redis key deleted |
| 2.17 | Duration = exactly 10 seconds | Start → stop after 10s | `200` — boundary passes |
| 2.18 | First session ever (no streak) | New user starts/stops | `200` — `Streak` record created with `current_streak=1` |
| 2.19 | Consecutive day session | Day 1 session → Day 2 session | `200` — `current_streak` increments to 2 |
| 2.20 | Same day second session | 2 sessions on same day | `current_streak` unchanged, `total_focus_time` increases |
| 2.21 | Session after gap (missed day) | Day 1 → skip Day 2 → Day 3 session | `current_streak` resets to 1, `longest_streak` preserved |
| 2.22 | Group highest_streak updated | User in group, new streak=5 > group record=3 | `Group.highest_streak=5`, `top_user_id=user.id` (Fix #13) |
| 2.23 | Group highest_streak unchanged | User streak=2 ≤ group record=10 | Group columns unchanged (Fix #13) |
| 2.24 | User in 0 groups | Solo user stops session | No crash — group update loop is a no-op (Fix #13) |
| 2.25 | User in multiple groups | User belongs to Group A (record=1) and B (record=10) | Only A's record updated, B unchanged (Fix #13) |
| 2.26 | Streak reset doesn't overwrite group record | User had streak=5 (group record=5), resets to 1 | Group stays at `highest_streak=5` (Fix #13) |

### History `GET /history`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 2.27 | User has 0 sessions | GET `/history` | `200` with `sessions: []` |
| 2.28 | User has 100+ sessions | Create 100 sessions, GET `/history` | `200` with all 100 — no pagination implemented |
| 2.29 | Another user's sessions | User A creates sessions, User B fetches history | User B sees only their own sessions |
| 2.30 | Session with `blocked_date=null` (DB) | Manually insert a session with null `blocked_date` | `200` — schema accepts `Optional[datetime]` (Fix #5) |

---

## 3. Groups (`/api/v1/groups`)

### Create `POST /`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 3.1 | Valid name | POST with `{"name": "Study Group"}` | `201` with group data, creator is admin member |
| 3.2 | Duplicate name | Create "Test", then create "Test" again | `400` "Group with name 'Test' already exists" |
| 3.3 | Name with only spaces `"   "` | POST with `{"name": "   "}` | `422` "name must be non-empty string" |
| 3.4 | Name < 2 chars `"A"` | POST with `{"name": "A"}` | `422` "name must be at least 2 characters long" |
| 3.5 | Name = exactly 2 chars `"AB"` | POST with `{"name": "AB"}` | `201` — boundary |
| 3.6 | Empty body `{}` | POST with `{}` | `422` — name required |

### List `GET /`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 3.7 | No groups exist | GET `/groups/` | `200` with `[]` |
| 3.8 | 50 groups exist | Create 50 groups, then list | `200` with all 50 — no pagination |

### Get `GET /{id}`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 3.9 | Valid group_id | GET `/groups/1` | `200` with group + members |
| 3.10 | Non-existent group_id | GET `/groups/99999` | `404` |
| 3.11 | Negative group_id | GET `/groups/-1` | `404` or `422` |
| 3.12 | String group_id | GET `/groups/abc` | `422` |

### Update `PATCH /{id}`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 3.13 | Admin user, valid name | Admin PATCH with `{"name": "New Name"}` | `200` with updated group |
| 3.14 | Non-admin member | Non-admin PATCH | `403` "Only group administrators can change the group name" |
| 3.15 | Name already taken by other group | Group A named "Foo", Group B tries to rename to "Foo" | `400` "Group with name 'Foo' already exists" |
| 3.16 | Admin updates to same name | Admin sets same name | `200` (passes — checks other groups only) |
| 3.17 | Non-member user | User not in group tries to update | `403` (no membership → not admin) |
| 3.18 | Deleted group | PATCH after DELETE | `404` |
| 3.19 | Empty name `{"name": ""}` | PATCH with empty name | `422` |
| 3.20 | Null name `{"name": null}` | PATCH with null | `422` or `200` (field is Optional — validator runs only if value is not None) |

### Delete `DELETE /{id}`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 3.21 | Admin deletes group | Admin DELETE | `204` No Content (Fix #2) |
| 3.22 | Non-admin member deletes | Non-admin DELETE | `403` "Only group administrators can delete the group" (Fix #2) |
| 3.23 | Non-member deletes | User not in group DELETES | `403` (Fix #2) |
| 3.24 | Non-existent group | DELETE `/groups/99999` | `404` |
| 3.25 | Group with members | Delete group that has 10 members | `204` — `ondelete="CASCADE"` cleans up `GroupMember` rows |

### Add Member `POST /{id}/add`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 3.26 | Admin adds existing user | Admin POST with `{"user_id": 5}` | `201` with membership data (Fix #2) |
| 3.27 | Non-admin tries to add | Non-admin POST | `403` "Only group administrators can add members" (Fix #2) |
| 3.28 | Non-existent user_id | POST with `user_id: 99999` | `500` — FK constraint fails on commit (unhandled `IntegrityError` in try/except — falls to generic `Exception` handler) |
| 3.29 | Duplicate membership | Add user, then add same user again | `400` "User already in group" |
| 3.30 | Add to non-existent group | POST `/groups/99999/add` | `400` "Group not found" |
| 3.31 | Missing `user_id` in body | POST with `{}` | `422` |

---

## 4. Leaderboard (`/api/v1/leaderboard`)

### Weekly `GET /{group_id}/weekly`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 4.1 | Group with sessions this week | Create group, log sessions for members | `200` with ranked entries, `total_time` > 0 |
| 4.2 | No sessions this week | Members with no sessions | `200` with `entries` — all have `total_time: 0` |
| 4.3 | Non-member tries to access | User not in group | `403` "You are not a member of this group" (Fix #10) |
| 4.4 | Non-existent group | GET `/leaderboard/99999/weekly` | `404` |
| 4.5 | Member is inactive | Set `is_active=False`, log session | Excluded from results (Fix #14) |
| 4.6 | All members inactive | Set all group members `is_active=False` | `200` with empty `entries` (Fix #14) |
| 4.7 | Sessions span UTC midnight | Session starts at 23:59 UTC, ends at 00:01 UTC | `blocked_date` determines the week boundary |
| 4.8 | Tie — two members same total_time | Create exact same duration for 2 users | Both appear, ranked 1 and 2 (no tie-handling) |

### Winner `GET /{group_id}/winner`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 4.9 | Winner with time > 0 | Member has sessions this week | `200` with winner data |
| 4.10 | No sessions (all total_time=0) | Group members, no sessions | `404` "No winner found for this group yet" |
| 4.11 | Non-member | User not in group | `403` (Fix #10) |
| 4.12 | Non-existent group | GET `/leaderboard/99999/winner` | `404` |
| 4.13 | All members inactive | All members `is_active=False` | `404` — empty entries (Fix #14) |
| 4.14 | Tie for first | 2 members with equal max time | First in query result wins (no tie-breaker) |

---

## 5. Scheduler (Background Jobs)

### Weekly Winner Calculation (runs Thu 01:05 UTC)

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 5.1 | Single group, 2 members with sessions | Set up group with sessions from last week | Both get `WeeklyStat` rows, winner gets FCM push |
| 5.2 | Multiple groups | Set up 3 groups with sessions | Each group processed independently — all get `WeeklyStat` rows |
| 5.3 | Group with 0 members | Create empty group | Skipped — no crash |
| 5.4 | Winner has no FCM token | Winner's `fcm_token` is null | `WeeklyStat` saved, push skipped gracefully |
| 5.5 | FCM push fails (invalid token) | Winner has garbage `fcm_token` | `WeeklyStat` committed, push failure logged, no crash |
| 5.6 | All members inactive | All members `is_active=False` | No `WeeklyStat` rows created (Fix #14) |
| 5.7 | `week_start_date` not provided | Call without argument | Defaults to last week's Monday |
| 5.8 | DB error during processing | Simulate DB failure mid-way | `rollback()` called, error logged, next groups continue |
| 5.9 | Redis unavailable | Redis down | No impact — scheduler only uses PostgreSQL |

---

## 6. Health (`/api/v1/health`)

### Liveness `GET /health/live`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 6.1 | App running | No auth, GET `/health/live` | `200 {"status": "ok"}` |

### Health `GET /health`

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 6.2 | DB reachable | No auth, GET `/health` | `200 {"status": "ok", "database": "ok"}` |
| 6.3 | DB down | Stop PostgreSQL, GET `/health` | `503` "Database unavailable" |

---

## 7. Global Edge Cases

| # | Test Case | Steps | Expected |
|---|-----------|-------|----------|
| 7.1 | Expired JWT token | Use token with `exp` in the past | `401` "Token expired" |
| 7.2 | Malformed JWT | Send `Authorization: Bearer garbage` | `401` "Could not validate credentials" |
| 7.3 | No Authorization header | Omit header entirely | `401` from OAuth2PasswordBearer |
| 7.4 | Wrong HTTP method | GET on `/auth/register` | `405` Method Not Allowed |
| 7.5 | JSON with extra unknown fields | POST with extra fields in body | Silently ignored (Pydantic default — `extra="ignore"`) |
| 7.6 | SQL injection in string field | `username: "' OR 1=1; --"` | Safe — SQLAlchemy uses parameterized queries |
| 7.7 | XSS payload in username | `username: "<script>alert(1)</script>"` | Stored as-is, returned as JSON — frontend must sanitize |
| 7.8 | Redis connection pool exhaustion | Send 200 concurrent rate-limited requests | Single client with default pool — may queue or fail under extreme load |
| 7.9 | Multiple rate limiters share Redis | Auth + future rate limiters | Each uses its own `key_prefix` — safe |
