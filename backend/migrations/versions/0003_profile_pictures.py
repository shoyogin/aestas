"""Add profile pictures.

One row per user holding an already-normalized avatar (see app/avatars.py).
A separate table rather than a column on `users`: the bytes would otherwise
ride along on every query that loads a user, and almost none of them want them.

Revision ID: 0003_profile_pictures
Revises: 0002_tz_and_cleanup
Create Date: 2026-09-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0003_profile_pictures"
down_revision = "0002_tz_and_cleanup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profile_pictures",
        # The user is the primary key: one picture each, no second row possible,
        # and the cascade drops it with the account.
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("profile_pictures")
