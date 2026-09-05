# 5. Docker and CI

This document explains how we run the backend with Docker Compose and how CI (GitHub Actions) and pre-commit are set up.

## Docker Compose: what runs

When you run `docker compose up --build`, four **services** start:

1. **frontend** — Vite dev server (Node 22), the Dockerfile's `dev` target. Port **5173** is published. Source is mounted so edits trigger HMR. Uses `VITE_API_URL=http://localhost:8000` so the browser calls the backend.
2. **backend** — FastAPI app (Python). Connects to PostgreSQL and Redis. Port **8000** is published. Its entrypoint runs `alembic upgrade head` before uvicorn starts, so the schema is always current and no two workers race over DDL. Runs as an unprivileged user.
3. **postgres** — PostgreSQL 16. Data is stored in a **volume** so it survives container restarts. Healthcheck: `pg_isready`.
4. **redis** — Redis 7. Sessions and rate limiting. Healthcheck: `redis-cli ping`.

The backend's healthcheck hits **`/health/ready`**, not `/health`. `/health`
only proves the process is alive; readiness also checks Postgres and Redis, so
the frontend waits for a backend that can actually serve requests.

### The frontend image has two targets

`frontend/Dockerfile` is multi-stage:

- `--target dev` — the Vite dev server with hot reload. This is what Compose uses.
- `--target production` — `npm run build`, then the static files served by nginx,
  with `try_files … /index.html` so client-side routes do not 404 on refresh.

## Environment variables

- **Backend** gets `DATABASE_URL`, `REDIS_URL`, `FRONTEND_ORIGIN` (e.g. `http://localhost:5173`), `BACKEND_PUBLIC_URL` (e.g. `http://localhost:8000`), `COOKIE_SECURE`, `LOG_LEVEL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` from `docker-compose.yml` and from `.env` for the Google keys.
- **BACKEND_PUBLIC_URL** is used to build the OAuth redirect URI (`http://localhost:8000/auth/callback`).
- **COOKIE_SECURE** must be `true` anywhere the app is served over HTTPS, or the
  session cookie travels in the clear. It is `false` for local HTTP dev, and the
  app logs a warning at startup to say so.

## CI: GitHub Actions

The workflow in `.github/workflows/ci.yml` runs on **push** and **pull_request** to `main`.

- **Frontend job**
  - Node 22, `npm ci` in `frontend/`, then `npm run lint`, `npm test`, `npm run build`. The build uses the default API URL (`http://localhost:8000`); you can set `VITE_API_URL` in the workflow if needed.
  - Install is `npm ci` with **no `|| npm install` fallback**. The fallback used
    to paper over a stale lockfile instead of failing the build.

- **Backend job**
  - Python 3.12, install from `backend/requirements-dev.txt`.
  - **Services**: PostgreSQL and Redis (same config as in Docker Compose) so the app can connect.
  - Lint with **ruff**.
  - **Migrations round-trip**: `alembic upgrade head`, `downgrade base`, `upgrade head`. A migration that cannot be undone is caught here rather than in production.
  - **`alembic check`**: fails if the SQLAlchemy models and the migrations have drifted apart.
  - **`pytest`**: the full suite against a real PostgreSQL.

- **Docker job**
  - Builds both images, so a broken Dockerfile fails the PR instead of the deploy.

Both test suites run `shared/phase-cases.json`. The backend and the frontend
implement the cycle phase rules separately, and those shared fixtures are what
stop the two from drifting apart.

No end-to-end browser tests in this basic setup; you can add them later (e.g. Playwright).

## Pre-commit

The config in `.pre-commit-config.yaml` runs **hooks** before each commit (after you run `pre-commit install`):

- **pre-commit-hooks**: trailing whitespace, end-of-file fixer, YAML/JSON check, no large files, no private keys.
- **ruff**: lint and fix Python in `backend/`.
- **eslint**: lint JS/JSX in `frontend/` (run from `frontend/` so it uses the project’s ESLint config).

To use it:

```bash
pip install pre-commit   # or use a dev environment
pre-commit install       # install git hooks
pre-commit run --all-files   # run on all files once
```

Then every `git commit` will run these checks. If something fails, the commit is blocked until you fix the reported issues.

## Summary

- **Docker Compose** runs frontend (Vite), backend, PostgreSQL, and Redis. One command: `docker compose up --build`.
- **CI** (GitHub Actions) lints, tests, and builds the frontend; lints, round-trips the migrations, and tests the backend; and builds both Docker images.
- **Pre-commit** runs lint and basic checks so broken or inconsistent code doesn’t get committed.
