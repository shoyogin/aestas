"""Small Redis-backed fixed-window rate limiter.

Keyed per user when there is a session, otherwise per client IP. Redis is
already a hard dependency for sessions, so this adds no new infrastructure.
"""
import logging

import redis
from fastapi import HTTPException, Request

from app.session import get_session, redis_client

logger = logging.getLogger(__name__)

RATE_LIMIT_PREFIX = "ratelimit:"


def parse_limit(spec: str) -> tuple[int, int]:
    """Parse "<max calls>/<window seconds>" into (max_calls, window_seconds)."""
    calls, _, window = spec.partition("/")
    return int(calls), int(window)


def _client_key(request: Request) -> str:
    session = get_session(request.cookies.get("session"))
    if session:
        return f"user:{session['user_id']}"
    client = request.client
    return f"ip:{client.host if client else 'unknown'}"


def rate_limit(name: str, spec: str):
    """Build a FastAPI dependency enforcing `spec` on the named bucket."""
    max_calls, window = parse_limit(spec)

    def dependency(request: Request) -> None:
        key = f"{RATE_LIMIT_PREFIX}{name}:{_client_key(request)}"
        try:
            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, window)
        except redis.RedisError:
            # Never lock users out of the app because Redis hiccuped.
            logger.exception("Rate limit check failed for %s; allowing request", name)
            return
        if count > max_calls:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down and try again shortly.",
                headers={"Retry-After": str(window)},
            )

    return dependency
