"""Test fixtures: a real Postgres schema built from the Alembic migrations, a
fake Redis so sessions and rate limits need no server, and an authenticated
TestClient."""
import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault(
    "DATABASE_URL", "postgresql://aestas:aestas@localhost:5432/aestas_test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

SHARED_DIR = pathlib.Path(__file__).resolve().parents[2] / "shared"


class FakeRedis:
    """Just enough Redis for sessions and the fixed-window rate limiter."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def setex(self, key, _ttl, value):
        self.store[key] = value

    def get(self, key):
        return self.store.get(key)

    def delete(self, key):
        self.store.pop(key, None)

    def incr(self, key):
        value = int(self.store.get(key, 0)) + 1
        self.store[key] = str(value)
        return value

    def expire(self, key, _ttl):
        return True

    def ping(self):
        return True


@pytest.fixture(scope="session", autouse=True)
def _fake_redis():
    """Swap Redis out before anything imports a live client."""
    from app import session as session_module

    fake = FakeRedis()
    session_module.redis_client = fake
    import app.ratelimit as ratelimit_module

    ratelimit_module.redis_client = fake
    yield fake


@pytest.fixture(scope="session")
def engine():
    from alembic import command
    from alembic.config import Config

    from app.database import engine as app_engine

    root = pathlib.Path(__file__).resolve().parents[1]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield app_engine


@pytest.fixture
def db(engine, _fake_redis):
    """A clean database and a clean Redis per test, so rate-limit counters and
    sessions never leak between tests."""
    from sqlalchemy import text

    from app.database import SessionLocal

    _fake_redis.store.clear()
    with engine.connect() as conn:
        conn.execute(
            text("TRUNCATE follow_requests, daily_logs, users RESTART IDENTITY CASCADE")
        )
        conn.commit()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_user(db):
    from app.models import User

    def _make(nickname=None, cycle_length=28, starts=None, ends=None, tz="UTC"):
        import datetime as dt

        user = User(
            google_id=f"google-{nickname or 'anon'}-{id(nickname)}",
            email=f"{nickname or 'anon'}@example.com",
            nickname=nickname,
            cycle_length=cycle_length,
            timezone=tz,
            cycle_start_dates=[dt.date.fromisoformat(s) for s in (starts or [])],
            cycle_end_dates=[dt.date.fromisoformat(s) for s in (ends or [])],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture
def client(db, _fake_redis):
    """TestClient sharing the test's DB session."""
    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def login(client, _fake_redis):
    """Authenticate the TestClient as a given user."""
    from app.session import create_session

    def _login(user):
        client.cookies.set("session", create_session(user.id))
        return user

    return _login


@pytest.fixture(scope="session")
def phase_cases():
    data = json.loads((SHARED_DIR / "phase-cases.json").read_text(encoding="utf-8"))
    return data["cases"]
