"""Liveness and readiness probes."""
import logging

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.database import engine
from app.schemas import HealthResponse
from app.session import ping as redis_ping

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    """Liveness: the process is up. Deliberately touches no dependency."""
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=HealthResponse)
def ready(response: Response):
    """Readiness: the app can actually serve requests, i.e. Postgres and Redis
    both answer. A healthcheck that skips this passes while the app is broken."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        logger.exception("Database readiness check failed")
        database = "error"

    redis_status = "ok" if redis_ping() else "error"
    ok = database == "ok" and redis_status == "ok"
    if not ok:
        response.status_code = 503
    return HealthResponse(
        status="ok" if ok else "degraded", database=database, redis=redis_status
    )
