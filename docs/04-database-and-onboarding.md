# 4. Database and onboarding

This document explains how we store users and cycle length in PostgreSQL and how the onboarding flow works.

## Database: PostgreSQL

We use **PostgreSQL** as the main database. It holds data that must **persist forever** (user account and cycle length). Session data (who is logged in right now) is in Redis, not here.

## Schema: the `users` table

The table is defined in `backend/app/models.py` with **SQLAlchemy** (an ORM: we define Python classes that map to tables).

- **id** — Auto-increment primary key.
- **google_id** — Unique ID from Google (so we can find the user when they log in again).
- **email** — Email from Google.
- **cycle_length** — Number of days for “typical cycle.” It is **nullable**: `NULL` until the user completes onboarding; then we set it (e.g. 28).
- **created_at**, **updated_at** — Timestamps.

We also have a property `has_completed_onboarding`: it is `True` when `cycle_length` is not `NULL`.

Alongside `users` sit `daily_logs` (one row per user per day), `follow_requests`
(see [08-circle-follows.md](08-circle-follows.md)), and `profile_pictures` —
one avatar per account, kept out of `users` so the image bytes do not ride
along on every query that loads a user (see
[09-profile-pictures.md](09-profile-pictures.md)).

Schema changes are handled by **Alembic migrations** in `backend/migrations/`, applied by `docker-entrypoint.sh` before the app starts serving. This used to be `Base.metadata.create_all()` plus a few hand-written `ALTER TABLE` helpers running at import time, which meant importing the app opened a database connection and several worker processes could race each other over the same DDL. `alembic check` in CI fails the build if the models and the migrations disagree.

## Onboarding flow

1. **New user** signs in with Google → we create a row in `users` with `cycle_length = NULL`.
2. Backend redirects to **/onboarding**.
3. **Frontend** shows the onboarding form: “How many days is your typical cycle?” with a number input (21–45) and an info banner (Tailwind styling).
4. User submits → frontend sends **POST /api/users/onboarding** with `{ "cycle_length": 28 }` (with credentials so the session cookie is sent).
5. **Backend** (`app/routers/users.py`): `get_current_user` ensures the request has a valid session and loads the `User`. We update that user’s `cycle_length` and save. The session in Redis holds only the user id, so there is nothing to refresh — `has_completed_onboarding` is read from the database on every `/auth/me`. The frontend calls `refresh()` on its auth context after onboarding so the route guards see the new state immediately.
6. Frontend redirects to **/app** (WIP page).

## Code to look at

- **Backend**
  - `backend/app/models.py`: `User` model and `has_completed_onboarding`.
  - `backend/app/database.py`: engine, `SessionLocal`, `get_db`.
  - `backend/migrations/`: Alembic revisions — the only place the schema changes.
  - `backend/app/routers/users.py`: `POST /onboarding` body validation (15–45 days) and update.
  - `backend/app/dependencies.py`: `get_current_user` (uses session from Redis to load `User` from DB).
- **Frontend**
  - `frontend/src/components/Onboarding.jsx`: form state, range 21–45, info banner, call to `submitOnboarding(cycleLength)`.
  - `frontend/src/api/onboarding.js`: `submitOnboarding` → `POST /users/onboarding` with `cycle_length`.

## Why cycle length in the DB and not Redis?

Cycle length is **permanent** user data. Redis is for **temporary** session data. So we keep it in PostgreSQL as the single source of truth; the session in Redis only stores things like “user ID” and “has completed onboarding” so we can answer `/auth/me` quickly without hitting the DB every time (we could also refresh that flag from the DB when we need it).

## Summary

- **PostgreSQL** stores: `users` (google_id, email, cycle_length, timestamps).
- **Onboarding**: frontend POSTs `cycle_length` to `/users/onboarding`; backend updates the current user’s row and returns; frontend redirects to `/app`.
- **Redis** is used for sessions only; cycle data lives in the database.
