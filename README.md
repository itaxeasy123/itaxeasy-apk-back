# iTaxEasy Mobile APK Backend (Python FastAPI + Alembic + PSQL)

This repository contains the brand new Python backend specifically developed for the **iTaxEasy Mobile APK** (Phase 1). It is modeled on high-performance enterprise structures, utilizing **FastAPI**, **SQLAlchemy** (asynchronous), **Alembic** migrations, and **PostgreSQL**.

---

## 📁 Repository Directory Structure

```
itaxeasy-apk-backend/
├── app/                          # Core Python FastAPI Application
│   ├── api/                      # Routing & Business Modules
│   │   ├── deps.py               # Shared deps (get_current_user JWT guard)
│   │   └── auth/                 # Authentication Module (SRS Module 1 & 2)
│   │       ├── router.py         # Endpoints (firebase, refresh, logout, me)
│   │       ├── schemas.py        # Pydantic Request/Response Validators
│   │       └── service.py        # Firebase verify + JWT/session logic
│   ├── core/                     # Application configurations
│   │   ├── config.py             # Pydantic Settings (.env loader)
│   │   ├── database.py           # Async SQLAlchemy Engine & get_db Dependency
│   │   └── firebase.py           # Firebase Admin SDK init + token verify
│   ├── main.py                   # FastAPI app initiation and entrypoint
│   └── models.py                 # SQLAlchemy models (User, UserSession, OtpLog)
│
├── alembic/                      # Alembic Database Migration Engine
│   ├── env.py                    # Async configuration of alembic schema contexts
│   ├── script.py.mako            # Migration template file
│   └── versions/                 # Versioned migration histories
│       └── a1b2c3d4e5f6_initial_migration.py  # Baseline initial migration
│
├── dev/                          # Local automation scripts
│   ├── start.sh                  # Installs poetry, spins up DB, migrates, starts app
│   └── stop.sh                   # stops and tears down Postgres/Redis containers
│
├── alembic.ini                   # Alembic configuration
├── docker-compose.dev.yml        # Development environment services (PostgreSQL & Redis)
├── pyproject.toml                # Poetry packages configuration
└── poetry.toml                   # In-project virtual environment setting
```

---

## ⚡ Quick Start

You can spin up the local development database, run the async schema migrations, and launch the hot-reloading FastAPI application on port `54110` with a single command!

### 1. Launch Dev Environment
Run the start automation script from the project root:
```bash
./dev/start.sh
```

### 2. View Swagger API Docs
Once started, go to your browser and access:
* **Swagger UI Docs:** [http://localhost:54110/docs](http://localhost:54110/docs)
* **ReDoc Docs:** [http://localhost:54110/redoc](http://localhost:54110/redoc)

### 3. Stop Environment
To stop the database and Redis services:
```bash
./dev/stop.sh
```

---

## 🛠️ Key Technology Stack

* **FastAPI:** Modern, high-performance web framework for Python.
* **SQLAlchemy 2.0 (Async):** Fully asynchronous Object Relational Mapper.
* **Alembic:** Database migration tool for SQLAlchemy.
* **asyncpg:** Asynchronous PostgreSQL driver for asyncio.
* **Firebase Admin SDK:** Verifies the phone-OTP ID token issued on-device.
* **Poetry:** Fast and secure Python packaging and dependency manager.

---

## 🔐 Authentication (Phase 1 — Firebase Phone OTP)

Auth is **phone + Firebase OTP only** (no passwords). The OTP is sent and
verified entirely on-device by the **Firebase Phone Auth SDK** (free via Google).
The backend never sends or stores OTP codes — it only **verifies the Firebase ID
token** the app forwards, then issues its own JWT access + refresh tokens.

```
App: enter phone → Firebase sends SMS OTP → enter OTP → Firebase returns ID token
App → POST /api/auth/firebase { idToken, fullName?, email? }
Backend: verify ID token (Admin SDK) → upsert user + session → return JWT pair
App → all later calls: Authorization: Bearer <accessToken>
```

### Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/firebase` | Register (first call, needs `fullName`) **or** login |
| POST | `/api/auth/refresh`  | Rotate refresh token → new access + refresh pair |
| POST | `/api/auth/logout`   | Revoke a refresh-token session |
| GET  | `/api/auth/me`       | Current user profile (SRS Module 2) |
| PATCH| `/api/auth/me`       | Edit profile (fullName, email, photo, timeZone, language) |

### Tables (SRS Module 1)
* `users` — phone, firebaseUid, fullName, email?, profilePhoto?, timeZone, language
* `user_sessions` — one row per refresh token (hashed), supports rotation/logout
* `otp_logs` — **audit** trail of Firebase verifications (no OTP codes stored)

---

## 🔥 Firebase Setup (one-time)

1. Create a project at <https://console.firebase.google.com>.
2. **Authentication → Sign-in method → Phone → Enable.**
3. **Project Settings → Service accounts → Generate new private key.** Save the
   downloaded JSON as `firebase-service-account.json` in this project root
   (already gitignored) and point `FIREBASE_CREDENTIALS_PATH` at it in `.env`.
4. For the mobile app (later phase): add an Android app, download
   `google-services.json`, and register your debug **and** release keystore
   **SHA-1 + SHA-256** fingerprints (required for Android phone auth).
5. For development, add **test phone numbers** under Authentication → Sign-in
   method → Phone → *Phone numbers for testing* to avoid burning SMS quota.

> Without the credentials file the server still boots (you'll see a warning), but
> `/api/auth/firebase` returns `401` until it's in place.

# itaxeasy-apk-back
