"""FastAPI entry point: CORS, auth routes, and router wiring.

Schema creation is not done here — `alembic upgrade head` runs before the app
starts (see docker-entrypoint.sh), so importing this module never touches the
database and multiple workers cannot race each other over DDL.
"""
import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from httpx import HTTPError
from sqlalchemy.orm import Session

from app.auth import exchange_code_for_user, get_google_authorize_url
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.logging_config import configure_logging
from app.models import User
from app.ratelimit import rate_limit
from app.routers import content, follows, health, users
from app.schemas import MeResponse, OkResponse
from app.session import SESSION_TTL, delete_session

configure_logging()
logger = logging.getLogger(__name__)

OAUTH_STATE_COOKIE = "oauth_state"
OAUTH_STATE_TTL = 300
SESSION_COOKIE = "session"

auth_limit = Depends(rate_limit("auth", settings.rate_limit_auth))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (frontend origin: %s)", settings.app_name, settings.frontend_origin)
    if not settings.cookie_secure:
        logger.warning(
            "COOKIE_SECURE is off — session cookies will travel over plain HTTP. "
            "Set COOKIE_SECURE=true when serving over HTTPS."
        )
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _set_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    """One place that decides cookie flags, so none of them can be forgotten."""
    response.set_cookie(
        key,
        value,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def _clear_cookie(response: Response, key: str) -> None:
    response.delete_cookie(
        key, path="/", samesite=settings.cookie_samesite, secure=settings.cookie_secure
    )


def _login_error(reason: str) -> RedirectResponse:
    response = RedirectResponse(
        url=f"{settings.frontend_origin}/?error={reason}", status_code=302
    )
    _clear_cookie(response, OAUTH_STATE_COOKIE)
    return response


# ----- Auth routes (no auth required) -----


@app.get("/auth/google", dependencies=[auth_limit])
async def auth_google():
    """Redirect user to Google OAuth consent screen."""
    redirect_uri = f"{settings.backend_public_url.rstrip('/')}/auth/callback"
    state = secrets.token_urlsafe(16)
    response = RedirectResponse(
        url=get_google_authorize_url(redirect_uri, state), status_code=302
    )
    _set_cookie(response, OAUTH_STATE_COOKIE, state, OAUTH_STATE_TTL)
    return response


@app.get("/auth/callback", name="auth_callback", dependencies=[auth_limit])
async def auth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """Handle redirect from Google: exchange code for user and set session cookie."""
    if error:
        logger.warning("Google returned an OAuth error: %s", error)
        return _login_error(error)
    if not code:
        logger.warning("OAuth callback without a code")
        return _login_error("no_code")
    saved_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if not saved_state or not state or not secrets.compare_digest(saved_state, state):
        logger.warning("OAuth callback with mismatched state")
        return _login_error("invalid_state")

    redirect_uri = f"{settings.backend_public_url.rstrip('/')}/auth/callback"
    try:
        result = await exchange_code_for_user(code, redirect_uri)
    except (ValueError, OSError, HTTPError):
        logger.exception("OAuth code exchange failed")
        return _login_error("oauth_failed")

    response = RedirectResponse(
        url=f"{settings.frontend_origin}{result['redirect_path']}", status_code=302
    )
    _set_cookie(response, SESSION_COOKIE, result["session_token"], SESSION_TTL)
    _clear_cookie(response, OAUTH_STATE_COOKIE)
    return response


@app.get("/auth/me", response_model=MeResponse)
async def auth_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Current user info for the frontend's auth context."""
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        nickname=current_user.nickname,
        timezone=current_user.timezone,
        has_completed_onboarding=current_user.has_completed_onboarding,
        awaiting_period_end=bool(current_user.awaiting_period_end),
    )


@app.post("/auth/logout", response_model=OkResponse)
async def auth_logout(request: Request):
    """Clear Redis session and session cookie."""
    delete_session(request.cookies.get(SESSION_COOKIE))
    response = JSONResponse(OkResponse().model_dump())
    _clear_cookie(response, SESSION_COOKIE)
    return response


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(follows.router, prefix="/follows", tags=["follows"])
app.include_router(content.router, prefix="/content", tags=["content"])
app.include_router(health.router, tags=["health"])
