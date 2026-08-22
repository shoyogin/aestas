# Resume: hardening refactor (branch `refactor/hardening`)

Work-in-progress from the code-review action list. Everything except the
compliance/product section (§5 of the review) is in scope. Backend is largely
done; frontend has not been started.

## Follow semantics agreed with the user (Instagram model)

A request stays **pending** until the target acts. Until then the requester's
only move is to **withdraw** it and send it again. `refused`, `withdrawn`, and
`revoked` are all re-requestable, and the row is reused rather than duplicated
(`uq_follow_requester_target`). Pending requests **never expire** — the old
14-day inbox cutoff is gone, because it hid requests while still blocking
re-requests.

## How to run things

```bash
# throwaway Postgres used for local test runs (recreate if gone)
docker run -d --name aestas-test-pg \
  -e POSTGRES_USER=aestas -e POSTGRES_PASSWORD=aestas -e POSTGRES_DB=aestas_test \
  -p 55432:5432 postgres:16-alpine

# venv with backend deps (recreate with: python3 -m venv <dir> && pip install -r backend/requirements-dev.txt)
VENV=/tmp/claude-1000/-home-ginevracerri-ginevra-dev-aestas/e1f1b347-f37a-4411-a54c-ba225a6c3dff/scratchpad/venv

cd backend
export DATABASE_URL="postgresql://aestas:aestas@localhost:55432/aestas_test"
export REDIS_URL="redis://localhost:6379/15"     # local redis is running
$VENV/bin/alembic upgrade head
$VENV/bin/alembic check        # asserts ORM == migrations
$VENV/bin/python -m pytest tests -q
```

Local redis was already running on 6379. Local python is 3.10; the project
targets 3.12 (CI and Docker use 3.12).

## DONE (verified)

- **Package layout**: everything moved to `backend/app/` (`app.main:app`).
  Routers in `backend/app/routers/`.
- **Alembic** replaces `create_all` + the hand-rolled DDL functions.
  `0001_initial` reproduces the pre-Alembic schema; `0002_tz_and_cleanup` makes
  the changes. Both `upgrade head` and `downgrade base` verified against
  Postgres 16, and `alembic check` reports no drift from the ORM.
  *Existing dev DB*: `alembic stamp 0001_initial && alembic upgrade head`.
- **No DDL at import time** — `docker-entrypoint.sh` runs `alembic upgrade head`
  before uvicorn, so workers cannot race over DDL.
- **Dropped the denormalized flow arrays** (`spot_date`/`light_date`/
  `normal_date`/`heavy_date`); `daily_logs` is now the only source. Migration
  0002 backfills them into `daily_logs` before dropping.
- **Added `users.timezone`** (IANA); `get_phase_for_today` now uses the user's
  own day instead of the server's UTC day.
- **LIKE wildcards escaped** in `/users/search` (searching `%` no longer lists
  every user).
- **Nickname collision** → 409 via `IntegrityError` handling, not a 500.
- **Daily log upsert** → single `INSERT ... ON CONFLICT DO UPDATE`.
- **Cycle dates**: deduped, kept sorted, rejected if in the user's future or
  before 2000-01-01.
