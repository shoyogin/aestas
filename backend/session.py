"""Redis-backed session management."""
import secrets

import redis

from config import settings

# Import after database so Base is defined

redis_client = redis.from_url(settings.redis_url, decode_responses=True)
SESSION_PREFIX = "session:"
SESSION_TTL = 60 * 60 * 24 * 7  # 7 days


def create_session(user_id: int, email: str, has_completed_onboarding: bool) -> str:
    """Store session in Redis and return session token (to set as cookie)."""
    token = secrets.token_urlsafe(32)
    key = SESSION_PREFIX + token
    redis_client.setex(
        key,
        SESSION_TTL,
        f"{user_id}|{email}|{1 if has_completed_onboarding else 0}",
    )
    return token


def get_session(token: str | None) -> dict | None:
    """Return session data from Redis or None if invalid/expired."""
    if not token:
        return None
    key = SESSION_PREFIX + token
    raw = redis_client.get(key)
    if not raw:
        return None
    parts = raw.split("|", 2)
    if len(parts) != 3:
        return None
    try:
        return {
            "user_id": int(parts[0]),
            "email": parts[1],
            "has_completed_onboarding": parts[2] == "1",
        }
    except ValueError:
        return None


def delete_session(token: str | None) -> None:
    """Remove session from Redis (logout)."""
    if token:
        redis_client.delete(SESSION_PREFIX + token)
