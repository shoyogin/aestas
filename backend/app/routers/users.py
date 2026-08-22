"""User-related endpoints: onboarding, profile, search, and daily logs."""
import logging
import re
from datetime import date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.cycle_phase import today_in
from app.database import get_db
from app.dependencies import get_current_user
from app.models import FLOW_VALUES, DailyLog, User
from app.ratelimit import rate_limit
from app.schemas import (
    CycleContextResponse,
    DailyLogEntry,
    DailyLogUpsertBody,
    DailyLogUpsertResponse,
    LastCycleBody,
    LastCycleResponse,
    OnboardingBody,
    OnboardingResponse,
    UpdateMeBody,
    UpdateMeResponse,
    UserSearchHit,
)

logger = logging.getLogger(__name__)

router = APIRouter()

NICKNAME_RE = re.compile(r"^[a-z0-9_]{3,24}$")
EARLIEST_CYCLE_DATE = date(2000, 1, 1)
SEARCH_LIMIT = 10


def _escape_like(value: str) -> str:
    """Neutralise LIKE wildcards so a search for "%" cannot list every user."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _validate_cycle_date(user: User, value: date) -> date:
    """Cycle dates must be real, not in the user's future, and not prehistoric."""
    if value > today_in(user.timezone):
        raise HTTPException(status_code=400, detail="That date is in the future.")
    if value < EARLIEST_CYCLE_DATE:
        raise HTTPException(status_code=400, detail="That date is too far in the past.")
    return value


def _add_cycle_date(user: User, attr: str, value: date) -> None:
    """Insert a cycle boundary, keeping the array sorted and free of duplicates.

    Tapping "Period started" twice on the same day must not record two cycles.
    """
    existing = list(getattr(user, attr) or [])
    if value in existing:
        return
    setattr(user, attr, sorted([*existing, value]))


def _normalize_nickname(raw: str) -> str:
    nick = (raw or "").strip().lower()
    if not NICKNAME_RE.match(nick):
        raise HTTPException(
            status_code=400,
            detail="Nickname must be 3–24 characters: a–z, 0–9, underscore.",
        )
    return nick


def _normalize_timezone(raw: str) -> str:
    name = (raw or "").strip()
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as err:
        raise HTTPException(
            status_code=400, detail="Unknown timezone."
        ) from err
    return name