- **Follows rewritten** to the Instagram model above. New endpoints:
  `GET /follows/requests` (my pending outgoing, cancellable) and
  `GET /follows/followers` (who can see my phase — closes the "cannot revoke
  access I granted" gap). `DELETE /follows/{id}` now withdraws / unfollows /
  removes a follower depending on who calls it and the current status.
- **N+1 fixed** with relationships + `joinedload`.
- **Pydantic response models** on every endpoint (`app/schemas.py`).
- **Logging** (`app/logging_config.py`); OAuth failures are now logged with a
  traceback instead of silently redirecting.
- **Rate limiting** (`app/ratelimit.py`, Redis fixed-window) on search, follow
  writes, and the auth endpoints. Fails open if Redis is down.
- **Cookies**: `Secure` flag driven by `COOKIE_SECURE` setting, applied through
  one `_set_cookie` helper. `secrets.compare_digest` for the OAuth state check.
- **Health**: `/health` (liveness, no deps) and `/health/ready` (Postgres +
  Redis, 503 when degraded).
- **Single source of truth for phase copy**: `backend/app/content/
  phase_panels.json`, served at `GET /content/phases`. `phase_share.py` is gone,
  replaced by `app/phase_content.py`. The frontend must now fetch this instead
  of keeping `src/cycle/phaseContent.js`.
- **Dead code removed**: `secret_key` setting, `asyncpg` and `itsdangerous`
  deps, the unused `has_completed_onboarding` field in the session payload
  (session is now JSON and holds only `user_id`), `access_type=offline` /
  `prompt=consent` on the OAuth URL.
- **Dockerfile**: non-root user, `.dockerignore`, entrypoint script.
- **ruff** widened to E/F/W/I/B/UP/C4/SIM, line-length 100.
- **Golden fixtures**: `shared/phase-cases.json`, 26 cases. Backend test suite
  (`backend/tests/`) runs them plus property-style tests over every allowed
  cycle length (15-45).

### Finding to report to the user (do not silently "fix")

For **cycle lengths of 15-17 days** the engine reports **no menstrual phase at
all** and puts ovulation on day 1. `ovDay = length - 14` collapses to 1-3, and
`maxMenstrual = ovStart - 1` then clamps the menstrual window to zero. Since
onboarding allows a minimum of 15, a user can enter 15 and be told they are
ovulating on the first day of their period. This is a modelling limitation in
both implementations, not a code defect, and changing it is a product decision.
Encoded as-is in `shared/phase-cases.json` ("very short cycle: ovulation clamps
to day 1 and squeezes out menstrual").

## NEXT — not started

1. **Router tests.** The engine suite passes (68 tests), but there are no
   endpoint tests yet. Needed: follows lifecycle (withdraw / re-request /
   refuse / accept / partner-uniqueness / cannot-remove-someone-elses),
   search wildcard escaping, daily-log upsert idempotency, cycle-date
   validation, `/content/phases`, `/health/ready` when a dependency is down.
2. **`backend/pytest.ini`** (or `[tool.pytest.ini_options]`) is still missing.
3. **Frontend — nothing done yet.** Outstanding:
   - Point every API call at the new shapes: `/content/phases` for panel copy
     (delete `src/cycle/phaseContent.js`), `PATCH /users/me` now takes
     `{nickname?, timezone?}`, `/follows/requests`, `/follows/followers`,
     `DELETE /follows/{id}` semantics.
   - Send the browser IANA timezone
     (`Intl.DateTimeFormat().resolvedOptions().timeZone`) on load.
   - Circle UI: show pending outgoing requests with a Cancel button, and a
     Followers list with Remove.
   - Shared auth/user context; stop fetching `/auth/me` three times; refresh
     `hasCompletedOnboarding` after onboarding.
   - Axios 401 interceptor → redirect to `/`.
   - Surface save errors (`AppHome.jsx` currently swallows them).
   - `CalendarArc`: render `is_period`; delete the duplicate
     `OUTSIDE_DAY_STYLE`.
   - `PhaseDashboard`: wrap bullets instead of `truncate whitespace-nowrap`,
     drop the fixed `h-[40rem]`, add arrow-key support and `aria-live`.
   - `Friends.jsx`: link to `/circle/:id` instead of the "Coming soon" hint;
     remove the dead `CalendarArc`.
   - Dedupe `toYMD` (3 copies: `cycle/dates.js`, `cycle/phaseEngine.js`,
     `components/LastCycle.jsx`).
   - Delete `components/WIP.jsx` and the unused `bloom-in` keyframe in
     `tailwind.config.js`.
   - `Blooming.jsx`: 3s navigate vs 5s animation.
   - `useMemo` for hormone sampling; guard `/onboarding/last-cycle`.
   - Google Fonts: `<link rel=preconnect>` in `index.html` instead of the
     render-blocking `@import` in `index.css`.
   - Vitest + `src/cycle/phaseEngine.test.js` reading
     `shared/phase-cases.json` (parity with the backend suite).
4. **Infra**: `npm ci` only in CI (drop `|| npm install`), add pytest + vitest
   jobs, add a docker build check, multi-stage production frontend Dockerfile,
   compose healthcheck → `/health/ready`, `docker-compose.yml` env for
   `COOKIE_SECURE`.
5. **Docs**: `docs/` still describes the old layout, the old follow rules, and
   the old migration functions. `README.md` too. `.pre-commit-config.yaml`
   `files:` regexes still assume `^backend/` flat layout (still fine) but ruff
   version should match `requirements-dev.txt`.
6. `.env.example` should gain `COOKIE_SECURE` and `LOG_LEVEL`.
