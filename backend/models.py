"""SQLAlchemy database models."""
from sqlalchemy import Column, Date, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """User account: OAuth, onboarding, and aggregated cycle fields (arrays of dates per flow)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    google_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False, index=True)
    cycle_length = Column(Integer, nullable=True)  # None until onboarding completed
    cycle_start_dates = Column(ARRAY(Date), nullable=True)  # Every "Period started" / onboarding date, in order
    cycle_end_dates = Column(ARRAY(Date), nullable=True)  # Every "Period ended" date, in order
    spot_date = Column(ARRAY(Date), nullable=True)  # Dates where "spots" was selected
    light_date = Column(ARRAY(Date), nullable=True)
    normal_date = Column(ARRAY(Date), nullable=True)
    heavy_date = Column(ARRAY(Date), nullable=True)
    awaiting_period_end = Column(Boolean, nullable=False, default=False)  # True after "Period started" until "Period ended"
    nickname = Column(String(32), unique=True, nullable=True, index=True)  # lowercase unique handle
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def has_completed_onboarding(self) -> bool:
        return self.cycle_length is not None


class DailyLog(Base):
    """One row per user per calendar day: period state and flow level."""
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    is_period = Column(Boolean, nullable=False, default=False)
    flow = Column(String(20), nullable=True)  # 'spots' | 'light' | 'normal' | 'heavy' | null
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_daily_logs_user_date"),)


class FollowRequest(Base):
    """Consent-based follow: requester wants to see target's cycle phase."""

    __tablename__ = "follow_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    link_type = Column(String(20), nullable=False)  # friend | partner
    status = Column(String(20), nullable=False, default="pending")  # pending | accepted | refused | revoked
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("requester_id", "target_id", name="uq_follow_requester_target"),)
