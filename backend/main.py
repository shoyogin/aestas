"""FastAPI entry point: CORS, routes, and OAuth callback."""
import secrets
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import settings
from database import get_db, engine, Base
from models import User
from auth import get_google_authorize_url, exchange_code_for_user
from session import get_session
from dependencies import get_current_user
from routers import users

# Create tables on startup (for dev; in production use migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- Auth routes (no auth required) -----


@app.get("/auth/google")
async def auth_google(request: Request):
    """Redirect user to Google OAuth consent screen."""
    base = settings.backend_public_url.rstrip("/")
    redirect_uri = f"{base}/auth/callback"
    state = secrets.token_urlsafe(16)
    # Store state in cookie for CSRF check (simplified: we could use Redis)
    url = get_google_authorize_url(redirect_uri, state)
    response = RedirectResponse(url=url, status_code=302)
    response.set_cookie("oauth_state", state, max_age=300, httponly=True, samesite="lax")
    return response


@app.get("/auth/callback", name="auth_callback")
async def auth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """Handle redirect from Google: exchange code for user and set session cookie."""
    if error:
        return RedirectResponse(
            url=f"{settings.frontend_origin}/?error={error}",
            status_code=302,
        )
    if not code:
        return RedirectResponse(url=f"{settings.frontend_origin}/?error=no_code", status_code=302)
    saved_state = request.cookies.get("oauth_state")
    if not saved_state or saved_state != state:
        return RedirectResponse(url=f"{settings.frontend_origin}/?error=invalid_state", status_code=302)

    redirect_uri = f"{settings.backend_public_url.rstrip('/')}/auth/callback"
    try:
        result = await exchange_code_for_user(code, redirect_uri)
    except Exception:
        return RedirectResponse(url=f"{settings.frontend_origin}/?error=oauth_failed", status_code=302)

    redirect_url = f"{settings.frontend_origin}{result['redirect_path']}"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        "session",
        result["session_token"],
        max_age=60 * 60 * 24 * 7,
        httponly=True,
        samesite="lax",
        path="/",
    )
    response.delete_cookie("oauth_state")
    return response


@app.get("/auth/me")
async def auth_me(request: Request, db: Session = Depends(get_db)):
    """Return current user info if session is valid (for frontend useAuth)."""
    token = request.cookies.get("session")
    session_data = get_session(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == session_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "has_completed_onboarding": user.has_completed_onboarding,
    }


# ----- User routes -----
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/health")
def health():
    return {"status": "ok"}
