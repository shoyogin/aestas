# 2. Google OAuth setup

To let users “Sign in with Google,” we use **OAuth 2.0**. This document explains what that means in simple terms and how to create the credentials in Google Cloud.

## What is OAuth 2.0?

OAuth 2.0 is a standard way for an app to **ask another service (here, Google) to confirm who the user is**, without the user giving us their Google password.

- The user clicks “Sign in with Google” in our app.
- We redirect them to **Google’s** login page.
- The user logs in on Google (we never see the password).
- Google redirects the user back to **our** app and gives us a one-time **authorization code**.
- Our backend exchanges that code with Google for **tokens** and **user info** (e.g. email, Google ID). We then create a session and log the user in.

So: **we never handle the password**; we only get confirmation from Google that the user is who they say they are.

## Create a Google Cloud project and OAuth client

1. **Open Google Cloud Console**  
   Go to [https://console.cloud.google.com/](https://console.cloud.google.com/).

2. **Create or select a project**  
   Use the project dropdown at the top. Click “New Project,” give it a name (e.g. “Aestas”), and create it.

3. **Enable the Google+ API (or People API)**  
   In the left menu: **APIs & Services → Library**. Search for “Google+ API” or “Google People API” and enable it. (For basic email/profile, “Google People API” or the OAuth consent screen is enough.)

4. **Configure the OAuth consent screen**  
   - Go to **APIs & Services → OAuth consent screen**.
   - Choose **External** (so any Google user can sign in).
   - Fill in App name (e.g. “Aestas”), User support email, and Developer contact.
   - Under **Scopes**, add `.../auth/userinfo.email` and `.../auth/userinfo.profile` (and `openid` if listed).
   - Save. You can add “Test users” during development if the app is in “Testing” mode.

5. **Create OAuth 2.0 credentials**  
   - Go to **APIs & Services → Credentials**.
   - Click **Create credentials → OAuth client ID**.
   - Application type: **Web application**.
   - Name: e.g. “Aestas web”.
   - **Authorized JavaScript origins** (optional for our flow, but good to set):
     - `http://localhost` (for Docker)
     - `http://localhost:5173` (for Vite dev server)
   - **Authorized redirect URIs** (required):
     - `http://localhost:8000/auth/callback` (backend on port 8000)
     - For production: `https://yourdomain.com/auth/callback` (or whatever URL actually hits your backend callback).
   - Create. You’ll get a **Client ID** and **Client Secret**.

6. **Use them in the app**  
   - In the project root, create a `.env` file (or set environment variables):
     - `GOOGLE_CLIENT_ID=...`
     - `GOOGLE_CLIENT_SECRET=...`
   - In Docker Compose, these are passed to the `backend` service (see `docker-compose.yml`). Never commit the secret to git; `.env` is in `.gitignore`.

## Why “redirect URI” matters

When we start the login, we tell Google: “When the user finishes logging in, send them back to **this exact URL**.” That URL must be one of the **Authorized redirect URIs** you configured. If it doesn’t match, Google will refuse the request. Our backend builds this URL from the `BACKEND_PUBLIC_URL` setting (e.g. `http://localhost:8000`, so the callback is `http://localhost:8000/auth/callback`).

## Summary

- OAuth 2.0 lets users sign in with Google without giving us their password.
- You create a “Web application” OAuth client in Google Cloud and get a Client ID and Client Secret.
- You configure the redirect URI to match where your backend receives the callback (`/auth/callback`).
- You pass the client ID and secret to the backend via environment variables and use them in the backend as described in [03-oauth-and-sessions.md](03-oauth-and-sessions.md).
