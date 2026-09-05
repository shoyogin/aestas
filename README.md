# Aestas

A modern cycle-tracking app: sign in with Google, set your cycle length, log period days, add a profile picture, and see phase-based suggestions on the main calendar. Built with React/Vite/Tailwind (frontend), FastAPI (backend), PostgreSQL, and Redis, orchestrated with Docker Compose.

![Welcome screen](docs/assets/welcome.png)


## Quick start

1. **Google OAuth**
   Create an OAuth 2.0 Client in [Google Cloud Console](https://console.cloud.google.com/) and set **Authorized redirect URI** to `http://localhost:8000/auth/callback`. See [docs/02-google-oauth-setup.md](docs/02-google-oauth-setup.md).

2. **Environment**
   Copy `.env.example` to `.env` in the project root and set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

3. **Run**
   ```bash
   docker compose up --build
   ```
   Frontend: **http://localhost:5173** · Backend: **http://localhost:8000** (Postgres + Redis start with them).
   Open the frontend URL, sign in with Google → Onboarding (cycle length + last cycle) → Track / Insights / Friends tabs.

## Project structure

- **frontend/** — React + Vite + Tailwind. Screens (Welcome, Onboarding, LastCycle, and the AppShell tabs Track / Insights / Friends), `src/api/` client, `src/cycle/` phase engine, `src/context/authContext.js` for the signed-in user.
- **backend/** — FastAPI as the `app` package (`app.main:app`): OAuth, Redis sessions, PostgreSQL, and the users / follows / content / health routers.
- **backend/migrations/** — Alembic migrations. They are the only thing that changes the schema.
- **shared/phase-cases.json** — Golden cases for the cycle phase engine. The backend and frontend implement the same rules separately and both test suites assert against this file, so the two cannot drift apart.
- **docs/** — Educational docs (overview, Google OAuth, OAuth/sessions, database/onboarding, Docker/CI, pre-commit, cycle phases, circle follows).
- **docker-compose.yml** — frontend (Vite dev server), backend, postgres, redis.

## Development

- **Full stack in Docker**: `docker compose up --build` — frontend on 5173, backend on 8000. Frontend source is mounted so edits trigger Vite HMR. The backend container applies migrations before it starts serving.
- **Frontend only locally**: `cd frontend && npm install && npm run dev` (talks to backend at `http://localhost:8000`).
- **Backend only locally**:
  ```bash
  cd backend
  pip install -r requirements-dev.txt
  export DATABASE_URL=... REDIS_URL=... GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=...
  alembic upgrade head          # never create_all: migrations own the schema
  uvicorn app.main:app --reload
  ```
- **Tests**: `cd backend && pytest` and `cd frontend && npm test`.
- **Migrations**: `alembic revision -m "..."` to add one, `alembic upgrade head` to apply, `alembic check` to confirm the models and the schema still agree.
- **Pre-commit**: `pip install pre-commit && pre-commit install`.
- **CI**: GitHub Actions on push/PR to `main` — frontend lint/test/build, backend lint, migration round-trip, `alembic check`, and pytest, plus a Docker image build.

### Adopting an existing database

The schema predates Alembic. A database created before migrations existed needs
to be told where it already is, once:

```bash
cd backend
alembic stamp 0001_initial   # "this DB already has the original schema"
alembic upgrade head
```

A fresh database just runs `alembic upgrade head`.

## Configuration

Set through the environment (see `.env.example`):

| Variable | Default | Notes |
| --- | --- | --- |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | — | Required for sign-in. |
| `DATABASE_URL` | local Postgres | |
| `REDIS_URL` | local Redis | Sessions and rate limiting. |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS origin and post-login redirect target. |
| `BACKEND_PUBLIC_URL` | `http://localhost:8000` | Used to build the OAuth redirect URI. |
| `COOKIE_SECURE` | `false` | **Set to `true` anywhere served over HTTPS**, so the session cookie is not sent in the clear. |
| `LOG_LEVEL` | `INFO` | |
| `SESSION_TTL_DAYS` | `7` | |
| `AVATAR_MAX_UPLOAD_BYTES` | `5242880` | Largest profile picture accepted, before it is re-encoded. |

## Health checks

- `GET /health` — liveness. Touches no dependency; answers as long as the process is up.
- `GET /health/ready` — readiness. Returns 503 unless both Postgres and Redis answer. This is what Compose waits on.

## Docs (educational)

All in **docs/**:

1. [01-overview-and-setup.md](docs/01-overview-and-setup.md) — What the app does, stack, layout, how to run.
2. [02-google-oauth-setup.md](docs/02-google-oauth-setup.md) — Create Google OAuth client and redirect URI.
3. [03-oauth-and-sessions.md](docs/03-oauth-and-sessions.md) — OAuth flow and Redis sessions.
4. [04-database-and-onboarding.md](docs/04-database-and-onboarding.md) — PostgreSQL schema and onboarding API.
5. [05-docker-and-ci.md](docs/05-docker-and-ci.md) — Docker Compose and GitHub Actions CI.
6. [06-pre-commit.md](docs/06-pre-commit.md) — Pre-commit hooks and usage.
7. [07-cycle-phases.md](docs/07-cycle-phases.md) — Four cycle phases and the dashboard under the calendar.
8. [08-circle-follows.md](docs/08-circle-follows.md) — Nickname search, friend vs partner follows, privacy.
9. [09-profile-pictures.md](docs/09-profile-pictures.md) — Avatar upload, normalization, and who can see it.

## Palette

- **Night Bordeaux** `#461220`
- **Burnt Rose** `#8c2f39`
- **Dusty Mauve** `#b23a48`
- **Powder Blush** `#fcb9b2`
- **Peach Fuzz** `#fed0bb`

## License

Private / unlicensed unless you add one.
