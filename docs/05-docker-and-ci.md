# 5. Docker and CI

This document explains how we run the backend with Docker Compose and how CI (GitHub Actions) and pre-commit are set up.

## Docker Compose: what runs

When you run `docker compose up --build`, four **services** start:

1. **frontend** — Vite dev server (Node 22). Port **5173** is published. Source is mounted so edits trigger HMR. Uses `VITE_API_URL=http://localhost:8000` so the browser calls the backend.
2. **backend** — FastAPI app (Python). Connects to PostgreSQL and Redis. Port **8000** is published.
3. **postgres** — PostgreSQL 16. Data is stored in a **volume** so it survives container restarts. Healthcheck: `pg_isready`.
4. **redis** — Redis 7. Used for sessions. Healthcheck: `redis-cli ping`.

## Environment variables

- **Backend** gets `DATABASE_URL`, `REDIS_URL`, `FRONTEND_ORIGIN` (e.g. `http://localhost:5173`), `BACKEND_PUBLIC_URL` (e.g. `http://localhost:8000`), `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` from `docker-compose.yml` and from `.env` for the Google keys.
- **BACKEND_PUBLIC_URL** is used to build the OAuth redirect URI (`http://localhost:8000/auth/callback`).

## CI: GitHub Actions

The workflow in `.github/workflows/ci.yml` runs on **push** and **pull_request** to `main`.

- **Frontend job**
  - Node 22, install deps in `frontend/`, run `npm run lint` and `npm run build`. The build uses the default API URL (`http://localhost:8000`); you can set `VITE_API_URL` in the workflow if needed.

- **Backend job**
  - Python 3.12, install from `backend/requirements.txt`.
  - **Services**: PostgreSQL and Redis (same config as in Docker Compose) so the app can connect.
  - Lint with **ruff**.
  - **Smoke test**: start the app with `uvicorn`, wait a bit, then `curl` the `/health` endpoint. Ensures the app starts and responds.

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
- **CI** (GitHub Actions) lints and builds the frontend and lints and smoke-tests the backend.
- **Pre-commit** runs lint and basic checks so broken or inconsistent code doesn’t get committed.
