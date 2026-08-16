# 3. OAuth and sessions

This doc explains how the “Sign in with Google” flow is implemented in the backend and how we keep the user logged in using Redis.

## Flow in steps

1. **User clicks “Sign in with Google”**
   The frontend sends the user to the backend at `GET http://localhost:8000/auth/google` (or whatever `VITE_API_URL` is set to).

2. **Backend starts the OAuth flow**
   In `main.py`, `auth_google`:
   - Builds the **redirect URI** where Google will send the user back (e.g. `http://localhost/auth/callback`).
   - Generates a random **state** (to prevent CSRF) and stores it in a cookie.
   - Builds Google’s authorization URL (client ID, scopes, redirect URI, state) and **redirects the browser** to Google.

3. **User logs in on Google**
   Google shows its login page. We never see the password.

4. **Google redirects back to our backend**
   Google sends the user to our redirect URI with a **code** (one-time) and the **state** we sent.

5. **Backend handles the callback** (`GET /auth/callback`)
   In `main.py`, `auth_callback`:
   - Checks that the `state` matches the one in the cookie (CSRF check).
   - Calls `exchange_code_for_user(code, redirect_uri)` in `auth.py`:
     - Uses **Authlib** to exchange the `code` for **access token** and (if requested) **refresh token**.
     - Calls Google’s userinfo API to get **email** and **Google ID**.
     - In the database: **find or create** a `User` with that `google_id` and `email`.
     - Creates a **session** in Redis (see below) and gets back a **session token**.
   - **Redirects** the browser to the frontend (`/onboarding` or `/app`) and **sets a cookie** named `session` with the session token (HttpOnly, SameSite=Lax, 7-day expiry).

6. **Frontend knows who’s logged in**
   The frontend calls `GET http://localhost:8000/auth/me` (with credentials). The browser sends the `session` cookie (set by the backend on port 8000). The backend reads the cookie, looks up the session in Redis, and returns user info (e.g. `has_completed_onboarding`). No password or Google token is stored in the frontend; only the session cookie is used. **Sign out** is `POST /auth/logout` (Account tab): Redis session is deleted and the cookie is cleared.

## Why we use Redis for sessions

- **Sessions are “who is logged in right now.”** We need to store something like: “this session token belongs to user ID 42, and they’ve completed onboarding.”
- **Redis** is fast and supports a simple key–value store with expiry. We store: `session:<token>` → `user_id|email|has_completed_onboarding` with a TTL (e.g. 7 days). So we don’t need to store session data in the database; we keep PostgreSQL for permanent data (user account, cycle length).
- **Cookie** holds only the **session token**. The actual session data lives in Redis. If Redis is cleared or the token expires, the user is logged out.

## Code you can look at

- **Backend**
  - `backend/main.py`: `auth_google`, `auth_callback`, `auth_me`.
  - `backend/auth.py`: `get_google_authorize_url`, `exchange_code_for_user` (Authlib + userinfo + DB create/find + session create).
  - `backend/session.py`: `create_session`, `get_session` (Redis get/set/delete).
- **Frontend**
  - `frontend/src/components/Welcome.jsx`: link to backend `/auth/google` (full URL from API base).
  - `frontend/src/hooks/useAuth.js`: calls `GET /auth/me` (API base URL) and sets `isAuthenticated` and `hasCompletedOnboarding`.
  - `frontend/src/App.jsx`: uses `useAuth` to decide whether to show Onboarding or WIP and to protect routes.

## Single origin and cookies

The session cookie is set by the **backend** (port 8000) when it redirects after Google login. The frontend (port 5173) calls the backend with `credentials: 'include'`, so the browser sends that cookie to the backend. Cookies are sent to the origin that set them (localhost:8000), so requests from the frontend to the backend do include the session cookie.

## Summary

- OAuth: user is sent to Google, then back to our `/auth/callback` with a code; we exchange it for user info, create/find the user in PostgreSQL, create a session in Redis, and set a session cookie.
- Sessions are stored in Redis (token → user id + flags); the cookie only holds the token.
- The frontend uses `GET /auth/me` (with the cookie) to know if the user is logged in and whether they’ve completed onboarding, and to drive conditional navigation.
