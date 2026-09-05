"""Initial schema.

Captures the schema as it existed before Alembic was introduced, so an existing
development database can be adopted with:

    alembic stamp 0001_initial && alembic upgrade head

A fresh database just runs `alembic upgrade head`.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("google_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("cycle_length", sa.Integer(), nullable=True),
        sa.Column(
            "cycle_start_dates", postgresql.ARRAY(sa.Date()), server_default="{}", nullable=True
        ),
        sa.Column(
            "cycle_end_dates", postgresql.ARRAY(sa.Date()), server_default="{}", nullable=True
        ),
        sa.Column("spot_date", postgresql.ARRAY(sa.Date()), server_default="{}", nullable=True),
        sa.Column("light_date", postgresql.ARRAY(sa.Date()), server_default="{}", nullable=True),
        sa.Column("normal_date", postgresql.ARRAY(sa.Date()), server_default="{}", nullable=True),
        sa.Column("heavy_date", postgresql.ARRAY(sa.Date()), server_default="{}", nullable=True),
        sa.Column(
            "awaiting_period_end", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("nickname", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("google_id"),
        sa.UniqueConstraint("nickname"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_google_id", "users", ["google_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_nickname", "users", ["nickname"])
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_nickname_lower "
        "ON users (LOWER(nickname)) WHERE nickname IS NOT NULL"
    )

    op.create_table(
        "daily_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("is_period", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("flow", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date", name="uq_daily_logs_user_date"),
    )
    op.create_index("ix_daily_logs_id", "daily_logs", ["id"])
    op.create_index("ix_daily_logs_user_id", "daily_logs", ["user_id"])
    op.create_index("ix_daily_logs_date", "daily_logs", ["date"])

    op.create_table(
        "follow_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("link_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requester_id", "target_id", name="uq_follow_requester_target"),
    )
    op.create_index("ix_follow_requests_id", "follow_requests", ["id"])
    op.create_index("ix_follow_requests_requester_id", "follow_requests", ["requester_id"])
    op.create_index("ix_follow_requests_target_id", "follow_requests", ["target_id"])


def downgrade() -> None:
    op.drop_table("follow_requests")
    op.drop_table("daily_logs")
    op.execute("DROP INDEX IF EXISTS uq_users_nickname_lower")
    op.drop_table("users")
