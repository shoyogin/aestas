"""Redis-backed session management."""
import json
import logging
import secrets

import redis

from app.config import settings

logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.redis_url, decode_responses=True)
SESSION_PREFIX = "session:"
SESSION_TTL = settings.session_ttl_days * 24 * 60 * 60


def create_session(user_id: int) -> str:
    """Store session in Redis and return session token (to set as cookie)."""
    token = secrets.token_urlsafe(32)
    redis_client.setex(
        SESSION_PREFIX + token,
        SESSION_TTL,
        json.dumps({"user_id": user_id}),
    )
    return token


def get_session(token: str | None) -> dict | None:
    """Return session data from Redis, or None if missing/expired/corrupt."""
    if not token:
        return None
    raw = redis_client.get(SESSION_PREFIX + token)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return {"user_id": int(data["user_id"])}
    except (ValueError, TypeError, KeyError):
        logger.warning("Discarding unreadable session payload")
        return None


def delete_session(token: str | None) -> None:
    """Remove session from Redis (logout)."""
    if token:
        redis_client.delete(SESSION_PREFIX + token)


def ping() -> bool:
    """True if Redis answers, for the readiness probe."""
    try:
        return bool(redis_client.ping())
    except redis.RedisError:
        logger.exception("Redis ping failed")
        return False
