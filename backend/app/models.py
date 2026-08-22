"""SQLAlchemy database models."""
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

FLOW_VALUES = ("spots", "light", "normal", "heavy")
LINK_TYPES = ("friend", "partner")
# withdrawn = requester cancelled a pending request; revoked = either side ended
# an accepted follow. Both are re-requestable, like Instagram.
FOLLOW_STATUSES = ("pending", "accepted", "refused", "revoked", "withdrawn")


class User(Base):
    """User account: OAuth identity, onboarding, and recorded cycle boundaries."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    google_id = Column(String(255), index=True, unique=True, nullable=False)
    email = Column(String(255), nullable=False, index=True)
    cycle_length = Column(Integer, nullable=True)  # None until onboarding completed
    # Every "Period started" / onboarding date, in order.
    cycle_start_dates = Column(ARRAY(Date), nullable=False, server_default="{}")
    # Every "Period ended" date, in order.
    cycle_end_dates = Column(ARRAY(Date), nullable=False, server_default="{}")
    # True after "Period started" until the matching "Period ended".
    awaiting_period_end = Column(Boolean, nullable=False, default=False)
    # Uniqueness is case-insensitive and enforced by uq_users_nickname_lower
    # below; a plain UNIQUE here would be redundant and weaker.
    nickname = Column(String(32), nullable=True, index=True)
    # IANA name, so the server agrees with the browser about which day "today" is.
    timezone = Column(String(64), nullable=False, server_default="UTC", default="UTC")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    daily_logs = relationship(
        "DailyLog", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "uq_users_nickname_lower",
            func.lower(nickname),
            unique=True,
            postgresql_where=text("nickname IS NOT NULL"),
        ),
    )

    @property
    def has_completed_onboarding(self) -> bool:
        return self.cycle_length is not None


class DailyLog(Base):
    """One row per user per calendar day: period state and flow level."""

    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date = Column(Date, nullable=False, index=True)
    is_period = Column(Boolean, nullable=False, default=False)
    flow = Column(String(20), nullable=True)  # one of FLOW_VALUES, or null
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="daily_logs")

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_logs_user_date"),
        CheckConstraint(
            "flow IS NULL OR flow IN ('spots', 'light', 'normal', 'heavy')",
            name="ck_daily_logs_flow",
        ),
    )


class FollowRequest(Base):
    """Consent-based follow: requester wants to see target's cycle phase."""

    __tablename__ = "follow_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requester_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    link_type = Column(String(20), nullable=False)  # one of LINK_TYPES
    status = Column(String(20), nullable=False, default="pending")  # one of FOLLOW_STATUSES
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    requester = relationship("User", foreign_keys=[requester_id])
    target = relationship("User", foreign_keys=[target_id])

    __table_args__ = (
        UniqueConstraint("requester_id", "target_id", name="uq_follow_requester_target"),
        CheckConstraint(
            "link_type IN ('friend', 'partner')", name="ck_follow_requests_link_type"
        ),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'refused', 'revoked', 'withdrawn')",
            name="ck_follow_requests_status",
        ),
        CheckConstraint("requester_id <> target_id", name="ck_follow_requests_not_self"),
        Index("ix_follow_requests_target_status", "target_id", "status"),
        Index("ix_follow_requests_requester_status", "requester_id", "status"),
    )
