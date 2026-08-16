"""User-related endpoints (onboarding, etc.)."""
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import DailyLog, User

router = APIRouter()

NICKNAME_RE = re.compile(r"^[a-z0-9_]{3,24}$")

FLOW_VALUES = {"spots", "light", "normal", "heavy"}

FLOW_TO_ATTR = {
    "spots": "spot_date",
    "light": "light_date",
    "normal": "normal_date",
    "heavy": "heavy_date",
}


_FLOW_ARRAY_ATTRS = ("spot_date", "light_date", "normal_date", "heavy_date")


def _remove_date_from_all_flow_arrays(user: User, d: date) -> None:
    for attr in _FLOW_ARRAY_ATTRS:
        arr = getattr(user, attr)
        if not arr:
            continue
        new_list = sorted([x for x in arr if x != d])
        setattr(user, attr, new_list if new_list else None)


def _set_flow_date_for_day(user: User, d: date, flow: str) -> None:
    _remove_date_from_all_flow_arrays(user, d)
    attr = FLOW_TO_ATTR[flow]
    arr = list(getattr(user, attr) or [])
    if d not in arr:
        arr.append(d)
        setattr(user, attr, sorted(arr))


def _append_cycle_date(user: User, attr: str, d: date) -> None:
    """Append a calendar date in chronological click order (no dedup)."""
    arr = list(getattr(user, attr) or [])
    arr.append(d)
    setattr(user, attr, arr)


def _cycle_dates_to_iso(user: User, attr: str) -> list[str]:
    arr = getattr(user, attr) or []
    return [x.isoformat() for x in arr]


class OnboardingBody(BaseModel):
    cycle_length: int = Field(..., ge=15, le=45, description="Typical cycle length in days")


class LastCycleBody(BaseModel):
    last_cycle_start: str = Field(..., description="First day of last period, YYYY-MM-DD")


