"""Drop denormalized flow arrays, add per-user timezone, tighten constraints.

The four DATE[] flow columns on `users` duplicated `daily_logs.flow` and were
kept in sync by hand with no reader; `daily_logs` is now the only source. The
timezone column lets the server agree with the browser about which day it is.

Revision ID: 0002_tz_and_cleanup
Revises: 0001_initial
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_tz_and_cleanup"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

FLOW_ARRAY_COLUMNS = ("spot_date", "light_date", "normal_date", "heavy_date")


def upgrade() -> None:
    # Any flow recorded only in the arrays is backfilled into daily_logs before
    # the columns go, so no logged day is lost.
    for column in FLOW_ARRAY_COLUMNS:
        flow = column.replace("_date", "")
        flow = "spots" if flow == "spot" else flow
        op.execute(
            sa.text(
                f"""
                INSERT INTO daily_logs (user_id, date, is_period, flow)
                SELECT u.id, d.day, TRUE, :flow
                FROM users u, UNNEST(u.{column}) AS d(day)
                WHERE u.{column} IS NOT NULL
                ON CONFLICT ON CONSTRAINT uq_daily_logs_user_date
                DO UPDATE SET flow = EXCLUDED.flow
                WHERE daily_logs.flow IS NULL
                """
            ).bindparams(flow=flow)
        )
    for column in FLOW_ARRAY_COLUMNS:
        op.drop_column("users", column)

    op.add_column(
        "users",
        sa.Column(
            "timezone", sa.String(length=64), server_default="UTC", nullable=False
        ),
    )

    # Empty arrays instead of NULL, so callers never branch on two empty cases.
    op.execute("UPDATE users SET cycle_start_dates = '{}' WHERE cycle_start_dates IS NULL")
    op.execute("UPDATE users SET cycle_end_dates = '{}' WHERE cycle_end_dates IS NULL")
    op.alter_column("users", "cycle_start_dates", nullable=False)
    op.alter_column("users", "cycle_end_dates", nullable=False)

    # Cascade deletes, so removing a user cannot strand rows behind.
    op.drop_constraint("daily_logs_user_id_fkey", "daily_logs", type_="foreignkey")
    op.create_foreign_key(
        "daily_logs_user_id_fkey", "daily_logs", "users", ["user_id"], ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "follow_requests_requester_id_fkey", "follow_requests", type_="foreignkey"
    )
    op.create_foreign_key(
        "follow_requests_requester_id_fkey", "follow_requests", "users",
        ["requester_id"], ["id"], ondelete="CASCADE",
    )
    op.drop_constraint(
        "follow_requests_target_id_fkey", "follow_requests", type_="foreignkey"
    )
    op.create_foreign_key(
        "follow_requests_target_id_fkey", "follow_requests", "users",
        ["target_id"], ["id"], ondelete="CASCADE",
    )

    # Enum-ish columns get real constraints rather than comments.
    op.create_check_constraint(
        "ck_daily_logs_flow",
        "daily_logs",
        "flow IS NULL OR flow IN ('spots', 'light', 'normal', 'heavy')",
    )
    op.create_check_constraint(
        "ck_follow_requests_link_type", "follow_requests",
        "link_type IN ('friend', 'partner')",
    )
    op.create_check_constraint(
        "ck_follow_requests_status", "follow_requests",
        "status IN ('pending', 'accepted', 'refused', 'revoked', 'withdrawn')",
    )
    op.create_check_constraint(
        "ck_follow_requests_not_self", "follow_requests", "requester_id <> target_id",
    )

    # create_all had produced both a UNIQUE constraint and a plain index for
    # google_id; collapse them into one unique index. For nickname, the
    # case-insensitive uq_users_nickname_lower is the real rule, so the plain
    # UNIQUE constraint beside it only allowed "Luna" and "luna" to coexist.
    op.drop_constraint("users_google_id_key", "users", type_="unique")
    op.drop_index("ix_users_google_id", table_name="users")
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.drop_constraint("users_nickname_key", "users", type_="unique")

    # The two hot follow lookups are (target, status) and (requester, status).
    op.create_index(
        "ix_follow_requests_target_status", "follow_requests", ["target_id", "status"]
    )
    op.create_index(
        "ix_follow_requests_requester_status",
        "follow_requests",
        ["requester_id", "status"],
    )


def downgrade() -> None:
    op.create_unique_constraint("users_nickname_key", "users", ["nickname"])
    op.drop_index("ix_users_google_id", table_name="users")
    op.create_index("ix_users_google_id", "users", ["google_id"])
    op.create_unique_constraint("users_google_id_key", "users", ["google_id"])

    op.drop_index("ix_follow_requests_requester_status", table_name="follow_requests")
    op.drop_index("ix_follow_requests_target_status", table_name="follow_requests")
    op.drop_constraint("ck_follow_requests_not_self", "follow_requests", type_="check")
    op.drop_constraint("ck_follow_requests_status", "follow_requests", type_="check")
    op.drop_constraint("ck_follow_requests_link_type", "follow_requests", type_="check")
    op.drop_constraint("ck_daily_logs_flow", "daily_logs", type_="check")

    for table, name, column in (
        ("follow_requests", "follow_requests_target_id_fkey", "target_id"),
        ("follow_requests", "follow_requests_requester_id_fkey", "requester_id"),
        ("daily_logs", "daily_logs_user_id_fkey", "user_id"),
    ):
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, "users", [column], ["id"])

    op.alter_column("users", "cycle_end_dates", nullable=True)
    op.alter_column("users", "cycle_start_dates", nullable=True)
    op.drop_column("users", "timezone")
    for column in FLOW_ARRAY_COLUMNS:
        op.add_column(
            "users",
            sa.Column(
                column, sa.dialects.postgresql.ARRAY(sa.Date()), server_default="{}",
                nullable=True,
            ),
        )
