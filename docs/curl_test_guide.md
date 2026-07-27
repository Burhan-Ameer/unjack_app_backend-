# REST API Integration Testing Curl Guide

This document contains a complete list of `curl` commands to manually test all endpoints on the live FastAPI backend server.

---

## 1. Health Probe

### Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

---

## 2. Authentication

### Register User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "testuser@example.com", "password": "strongpassword123"}'
```

### Log In
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "testuser@example.com", "password": "strongpassword123"}'
```

### Refresh JWT Access Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "<YOUR_REFRESH_TOKEN>"}'
```

---

## 3. Sessions (JWT Auth Required)

### Start Session
```bash
curl -X POST "http://localhost:8000/api/v1/sessions/start" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"app_name": "Unjack App", "package": "com.unjack.app", "ttl_seconds": 3600}'
```

### Fetch Session History
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/history" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### Stop Session
```bash
curl -X POST "http://localhost:8000/api/v1/sessions/stop" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

---

## 4. Groups (JWT Auth Required)

### Create Group
```bash
curl -X POST "http://localhost:8000/api/v1/groups/" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Group Alpha"}'
```

### List Groups
```bash
curl -X GET "http://localhost:8000/api/v1/groups/" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### Get Specific Group Details
```bash
curl -X GET "http://localhost:8000/api/v1/groups/1" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### Update Group Name
```bash
curl -X PATCH "http://localhost:8000/api/v1/groups/1" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Group Alpha Pro"}'
```

### Add Another User to Group
```bash
curl -X POST "http://localhost:8000/api/v1/groups/1/add" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"user_id": 2}'
```

### Delete Group
```bash
curl -X DELETE "http://localhost:8000/api/v1/groups/1" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

---

## 5. Leaderboard (JWT Auth Required)

### Get Weekly Leaderboard for a Group
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboard/1/weekly" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### Get Current Weekly Winner of a Group
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboard/1/winner" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```
