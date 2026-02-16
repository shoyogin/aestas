"""Google OAuth 2.0 flow using Authlib."""
from urllib.parse import urlencode
from authlib.integrations.httpx_client import AsyncOAuth2Client
from config import settings
from database import SessionLocal
from models import User
from session import create_session

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPES = ["openid", "email", "profile"]


def get_google_authorize_url(redirect_uri: str, state: str) -> str:
    """Build the URL to send the user to Google for login."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_user(code: str, redirect_uri: str) -> dict:
    """
    Exchange the authorization code for tokens, fetch userinfo,
    create or update user in DB, create session. Return session token and redirect path.
    """
    async with AsyncOAuth2Client(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        token_endpoint=GOOGLE_TOKEN_URL,
    ) as client:
        token = await client.fetch_token(
            GOOGLE_TOKEN_URL,
            code=code,
            redirect_uri=redirect_uri,
        )
        if not token:
            raise ValueError("Failed to get token from Google")
        resp = await client.get(GOOGLE_USERINFO_URL)
        resp.raise_for_status()
        info = resp.json()

    google_id = info.get("id")
    email = info.get("email") or ""
    if not google_id or not email:
        raise ValueError("Google did not return id or email")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
            user = User(google_id=google_id, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        session_token = create_session(
            user.id,
            user.email,
            user.has_completed_onboarding,
        )
        return {
            "session_token": session_token,
            "redirect_path": "/onboarding" if not user.has_completed_onboarding else "/app",
        }
    finally:
        db.close()
