"""PostgreSQL connection and session management."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def add_user_cycle_aggregate_columns_if_missing():
    """Add flow date[] and awaiting_period_end columns to users if missing."""
    stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS spot_date DATE[] DEFAULT '{}'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS light_date DATE[] DEFAULT '{}'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS normal_date DATE[] DEFAULT '{}'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS heavy_date DATE[] DEFAULT '{}'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS awaiting_period_end BOOLEAN NOT NULL DEFAULT FALSE",
    ]
    with engine.connect() as conn:
        for s in stmts:
            conn.execute(text(s))
        conn.commit()


def migrate_user_cycle_history_arrays():
    """Add cycle_* DATE[] columns; copy legacy last_cycle_start/end into them once; drop legacy columns."""
    with engine.connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS cycle_start_dates DATE[] DEFAULT '{}'"
            )
        )
        conn.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS cycle_end_dates DATE[] DEFAULT '{}'")
        )
        conn.commit()

    def _has_column(conn, name: str) -> bool:
        r = conn.execute(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'users' AND column_name = :n"
            ),
            {"n": name},
        )
        return r.scalar() is not None

    with engine.connect() as conn:
        if _has_column(conn, "last_cycle_start"):
            conn.execute(
                text(
                    """
                    UPDATE users
                    SET cycle_start_dates = ARRAY[last_cycle_start]::date[]
                    WHERE last_cycle_start IS NOT NULL
                      AND (cycle_start_dates IS NULL OR cycle_start_dates = '{}')
                    """
                )
            )
            conn.execute(text("ALTER TABLE users DROP COLUMN last_cycle_start"))
        if _has_column(conn, "last_cycle_end"):
            conn.execute(
                text(
                    """
                    UPDATE users
                    SET cycle_end_dates = ARRAY[last_cycle_end]::date[]
                    WHERE last_cycle_end IS NOT NULL
                      AND (cycle_end_dates IS NULL OR cycle_end_dates = '{}')
                    """
                )
            )
            conn.execute(text("ALTER TABLE users DROP COLUMN last_cycle_end"))
        conn.commit()


def add_nickname_and_follows_if_missing():
    """Nickname on users; follow_requests created via metadata.create_all."""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR(32)"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_nickname_lower "
                "ON users (LOWER(nickname)) WHERE nickname IS NOT NULL"
            )
        )
        conn.commit()


def get_db():
    """Dependency: yield a DB session and close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
