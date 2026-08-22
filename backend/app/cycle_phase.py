"""Server-side cycle phase.

Mirrors frontend/src/cycle/phaseEngine.js exactly; shared/phase-cases.json holds
the golden cases both test suites assert against, so the two cannot drift.
"""
import logging
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

# Phase lengths are expressed per 28-day cycle and scaled from there.
MENSTRUAL_DAYS_PER_28 = 5
OVULATION_DAYS_PER_28 = 3
LUTEAL_DAYS = 14

PHASE_LABELS = {
    "menstrual": "Menstrual",
    "follicular": "Follicular",
    "ovulation": "Ovulation",
    "luteal": "Luteal",
}


def _latest_start_on_or_before(start_dates: list[date], selected: date) -> date | None:
    best = None
    for d in start_dates or []:
        if d is None or d > selected:
            continue
        if best is None or d > best:
            best = d
    return best


def _next_start_after(start_dates: list[date], start: date) -> date | None:
    best = None
    for d in start_dates or []:
        if d is None or d <= start:
            continue
        if best is None or d < best:
            best = d
    return best


def _recorded_menstrual_end_day(
    start: date, end_dates: list[date], start_dates: list[date], length: int
) -> int | None:
    cycle_end_cap = start + timedelta(days=length)
    next_start = _next_start_after(start_dates, start)
    cap = next_start if next_start and next_start < cycle_end_cap else cycle_end_cap
    best_end = None
    for d in end_dates or []:
        if d is None or d < start or d >= cap:
            continue
        if best_end is None or d > best_end:
            best_end = d
    if best_end is None:
        return None
    return (best_end - start).days + 1


def _round_half_up(value: float) -> int:
    """Round .5 away from zero, the way JavaScript's Math.round does.

    Python's built-in round() is banker's rounding, so round(4.5) is 4 while
    Math.round(4.5) is 5 — which is exactly the kind of silent divergence the
    two implementations must not have. A 42-day cycle hits that case.
    """
    return math.floor(value + 0.5)


def _default_menstrual_days(length: int) -> int:
    return max(3, _round_half_up((length * MENSTRUAL_DAYS_PER_28) / 28))


def _ovulation_days(length: int) -> int:
    """Width of the ovulation window, scaled to the cycle like every other phase."""
    return max(3, _round_half_up((length * OVULATION_DAYS_PER_28) / 28))


def _ovulation_window(length: int) -> tuple[int, int, int]:
    """Return (ov_start, ov_end, ov_day) — the window and the day it centres on.

    The window leans earlier than ovulation itself, because the fertile window
    is mostly the days leading up to it.
    """
    width = _ovulation_days(length)
    before = math.ceil((width - 1) / 2)

    # The luteal phase runs ~14 days whatever the cycle length, so ovulation is
    # counted back from the end. Below roughly 21 days that rule puts ovulation
    # on or before the period itself; keep menstrual plus one follicular day
    # ahead of it instead, so every phase still exists.
    earliest_start = _default_menstrual_days(length) + 2
    ov_day = max(length - LUTEAL_DAYS, earliest_start + before)

    ov_start = ov_day - before
    ov_end = ov_start + width - 1
    if ov_end > length:
        ov_end = length
        ov_start = max(1, ov_end - width + 1)
        ov_day = min(ov_day, ov_end)
    return ov_start, ov_end, ov_day


def _assign_phase(cycle_day: int, m_end: int, ov_start: int, ov_end: int) -> str:
    if cycle_day <= m_end:
        return "menstrual"
    if cycle_day < ov_start:
        return "follicular"
    if cycle_day <= ov_end:
        return "ovulation"
    return "luteal"


def _empty() -> dict:
    return {"phase": None, "cycle_day": None, "phase_label": None}


def today_in(timezone_name: str | None) -> date:
    """Calendar day in the user's own timezone, falling back to UTC."""
    try:
        tz = ZoneInfo(timezone_name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        logger.warning("Unknown timezone %r; falling back to UTC", timezone_name)
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


def get_phase_for_date(
    selected: date,
    cycle_length: int | None,
    start_dates: list[date] | None,
    end_dates: list[date] | None,
) -> dict:
    """Return {phase, cycle_day, phase_label} for `selected`, or Nones."""
    length = int(cycle_length) if cycle_length else 0
    if length < 1:
        return _empty()
    starts = list(start_dates or [])
    ends = list(end_dates or [])
    start = _latest_start_on_or_before(starts, selected)
    if start is None:
        return _empty()
    raw_day = (selected - start).days + 1
    if raw_day < 1:
        return _empty()
    cycle_day = ((raw_day - 1) % length) + 1
    ov_start, ov_end, _ov_day = _ovulation_window(length)
    max_m = max(0, ov_start - 1)
    recorded = _recorded_menstrual_end_day(start, ends, starts, length)
    default_m = _default_menstrual_days(length)
    m_end = min(max(recorded if recorded is not None else default_m, 0), max_m)
    phase = _assign_phase(cycle_day, m_end, ov_start, ov_end)
    return {
        "phase": phase,
        "cycle_day": cycle_day,
        "phase_label": PHASE_LABELS[phase],
    }


def get_phase_for_today(
    cycle_length: int | None,
    start_dates: list[date] | None,
    end_dates: list[date] | None,
    timezone_name: str | None = None,
) -> dict:
    """Phase for the user's own "today", not the server's."""
    return get_phase_for_date(
        today_in(timezone_name), cycle_length, start_dates, end_dates
    )
