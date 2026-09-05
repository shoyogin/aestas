# 1. Overview and setup

This document explains what the Aestas app is, which technologies it uses, and how to run it on your machine.

## What is Aestas?

Aestas is a cycle-tracking app. Right now it does three things:

1. **Welcome** — A landing page where you sign in with Google.
2. **Onboarding** — After first sign-in, you answer one question: “How many days is your typical cycle?” We store that in the database.
3. **WIP (Work in progress)** — A simple “Under construction” page for users who have already completed onboarding.

The app is built so we can add more features later (predictions, reminders, etc.) while keeping the codebase clear and maintainable.

## Technology stack (why these choices?)

- **Frontend: React + Vite + Tailwind**
  - **React**: Component-based UI; easy to add new screens and reuse pieces.
  - **Vite**: Fast development server and builds; works well with React.
  - **Tailwind CSS**: Utility classes for layout and colours; we use a custom palette (Night Bordeaux, Burnt Rose, etc.) defined in `frontend/tailwind.config.js`.

- **Backend: Python + FastAPI**
  - **FastAPI**: Modern Python web framework with automatic API docs and validation.
  - We use it for: Google OAuth (login), session management (Redis), and saving user data (PostgreSQL).

- **Database: PostgreSQL**
  - Stores long-term data: user accounts (Google ID, email) and cycle length. This is the “source of truth” that persists forever.

- **Redis**
  - Stores **sessions** only: “who is logged in right now.” Session data is temporary (e.g. 7 days). We do not store cycle data in Redis; that stays in PostgreSQL.

- **Docker Compose**
  - Runs the frontend (Vite dev server on port 5173), backend (port 8000), PostgreSQL, and Redis. One command: `docker compose up --build`.

## Project layout (high level)

```
aestas/
├── frontend/          # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/ # Welcome, Onboarding, WIP, Logo
│   │   ├── api/       # Axios client and API calls (onboarding)
│   │   ├── context/   # authContext (the signed-in user)
│   ├── index.html
│   ├── vite.config.js
│   └── tailwind.config.js
├── backend/           # FastAPI
│   ├── main.py        # App entry, CORS, auth routes (/auth/google, /auth/callback, /auth/me)
│   ├── config.py      # Settings from environment
│   ├── models.py      # SQLAlchemy User model
│   ├── database.py    # PostgreSQL connection
│   ├── auth.py        # Google OAuth (Authlib)
│   ├── session.py     # Redis session create/get
│   └── routers/
│       └── users.py   # POST /users/onboarding
├── docker-compose.yml # Backend, Postgres, Redis
└── docs/              # These educational docs
```

## How to run the app

### Option A: Full stack in Docker (recommended)

1. **Prerequisites**: Docker and Docker Compose installed.
2. **Google OAuth** (see [02-google-oauth-setup.md](02-google-oauth-setup.md)): Create a Google Cloud OAuth 2.0 Client and set **Authorized redirect URI** to `http://localhost:8000/auth/callback`.
3. **Environment**: In the project root, create a `.env` file with `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
4. **Run**: `docker compose up --build`. Frontend runs at **http://localhost:5173**, backend at **http://localhost:8000**. Open the frontend URL and click “Sign in with Google”; after login you’ll be sent to Onboarding (first time) or the WIP page (if you already completed onboarding). Frontend source is mounted so code edits trigger Vite HMR.

### Option B: Backend and frontend both locally

- **Backend**: From `backend/`, install Python deps (`pip install -r requirements-dev.txt`), set `DATABASE_URL`, `REDIS_URL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, apply the schema with `alembic upgrade head`, then run `uvicorn app.main:app --reload`.
- **Frontend**: From `frontend/`, run `npm install` and `npm run dev`. The frontend calls the backend at `http://localhost:8000` (default; override with `VITE_API_URL` in `frontend/.env`).
- **Database and Redis**: Run PostgreSQL and Redis (e.g. with Docker: `docker run -p 5432:5432 -e POSTGRES_USER=aestas -e POSTGRES_PASSWORD=aestas -e POSTGRES_DB=aestas postgres:16-alpine` and `docker run -p 6379:6379 redis:7-alpine`).

**Important**: For Google login to work, the “Authorized redirect URI” in Google Cloud must be `http://localhost:8000/auth/callback` (where the backend receives the callback).

## What happens when you click “Sign in with Google”?

1. The frontend sends you to the backend at `http://localhost:8000/auth/google`.
2. The backend redirects your browser to Google’s login page.
3. After you log in, Google redirects back to our backend at `http://localhost:8000/auth/callback` with a one-time “authorization code.”
4. The backend exchanges that code for your email and Google ID, creates or finds a user in PostgreSQL, creates a **session** in Redis, and sets a **session cookie** in your browser.
5. The backend then redirects you to the frontend (e.g. `http://localhost:5173/onboarding` or `.../app`).
6. The frontend calls `GET http://localhost:8000/auth/me` (with the cookie) to know if you’re logged in and whether you’ve completed onboarding; that’s how it decides which page to show.

This flow is described in more detail in [03-oauth-and-sessions.md](03-oauth-and-sessions.md).

## Next steps

- [02-google-oauth-setup.md](02-google-oauth-setup.md) — Create and configure the Google OAuth client.
- [03-oauth-and-sessions.md](03-oauth-and-sessions.md) — How OAuth and Redis sessions work.
- [04-database-and-onboarding.md](04-database-and-onboarding.md) — PostgreSQL schema and the onboarding API.
- [05-docker-and-ci.md](05-docker-and-ci.md) — Docker Compose and GitHub Actions CI.
