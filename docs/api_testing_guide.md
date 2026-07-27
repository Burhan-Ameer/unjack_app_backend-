# Unjack Backend API Testing Guide

This guide contains complete **cURL commands** and **Postman request bodies** for testing all the implemented backend features.

By default, the server is assumed to run locally at `http://localhost:8000`.

---

## 📋 Table of Contents
1. [Health Checks](#1-health-checks)
2. [Authentication (`/auth`)](#2-authentication-auth)
3. [App Sessions (`/sessions`)](#3-app-sessions-sessions)
4. [Groups (`/groups`)](#4-groups-groups)
5. [Leaderboard (`/leaderboard`)](#5-leaderboard-leaderboard)

---

## 1. Health Checks

### 🟢 Liveness Check
Checks if the API process is running.
* **Method:** `GET`
* **URL:** `http://localhost:8000/api/v1/health/live`
* **cURL:**
  ```bash
  curl -X GET "http://localhost:8000/api/v1/health/live"
  ```

### 🟢 Full Health Check
Probes database availability.
* **Method:** `GET`
* **URL:** `http://localhost:8000/api/v1/health`
* **cURL:**
  ```bash
  curl -X GET "http://localhost:8000/api/v1/health"
  ```

---

## 2. Authentication (`/auth`)

### 👤 Register User
* **Method:** `POST`
* **URL:** `http://localhost:8000/api/v1/auth/register`
* **cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/register" \
       -H "Content-Type: application/json" \
       -d '{
         "username": "burhan",
         "email": "burhan@test.com",
         "password": "mySecurePassword123"
       }'
  ```

### 🔑 Login (Get Tokens)
* **Method:** `POST`
* **URL:** `http://localhost:8000/api/v1/auth/login`
* **cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/login" \
       -H "Content-Type: application/json" \
       -d '{
         "email": "burhan@test.com",
         "password": "mySecurePassword123"
       }'
  ```
* **Postman Body:** Choose `raw` -> `JSON`:
  ```json
  {
    "email": "burhan@test.com",
    "password": "mySecurePassword123"
  }
  ```
> [!NOTE]  
> Copy the returned `access_token` and `refresh_token` from this response. Use the `access_token` as a Bearer token for subsequent requests.

### 🔄 Refresh Token
* **Method:** `POST`
* **URL:** `http://localhost:8000/api/v1/auth/refresh`
* **cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
       -H "Content-Type: application/json" \
       -d '{
         "refresh_token": "YOUR_REFRESH_TOKEN_HERE"
       }'
  ```

---

## 3. App Sessions (`/sessions`)

All endpoints below require a header: `Authorization: Bearer <your_access_token>`.

### 📱 Log a Session
Logs focus activity and updates user streaks.
* **Method:** `POST`
* **URL:** `http://localhost:8000/api/v1/sessions/`
* **cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/sessions/" \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
       -d '{
         "app_name": "Instagram",
         "package": "com.instagram.android",
         "duration": 3600,
         "blocked_date": "2026-06-13T10:00:00Z"
       }'
  ```
* **Postman Body:** Choose `raw` -> `JSON`:
  ```json
  {
    "app_name": "Instagram",
    "package": "com.instagram.android",
    "duration": 3600,
    "blocked_date": "2026-06-13T10:00:00Z"
  }
  ```

### 📜 Get Session History
* **Method:** `GET`
* **URL:** `http://localhost:8000/api/v1/sessions/history`
* **cURL:**
  ```bash
  curl -X GET "http://localhost:8000/api/v1/sessions/history" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
  ```

---

## 4. Groups (`/groups`)

All endpoints below require a header: `Authorization: Bearer <your_access_token>`.

### 👥 Create a Group
* **Method:** `POST`
* **URL:** `http://localhost:8000/api/v1/groups/`
* **cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/groups/" \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
       -d '{
         "name": "Focus Champions"
       }'
  ```
* **Postman Body:** Choose `raw` -> `JSON`:
  ```json
  {
    "name": "Focus Champions"
  }
  ```

### 👥 List All Groups
* **Method:** `GET`
* **URL:** `http://localhost:8000/api/v1/groups/`
* **cURL:**
  ```bash
  curl -X GET "http://localhost:8000/api/v1/groups/" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
  ```

### 👥 Get a Specific Group
* **Method:** `GET`
* **URL:** `http://localhost:8000/api/v1/groups/1`
* **cURL:**
  ```bash
  curl -X GET "http://localhost:8000/api/v1/groups/1" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
  ```

### 👥 Update a Group (Admins only)
* **Method:** `PATCH`
* **URL:** `http://localhost:8000/api/v1/groups/1`
* **cURL:**
  ```bash
  curl -X PATCH "http://localhost:8000/api/v1/groups/1" \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
       -d '{
         "name": "Super Focusers"
       }'
  ```

### 👥 Add User to Group
* **Method:** `POST`
* **URL:** `http://localhost:8000/api/v1/groups/1/add`
* **cURL:**
  ```bash
  curl -X POST "http://localhost:8000/api/v1/groups/1/add" \
       -H "Content-Type: application/json" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
       -d '{
         "user_id": 2
       }'
  ```

### 👥 Delete Group
* **Method:** `DELETE`
* **URL:** `http://localhost:8000/api/v1/groups/1`
* **cURL:**
  ```bash
  curl -X DELETE "http://localhost:8000/api/v1/groups/1" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
  ```

---

## 5. Leaderboard (`/leaderboard`)

All endpoints below require a header: `Authorization: Bearer <your_access_token>`.

### 🏆 Get Weekly Leaderboard for Group
* **Method:** `GET`
* **URL:** `http://localhost:8000/api/v1/leaderboard/1/weekly`
* **cURL:**
  ```bash
  curl -X GET "http://localhost:8000/api/v1/leaderboard/1/weekly" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
  ```

### 🏆 Get Weekly Winner for Group
* **Method:** `GET`
* **URL:** `http://localhost:8000/api/v1/leaderboard/1/winner`
* **cURL:**
  ```bash
  curl -X GET "http://localhost:8000/api/v1/leaderboard/1/winner" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
  ```