@router.post("/onboarding")
def post_onboarding(
    body: OnboardingBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the user's cycle length (onboarding)."""
    current_user.cycle_length = body.cycle_length
    db.commit()
    db.refresh(current_user)
    return {"ok": True, "cycle_length": current_user.cycle_length}


@router.post("/onboarding/last-cycle")
def post_last_cycle(
    body: LastCycleBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the user's last cycle start date (onboarding step 2)."""
    try:
        parsed = date.fromisoformat(body.last_cycle_start)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date; use YYYY-MM-DD")
    _append_cycle_date(current_user, "cycle_start_dates", parsed)
    db.commit()
    db.refresh(current_user)
    return {
        "ok": True,
        "last_cycle_start": body.last_cycle_start,
        "cycle_start_dates": _cycle_dates_to_iso(current_user, "cycle_start_dates"),
    }


@router.get("/cycle-context")
def get_cycle_context(current_user: User = Depends(get_current_user)):
    """Cycle length and recorded start/end dates for phase mapping on the main calendar."""
    return {
        "cycle_length": current_user.cycle_length,
        "cycle_start_dates": _cycle_dates_to_iso(current_user, "cycle_start_dates"),
        "cycle_end_dates": _cycle_dates_to_iso(current_user, "cycle_end_dates"),
    }


class NicknameBody(BaseModel):
    nickname: str = Field(..., min_length=3, max_length=24)


def _normalize_nickname(raw: str) -> str:
    nick = (raw or "").strip().lower()
    if not NICKNAME_RE.match(nick):
        raise HTTPException(
            status_code=400,
            detail="Nickname must be 3–24 characters: a–z, 0–9, underscore.",
        )
    return nick


@router.patch("/me")
def patch_me(
    body: NicknameBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set or change unique nickname (stored lowercase)."""
    nick = _normalize_nickname(body.nickname)
    taken = (
        db.query(User)
        .filter(func.lower(User.nickname) == nick, User.id != current_user.id)
        .first()
    )
    if taken:
        raise HTTPException(status_code=409, detail="That nickname is taken.")
    current_user.nickname = nick
    db.commit()
    db.refresh(current_user)
    return {"ok": True, "nickname": current_user.nickname}


@router.get("/search")
def search_users(
    nickname: str = Query(..., min_length=1, max_length=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Find users by nickname prefix. Returns nickname only (no email)."""
    q = nickname.strip().lower()
    rows = (
        db.query(User)
        .filter(
            User.nickname.isnot(None),
            func.lower(User.nickname).like(f"{q}%"),
            User.id != current_user.id,
        )
        .order_by(User.nickname)
        .limit(10)
        .all()
    )
    return [{"nickname": r.nickname} for r in rows]


class DailyLogUpsertBody(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    is_period: bool | None = Field(None, description="Set period day on daily_logs")
    flow: str | None = Field(None, description="spots | light | normal | heavy")
    period_event: str | None = Field(
        None,
        description='If "start", append date to cycle_start_dates; if "end", append to cycle_end_dates',
    )


@router.get("/daily-logs")
def get_daily_logs(
    from_date: str = Query(..., alias="from", description="YYYY-MM-DD"),
    to: str = Query(..., description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return daily logs for the given date range (inclusive)."""
    try:
        from_parsed = date.fromisoformat(from_date)
        to_parsed = date.fromisoformat(to)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date; use YYYY-MM-DD")
    if from_parsed > to_parsed:
        raise HTTPException(status_code=400, detail="from must be <= to")
    rows = (
        db.query(DailyLog)
        .filter(
            DailyLog.user_id == current_user.id,
            DailyLog.date >= from_parsed,
            DailyLog.date <= to_parsed,
        )
        .all()
    )
    return [
        {"date": r.date.isoformat(), "is_period": r.is_period, "flow": r.flow}
        for r in rows
    ]


@router.post("/daily-logs")
def upsert_daily_log(
    body: DailyLogUpsertBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upsert daily_logs; optionally append to cycle_start_dates / cycle_end_dates and flow date arrays."""
    try:
        day = date.fromisoformat(body.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date; use YYYY-MM-DD")
    if body.period_event is not None and body.period_event not in ("start", "end"):
        raise HTTPException(status_code=400, detail='period_event must be "start" or "end"')
    if body.flow is not None and body.flow not in FLOW_VALUES:
        raise HTTPException(status_code=400, detail="flow must be spots, light, normal, or heavy")

    flow_in_body = "flow" in body.model_fields_set

    row = db.query(DailyLog).filter(
        DailyLog.user_id == current_user.id,
        DailyLog.date == day,
    ).first()
    if row is None:
        row = DailyLog(
            user_id=current_user.id,
            date=day,
            is_period=body.is_period if body.is_period is not None else False,
            flow=body.flow if flow_in_body else None,
        )
        db.add(row)
    else:
        if body.is_period is not None:
            row.is_period = body.is_period
        if flow_in_body:
            row.flow = body.flow

    # body.date is the selected calendar day; each click appends to the history array.
    if body.period_event == "start":
        _append_cycle_date(current_user, "cycle_start_dates", day)
        current_user.awaiting_period_end = True
    elif body.period_event == "end":
        _append_cycle_date(current_user, "cycle_end_dates", day)
        current_user.awaiting_period_end = False

    if flow_in_body:
        if body.flow is None:
            _remove_date_from_all_flow_arrays(current_user, day)
        else:
            _set_flow_date_for_day(current_user, day, body.flow)

    db.commit()
    db.refresh(row)
    db.refresh(current_user)
    return {
        "ok": True,
        "date": body.date,
        "is_period": row.is_period,
        "flow": row.flow,
        "cycle_start_dates": _cycle_dates_to_iso(current_user, "cycle_start_dates"),
        "cycle_end_dates": _cycle_dates_to_iso(current_user, "cycle_end_dates"),
        "awaiting_period_end": current_user.awaiting_period_end,
    }
