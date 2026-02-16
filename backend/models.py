"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """User account: Google OAuth identity + optional cycle_length from onboarding."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    google_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False, index=True)
    cycle_length = Column(Integer, nullable=True)  # None until onboarding completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def has_completed_onboarding(self) -> bool:
        return self.cycle_length is not None
