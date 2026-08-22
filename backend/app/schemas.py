"""Request and response models. Every endpoint declares one, so the OpenAPI
schema is accurate and no field can leak into a response by accident."""
import datetime

from pydantic import BaseModel, Field

from app.models import FLOW_VALUES, LINK_TYPES

# Imported as a module, not a name: several models have a field called `date`,
# which would otherwise shadow the annotation it needs.
Date = datetime.date


# ----- Users -----


class MeResponse(BaseModel):
    id: int
    email: str
    nickname: str | None
    timezone: str
    has_completed_onboarding: bool
    awaiting_period_end: bool


class OkResponse(BaseModel):
    ok: bool = True


class OnboardingBody(BaseModel):
    cycle_length: int = Field(..., ge=15, le=45, description="Typical cycle length in days")


class OnboardingResponse(BaseModel):
    ok: bool = True
    cycle_length: int


class LastCycleBody(BaseModel):
    last_cycle_start: Date = Field(..., description="First day of last period, YYYY-MM-DD")


class CycleContextResponse(BaseModel):
    cycle_length: int | None
    cycle_start_dates: list[Date]
    cycle_end_dates: list[Date]
    timezone: str


class LastCycleResponse(BaseModel):
    ok: bool = True
    last_cycle_start: Date
    cycle_start_dates: list[Date]


class UpdateMeBody(BaseModel):
    nickname: str | None = Field(None, min_length=3, max_length=24)
    timezone: str | None = Field(None, max_length=64, description="IANA timezone name")


class UpdateMeResponse(BaseModel):
    ok: bool = True
    nickname: str | None
    timezone: str


class UserSearchHit(BaseModel):
    nickname: str


# ----- Daily logs -----


class DailyLogEntry(BaseModel):
    date: Date
    is_period: bool
    flow: str | None


class DailyLogUpsertBody(BaseModel):
    date: Date = Field(..., description="YYYY-MM-DD")
    is_period: bool | None = Field(None, description="Set period day on daily_logs")
    flow: str | None = Field(None, description=f"One of: {', '.join(FLOW_VALUES)}")
    period_event: str | None = Field(
        None,
        description='"start" appends to cycle_start_dates; "end" appends to cycle_end_dates',
    )


class DailyLogUpsertResponse(BaseModel):
    ok: bool = True
    date: Date
    is_period: bool
    flow: str | None
    cycle_start_dates: list[Date]
    cycle_end_dates: list[Date]
    awaiting_period_end: bool


# ----- Follows -----


class FollowCreateBody(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=24)
    link_type: str = Field(..., description=f"One of: {', '.join(LINK_TYPES)}")


class FollowSummary(BaseModel):
    """A follow edge as seen by one side. Never carries the other user's email."""

    id: int
    link_type: str
    status: str
    nickname: str | None
    created_at: str | None
    direction: str


class FollowWithPhase(FollowSummary):
    phase: str | None = None
    cycle_day: int | None = None
    phase_label: str | None = None


class SharedCycleResponse(BaseModel):
    nickname: str | None
    link_type: str
    phase: str | None
    cycle_day: int | None
    phase_label: str | None
    panels: dict | None
    disclaimer: str


# ----- Content -----


class PhaseContentResponse(BaseModel):
    labels: dict[str, str]
    panel_order: list[str]
    panel_headings: dict[str, str]
    panels: dict
    disclaimer: str


# ----- Health -----


class HealthResponse(BaseModel):
    status: str
    database: str | None = None
    redis: str | None = None