@router.post("/onboarding", response_model=OnboardingResponse)
def post_onboarding(
    body: OnboardingBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the user's cycle length (onboarding)."""
    current_user.cycle_length = body.cycle_length
    db.commit()
    return OnboardingResponse(cycle_length=body.cycle_length)


@router.post("/onboarding/last-cycle", response_model=LastCycleResponse)
def post_last_cycle(
    body: LastCycleBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the user's last cycle start date (onboarding step 2)."""
    start = _validate_cycle_date(current_user, body.last_cycle_start)
    _add_cycle_date(current_user, "cycle_start_dates", start)
    db.commit()
    db.refresh(current_user)
    return LastCycleResponse(
        last_cycle_start=start,
        cycle_start_dates=list(current_user.cycle_start_dates or []),
    )


@router.get("/cycle-context", response_model=CycleContextResponse)
def get_cycle_context(current_user: User = Depends(get_current_user)):
    """Cycle length and recorded start/end dates, for phase mapping in the UI."""
    return CycleContextResponse(
        cycle_length=current_user.cycle_length,
        cycle_start_dates=list(current_user.cycle_start_dates or []),
        cycle_end_dates=list(current_user.cycle_end_dates or []),
        timezone=current_user.timezone,
    )


@router.patch("/me", response_model=UpdateMeResponse)
def patch_me(
    body: UpdateMeBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set the unique nickname (stored lowercase) and/or the user's timezone."""
    if body.nickname is None and body.timezone is None:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    if body.timezone is not None:
        current_user.timezone = _normalize_timezone(body.timezone)

    if body.nickname is not None:
        current_user.nickname = _normalize_nickname(body.nickname)

    try:
        db.commit()
    except IntegrityError as err:
        # The partial unique index is the real arbiter: two people can pass the
        # availability check at once, and exactly one of them commits.
        db.rollback()
        logger.info("Nickname collision for user %s", current_user.id)
        raise HTTPException(status_code=409, detail="That nickname is taken.") from err
    db.refresh(current_user)
    return UpdateMeResponse(
        nickname=current_user.nickname, timezone=current_user.timezone
    )


@router.get(
    "/search",
    response_model=list[UserSearchHit],
    dependencies=[Depends(rate_limit("search", settings.rate_limit_search))],
)
def search_users(
    nickname: str = Query(..., min_length=1, max_length=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Find users by nickname prefix. Returns nicknames only — never emails."""
    q = nickname.strip().lower()
    if not q:
        return []
    pattern = f"{_escape_like(q)}%"
    rows = (
        db.query(User)
        .filter(
            User.nickname.isnot(None),
            func.lower(User.nickname).like(pattern, escape="\\"),
            User.id != current_user.id,
        )
        .order_by(User.nickname)
        .limit(SEARCH_LIMIT)
        .all()
    )
    return [UserSearchHit(nickname=r.nickname) for r in rows]


@router.get("/daily-logs", response_model=list[DailyLogEntry])
def get_daily_logs(
    from_date: date = Query(..., alias="from", description="YYYY-MM-DD"),
    to: date = Query(..., description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return daily logs for the given date range (inclusive)."""
    if from_date > to:
        raise HTTPException(status_code=400, detail="from must be <= to")
    rows = (
        db.query(DailyLog)
        .filter(
            DailyLog.user_id == current_user.id,
            DailyLog.date >= from_date,
            DailyLog.date <= to,
        )
        .order_by(DailyLog.date)
        .all()
    )
    return [
        DailyLogEntry(date=r.date, is_period=r.is_period, flow=r.flow) for r in rows
    ]


@router.post("/daily-logs", response_model=DailyLogUpsertResponse)
def upsert_daily_log(
    body: DailyLogUpsertBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upsert one day's log, and optionally record a period start/end boundary."""
    day = body.date
    if body.period_event is not None and body.period_event not in ("start", "end"):
        raise HTTPException(status_code=400, detail='period_event must be "start" or "end"')
    if body.flow is not None and body.flow not in FLOW_VALUES:
        raise HTTPException(
            status_code=400,
            detail=f"flow must be one of: {', '.join(FLOW_VALUES)}",
        )

    flow_in_body = "flow" in body.model_fields_set

    # One statement, so two concurrent taps cannot trip uq_daily_logs_user_date.
    values = {
        "user_id": current_user.id,
        "date": day,
        "is_period": bool(body.is_period),
        "flow": body.flow if flow_in_body else None,
    }
    updates = {}
    if body.is_period is not None:
        updates["is_period"] = body.is_period
    if flow_in_body:
        updates["flow"] = body.flow

    stmt = pg_insert(DailyLog).values(**values)
    if updates:
        stmt = stmt.on_conflict_do_update(
            constraint="uq_daily_logs_user_date",
            set_={**updates, "updated_at": func.now()},
        )
    else:
        stmt = stmt.on_conflict_do_nothing(constraint="uq_daily_logs_user_date")
    db.execute(stmt)

    if body.period_event == "start":
        _add_cycle_date(current_user, "cycle_start_dates", _validate_cycle_date(current_user, day))
        current_user.awaiting_period_end = True
    elif body.period_event == "end":
        _add_cycle_date(current_user, "cycle_end_dates", _validate_cycle_date(current_user, day))
        current_user.awaiting_period_end = False

    db.commit()
    db.refresh(current_user)

    row = db.execute(
        select(DailyLog).where(
            DailyLog.user_id == current_user.id, DailyLog.date == day
        )
    ).scalar_one()
    return DailyLogUpsertResponse(
        date=row.date,
        is_period=row.is_period,
        flow=row.flow,
        cycle_start_dates=list(current_user.cycle_start_dates or []),
        cycle_end_dates=list(current_user.cycle_end_dates or []),
        awaiting_period_end=current_user.awaiting_period_end,
    )
